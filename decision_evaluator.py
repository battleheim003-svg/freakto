"""
decision_evaluator.py

ارزیابی تصمیم‌های ثبت‌شده در logs/decisions.csv

نسخه Partial Evaluation + decision_id:
اگر هنوز داده کافی برای 24h وجود نداشته باشد، ارزیابی‌های موجود مثل 4h یا 12h
را انجام می‌دهد و بقیه را خالی می‌گذارد.
"""

import ast
import csv
import json
from pathlib import Path

import pandas as pd

from engine.csv_utils import read_csv_dicts_lenient

from config import SYMBOL, TIMEFRAME
from data_fetcher import fetch_ohlcv


LOG_DIR = Path("logs")
DECISIONS_FILE = LOG_DIR / "decisions.csv"
EVALUATIONS_FILE = LOG_DIR / "decision_evaluations.csv"
ROOT_CAUSE_DIR = LOG_DIR / "root_cause"


HORIZON_CANDLES = {
    "4h": 1,
    "12h": 3,
    "24h": 6,
}


def _is_blank(value):
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "none", "null"}


def _safe_json_load(path):
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception:
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def _load_latest_root_cause_snapshot():
    """Load the latest saved Root Cause report and expose evaluator-ready fields.

    v8.1.1 bridge patch:
    root_cause_dashboard.py writes the Root Cause report under logs/root_cause,
    while historical rows in decisions.csv may not yet carry root_cause_* fields.
    The evaluator uses this latest report only when it can match the report's
    latest_decision_id to a decision row. This avoids blindly applying today's
    root cause to all historical decisions.
    """
    if not ROOT_CAUSE_DIR.exists():
        return {}

    candidates = []
    for pattern in ("root_cause_root_cause_*.json", "root_cause_*.json"):
        candidates.extend(ROOT_CAUSE_DIR.glob(pattern))
    candidates = [p for p in candidates if "forward_validation" not in p.name and p.is_file()]
    if not candidates:
        return {}

    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    data = _safe_json_load(latest)
    if not data:
        return {}

    top_causes = data.get("top_causes") or []
    top_summary = ""
    if isinstance(top_causes, list):
        compact = []
        for item in top_causes[:5]:
            if isinstance(item, dict):
                cause = item.get("cause") or item.get("root_cause") or item.get("label") or ""
                prob = item.get("probability_pct") or item.get("probability") or ""
                if cause:
                    compact.append(f"{cause}:{prob}%")
        top_summary = ";".join(compact)

    return {
        "source_file": str(latest),
        "latest_decision_id": str(data.get("latest_decision_id") or data.get("decision_id") or "").strip(),
        "symbol": str(data.get("symbol") or "").strip(),
        "timeframe": str(data.get("timeframe") or "").strip(),
        "root_cause_primary": data.get("primary_root_cause") or data.get("root_cause_primary") or "",
        "root_cause_direction": data.get("root_cause_direction") or "",
        "root_cause_confidence": data.get("root_cause_confidence") or "",
        "root_cause_probability_pct": data.get("root_cause_probability_pct") or "",
        "root_cause_evidence_quality": data.get("root_cause_evidence_quality") or "",
        "root_cause_verdict": data.get("root_cause_verdict") or "",
        "root_cause_evidence_total": data.get("evidence_total") or data.get("root_cause_evidence_total") or "",
        "root_cause_official_evidence_total": data.get("official_evidence_total") or data.get("root_cause_official_evidence_total") or "",
        "root_cause_top_causes": top_summary,
        "root_cause_summary": data.get("root_cause_summary") or "",
    }


