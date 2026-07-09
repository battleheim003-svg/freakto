"""
decision_evaluator.py

ارزیابی تصمیم‌های ثبت‌شده در logs/decisions.csv

نسخه Partial Evaluation + decision_id:
اگر هنوز داده کافی برای 24h وجود نداشته باشد، ارزیابی‌های موجود مثل 4h یا 12h
را انجام می‌دهد و بقیه را خالی می‌گذارد.
"""

import ast
import csv
from pathlib import Path

import pandas as pd

from engine.csv_utils import read_csv_dicts_lenient

from config import SYMBOL, TIMEFRAME
from data_fetcher import fetch_ohlcv


LOG_DIR = Path("logs")
DECISIONS_FILE = LOG_DIR / "decisions.csv"
EVALUATIONS_FILE = LOG_DIR / "decision_evaluations.csv"


HORIZON_CANDLES = {
    "4h": 1,
    "12h": 3,
    "24h": 6,
}


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
            "entry_price": entry_price,
            "available_future_candles": available_candles,
            "evaluation_status": "PARTIAL",
        }

        completed_horizons = 0

        for label, candle_offset in HORIZON_CANDLES.items():
            column_name = f"return_after_{label}_pct"

            if available_candles >= candle_offset:
                future_close = float(market_df.iloc[entry_idx + candle_offset]["close"])
                result[column_name] = _evaluate_price_move(
                    side=side,
                    entry_price=entry_price,
                    future_price=future_close,
                )
                completed_horizons += 1
            else:
                result[column_name] = None

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
    print(output_df.tail(10).to_string(index=False))


if __name__ == "__main__":
    evaluate_decisions()