def _apply_root_cause_bridge(decision, snapshot):
    """Return root_cause fields for a decision row.

    Existing decision values always win. Snapshot fallback is applied only when
    the row lacks root_cause_primary and the snapshot matches the row's
    decision_id. This is intentionally conservative to avoid leakage/mislabeling.
    """
    fields = {
        "root_cause_primary": decision.get("root_cause_primary", ""),
        "root_cause_direction": decision.get("root_cause_direction", ""),
        "root_cause_confidence": decision.get("root_cause_confidence", ""),
        "root_cause_probability_pct": decision.get("root_cause_probability_pct", ""),
        "root_cause_evidence_quality": decision.get("root_cause_evidence_quality", ""),
        "root_cause_verdict": decision.get("root_cause_verdict", ""),
        "root_cause_evidence_total": decision.get("root_cause_evidence_total", ""),
        "root_cause_official_evidence_total": decision.get("root_cause_official_evidence_total", ""),
        "root_cause_top_causes": decision.get("root_cause_top_causes", ""),
        "root_cause_summary": decision.get("root_cause_summary", ""),
    }
    if not snapshot or not _is_blank(fields.get("root_cause_primary")):
        return fields

    row_decision_id = str(decision.get("decision_id", "") or "").strip()
    snap_decision_id = str(snapshot.get("latest_decision_id", "") or "").strip()
    if not row_decision_id or row_decision_id != snap_decision_id:
        return fields

    row_symbol = str(decision.get("symbol", SYMBOL) or SYMBOL).strip()
    row_tf = str(decision.get("timeframe", TIMEFRAME) or TIMEFRAME).strip()
    snap_symbol = str(snapshot.get("symbol", "") or "").strip()
    snap_tf = str(snapshot.get("timeframe", "") or "").strip()
    if snap_symbol and row_symbol and snap_symbol != row_symbol:
        return fields
    if snap_tf and row_tf and snap_tf != row_tf:
        return fields

    for key in fields:
        fields[key] = snapshot.get(key, fields[key])
    fields["root_cause_bridge_source"] = "LATEST_ROOT_CAUSE_JSON_MATCHED_DECISION_ID"
    return fields


def _parse_targets(value):
    if not value:
        return []

    try:
        parsed = ast.literal_eval(value)
        return [float(str(item).replace(",", "")) for item in parsed]
    except Exception:
        return []


def _parse_price(value):
    if value is None:
        return None

    text = str(value).replace(",", "").strip()

    if not text or text == "نامشخص":
        return None

    try:
        return float(text)
    except ValueError:
        return None


def _load_decisions():
    if not DECISIONS_FILE.exists():
        print(f"❌ فایل تصمیم‌ها پیدا نشد: {DECISIONS_FILE}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(DECISIONS_FILE, encoding="utf-8-sig")
    except Exception as error:
        print(
            "⚠️ خواندن مستقیم decisions.csv با pandas شکست خورد؛ "
            "حالت سازگار با schema قدیمی/جدید فعال شد."
        )
        print(f"جزئیات: {type(error).__name__}: {error}")
        _, rows = read_csv_dicts_lenient(DECISIONS_FILE)
        df = pd.DataFrame(rows)

    if df.empty:
        print("❌ فایل تصمیم‌ها خالی است.")
        return pd.DataFrame()

    # Drop DictReader overflow payload if a mixed-schema row had more fields
    # than the old header. Evaluation only needs stable early columns.
    if "_extra" in df.columns:
        df = df.drop(columns=["_extra"])

    if "decision_id" not in df.columns:
        print("⚠️ ستون decision_id در لاگ قدیمی وجود ندارد. از این به بعد اضافه می‌شود.")
        df["decision_id"] = ""

    required_defaults = {
        "symbol": SYMBOL,
        "timeframe": TIMEFRAME,
        "side": "NEUTRAL",
        "score": 0,
        "confidence_label": "",
        "risk_label": "",
        "actionability": "",
        "targets": "",
        "stop_zone": "",
        "regime_label": "UNKNOWN",
        "regime_confidence": "",
        "regime_adjustment": "",
        "regime_source": "",
        "regime_label_quality": "",
        "trend_state": "",
        "volatility_state": "",
        "market_phase": "",
        "primary_cause": "",
        "cause_confidence": "",
        "catalyst_score": "",
        "event_risk": "",
        "technical_event_conflict": "",
        "causal_alignment": "",
        "causal_verdict": "",
        "causal_source_count": "",
        "causal_trusted_source_count": "",
        "causal_manual_event_count": "",
        "causal_auto_event_count": "",
        "causal_top_sources": "",
        "causal_notes": "",
        "market_narrative_label": "",
        "market_narrative_confidence": "",
        "market_narrative_direction": "",
        "market_narrative_theme": "",
        "market_narrative_score": "",
        "market_narrative_event_risk": "",
        "market_narrative_conflict": "",
        "market_narrative_summary": "",
        "narrative_alignment": "",
        "narrative_conflict_score": "",
        "narrative_adjustment": "",
        "narrative_adjusted_score": "",
        "narrative_action_override": "",
        "narrative_decision_verdict": "",
        "narrative_decision_notes": "",
        "root_cause_primary": "",
        "root_cause_direction": "",
        "root_cause_confidence": "",
        "root_cause_probability_pct": "",
        "root_cause_evidence_quality": "",
        "root_cause_verdict": "",
        "root_cause_evidence_total": "",
        "root_cause_official_evidence_total": "",
        "root_cause_top_causes": "",
        "root_cause_summary": "",
        "root_cause_bridge_source": "",
    }
    for column, default in required_defaults.items():
        if column not in df.columns:
            df[column] = default

    if "price" not in df.columns:
        if "entry_price" in df.columns:
            df["price"] = df["entry_price"]
        else:
            df["price"] = None

    df["candle_timestamp"] = pd.to_datetime(df.get("candle_timestamp"), errors="coerce")
    df = df.dropna(subset=["candle_timestamp"])

    if df.empty:
        print("❌ هیچ تصمیمی با candle_timestamp معتبر برای ارزیابی وجود ندارد.")

    return df


def _load_market_data():
    raw = fetch_ohlcv(symbol=SYMBOL, timeframe=TIMEFRAME, limit=500)

    if raw is None or raw.empty:
        print("❌ داده بازار دریافت نشد.")
        return pd.DataFrame()

    df = raw.copy()

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df = df.set_index("timestamp")

    df = df.sort_index()

    return df


def _find_candle_index(market_df, timestamp):
    matches = market_df.index[market_df.index == timestamp]

    if len(matches) == 0:
        return None

    return market_df.index.get_loc(matches[0])


def _evaluate_price_move(side, entry_price, future_price):
    if not entry_price or not future_price:
        return None

    change_pct = ((future_price - entry_price) / entry_price) * 100

    if side == "SHORT":
        change_pct *= -1

    if side == "NEUTRAL":
        return round(((future_price - entry_price) / entry_price) * 100, 4)

    return round(change_pct, 4)


def _evaluate_market_move(entry_price, future_price):
    """Raw market return, independent from decision side.

    v8.1 uses this for Root Cause Forward Validation because root-cause
    directions such as BULLISH/BEARISH must be validated against actual market
    movement, not the side-adjusted trade return used by decision evaluation.
    """
    if not entry_price or not future_price:
        return None
    return round(((future_price - entry_price) / entry_price) * 100, 4)


def _root_cause_direction_correct(direction, market_return):
    direction = str(direction or "").upper().replace("-", "_").replace(" ", "_")
    if market_return is None:
        return None
    if direction == "BULLISH":
        return bool(market_return > 0)
    if direction == "BEARISH":
        return bool(market_return < 0)
    return None


def _root_cause_signed_return(direction, market_return):
    direction = str(direction or "").upper().replace("-", "_").replace(" ", "_")
    if market_return is None:
        return None
    if direction == "BULLISH":
        return round(float(market_return), 4)
    if direction == "BEARISH":
        return round(float(market_return) * -1, 4)
    return None


def _evaluate_targets_and_stop_partial(side, entry_idx, market_df, targets, stop_price):
    available_future = market_df.iloc[entry_idx + 1:]

    if available_future.empty:
        return {
            "target_1_hit": None,
            "target_2_hit": None,
            "target_3_hit": None,
            "stop_hit": None,
            "mfe_pct": None,
            "mae_pct": None,
            "evaluated_candles": 0,
        }

    entry_price = float(market_df.iloc[entry_idx]["close"])

    target_hits = [False, False, False]
    stop_hit = False

    highs = available_future["high"].astype(float)
    lows = available_future["low"].astype(float)

    if side == "LONG":
        for index, target in enumerate(targets[:3]):
            target_hits[index] = bool((highs >= target).any())

        if stop_price:
            stop_hit = bool((lows <= stop_price).any())

        mfe_pct = ((highs.max() - entry_price) / entry_price) * 100
        mae_pct = ((lows.min() - entry_price) / entry_price) * 100

    elif side == "SHORT":
        for index, target in enumerate(targets[:3]):
            target_hits[index] = bool((lows <= target).any())

        if stop_price:
            stop_hit = bool((highs >= stop_price).any())

        mfe_pct = ((entry_price - lows.min()) / entry_price) * 100
        mae_pct = ((entry_price - highs.max()) / entry_price) * 100

    else:
        mfe_pct = ((highs.max() - entry_price) / entry_price) * 100
        mae_pct = ((lows.min() - entry_price) / entry_price) * 100

    return {
        "target_1_hit": target_hits[0],
        "target_2_hit": target_hits[1],
        "target_3_hit": target_hits[2],
        "stop_hit": stop_hit,
        "mfe_pct": round(mfe_pct, 4) if mfe_pct is not None else None,
        "mae_pct": round(mae_pct, 4) if mae_pct is not None else None,
        "evaluated_candles": len(available_future),
    }


def evaluate_decisions():
    decisions = _load_decisions()
    if decisions.empty:
        return

    market_df = _load_market_data()
    if market_df.empty:
        return

    latest_root_cause_snapshot = _load_latest_root_cause_snapshot()
    bridge_applied = 0

    rows = []

    for _, decision in decisions.iterrows():
        timestamp = decision["candle_timestamp"]
        entry_idx = _find_candle_index(market_df, timestamp)

        if entry_idx is None:
            print(f"⚠️ کندل تصمیم پیدا نشد: {timestamp}")
            continue

        available_candles = len(market_df) - entry_idx - 1

        if available_candles <= 0:
            print(f"⏳ هنوز حتی یک کندل بعد از این تصمیم موجود نیست: {timestamp}")
            continue

        side = str(decision.get("side", "NEUTRAL"))
        root_cause_fields = _apply_root_cause_bridge(decision, latest_root_cause_snapshot)
        if root_cause_fields.get("root_cause_bridge_source"):
            bridge_applied += 1
        entry_price = _parse_price(decision.get("price"))
        if entry_price is None:
            print(f"⚠️ قیمت ورود نامعتبر است و رد شد: {timestamp}")
            continue

        result = {
            "decision_id": decision.get("decision_id", ""),
            "candle_timestamp": str(timestamp),
            "symbol": decision.get("symbol", SYMBOL),
            "timeframe": decision.get("timeframe", TIMEFRAME),
            "side": side,
            "score": int(decision.get("score", 0)),
            "confidence_label": decision.get("confidence_label", ""),
            "risk_label": decision.get("risk_label", ""),
            "actionability": decision.get("actionability", ""),
            "regime_label": decision.get("regime_label", "UNKNOWN"),
            "regime_confidence": decision.get("regime_confidence", ""),
            "regime_adjustment": decision.get("regime_adjustment", ""),
            "regime_source": decision.get("regime_source", ""),
            "regime_label_quality": decision.get("regime_label_quality", ""),
            "trend_state": decision.get("trend_state", ""),
            "volatility_state": decision.get("volatility_state", ""),
            "market_phase": decision.get("market_phase", ""),
            "primary_cause": decision.get("primary_cause", ""),
            "cause_confidence": decision.get("cause_confidence", ""),
            "catalyst_score": decision.get("catalyst_score", ""),
            "event_risk": decision.get("event_risk", ""),
            "technical_event_conflict": decision.get("technical_event_conflict", ""),
            "causal_alignment": decision.get("causal_alignment", ""),
            "causal_verdict": decision.get("causal_verdict", ""),
            "causal_source_count": decision.get("causal_source_count", ""),
            "causal_trusted_source_count": decision.get("causal_trusted_source_count", ""),
            "causal_manual_event_count": decision.get("causal_manual_event_count", ""),
            "causal_auto_event_count": decision.get("causal_auto_event_count", ""),
            "causal_top_sources": decision.get("causal_top_sources", ""),
            "causal_notes": decision.get("causal_notes", ""),
            "market_narrative_label": decision.get("market_narrative_label", ""),
            "market_narrative_confidence": decision.get("market_narrative_confidence", ""),
            "market_narrative_direction": decision.get("market_narrative_direction", ""),
            "market_narrative_theme": decision.get("market_narrative_theme", ""),
            "market_narrative_score": decision.get("market_narrative_score", ""),
            "market_narrative_event_risk": decision.get("market_narrative_event_risk", ""),
            "market_narrative_conflict": decision.get("market_narrative_conflict", ""),
            "market_narrative_summary": decision.get("market_narrative_summary", ""),
            "narrative_alignment": decision.get("narrative_alignment", ""),
            "narrative_conflict_score": decision.get("narrative_conflict_score", ""),
            "narrative_adjustment": decision.get("narrative_adjustment", ""),
            "narrative_adjusted_score": decision.get("narrative_adjusted_score", ""),
            "narrative_action_override": decision.get("narrative_action_override", ""),
            "narrative_decision_verdict": decision.get("narrative_decision_verdict", ""),
            "narrative_decision_notes": decision.get("narrative_decision_notes", ""),
            "root_cause_primary": root_cause_fields.get("root_cause_primary", ""),
            "root_cause_direction": root_cause_fields.get("root_cause_direction", ""),
            "root_cause_confidence": root_cause_fields.get("root_cause_confidence", ""),
            "root_cause_probability_pct": root_cause_fields.get("root_cause_probability_pct", ""),
            "root_cause_evidence_quality": root_cause_fields.get("root_cause_evidence_quality", ""),
            "root_cause_verdict": root_cause_fields.get("root_cause_verdict", ""),
            "root_cause_evidence_total": root_cause_fields.get("root_cause_evidence_total", ""),
            "root_cause_official_evidence_total": root_cause_fields.get("root_cause_official_evidence_total", ""),
            "root_cause_top_causes": root_cause_fields.get("root_cause_top_causes", ""),
            "root_cause_summary": root_cause_fields.get("root_cause_summary", ""),
            "root_cause_bridge_source": root_cause_fields.get("root_cause_bridge_source", ""),
            "entry_price": entry_price,
            "available_future_candles": available_candles,
            "evaluation_status": "PARTIAL",
        }

        completed_horizons = 0

        root_cause_direction = root_cause_fields.get("root_cause_direction", "")

        for label, candle_offset in HORIZON_CANDLES.items():
            column_name = f"return_after_{label}_pct"
            market_column_name = f"market_return_after_{label}_pct"
            signed_column_name = f"root_cause_signed_return_after_{label}_pct"
            correct_column_name = f"root_cause_direction_correct_after_{label}"

            if available_candles >= candle_offset:
                future_close = float(market_df.iloc[entry_idx + candle_offset]["close"])
                side_adjusted_return = _evaluate_price_move(
                    side=side,
                    entry_price=entry_price,
                    future_price=future_close,
                )
                market_return = _evaluate_market_move(
                    entry_price=entry_price,
                    future_price=future_close,
                )
                result[column_name] = side_adjusted_return
                result[market_column_name] = market_return
                result[signed_column_name] = _root_cause_signed_return(root_cause_direction, market_return)
                result[correct_column_name] = _root_cause_direction_correct(root_cause_direction, market_return)
                completed_horizons += 1
            else:
                result[column_name] = None
                result[market_column_name] = None
                result[signed_column_name] = None
                result[correct_column_name] = None

        if completed_horizons == len(HORIZON_CANDLES):
            result["evaluation_status"] = "COMPLETE"

        targets = _parse_targets(decision.get("targets", ""))
        stop_price = _parse_price(decision.get("stop_zone", ""))

        result.update(
            _evaluate_targets_and_stop_partial(
                side=side,
                entry_idx=entry_idx,
                market_df=market_df,
                targets=targets,
                stop_price=stop_price,
            )
        )

        rows.append(result)

    if not rows:
        print("ℹ️ هنوز تصمیم قابل ارزیابی وجود ندارد.")
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    output_df = pd.DataFrame(rows)
    output_df.to_csv(EVALUATIONS_FILE, index=False, encoding="utf-8-sig")

    print(f"✅ ارزیابی‌ها ذخیره شد: {EVALUATIONS_FILE}")
    if bridge_applied:
        print(f"🧬 Root Cause bridge applied rows: {bridge_applied}")
    elif latest_root_cause_snapshot:
        print("ℹ️ Root Cause snapshot found, but no matching blank decision_id row needed bridge.")
    print(output_df.tail(10).to_string(index=False))


if __name__ == "__main__":
    evaluate_decisions()