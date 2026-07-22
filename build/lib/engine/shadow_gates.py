"""
engine/shadow_gates.py

Freakto v6.2.1 - Candidate + Regime Shadow Gate Activator

Purpose:
- Take the best research gates found by Backtest Gate Simulator.
- Apply them to live/forward decisions in logs/decisions.csv in SHADOW mode.
- Join with logs/decision_evaluations.csv when available.
- Track whether candidate gates keep their edge in Forward Test without opening
  paper trades and without affecting live/paper decisions.

Safety:
This module never sends orders and never creates paper trades. It only labels
existing decisions and writes research reports under logs/shadow_gates/.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from engine.csv_utils import read_csv_dicts_lenient


VERSION = "v6.2.1"
LOG_DIR = Path("logs")
DECISIONS_FILE = LOG_DIR / "decisions.csv"
EVALUATIONS_FILE = LOG_DIR / "decision_evaluations.csv"
SHADOW_DIR = LOG_DIR / "shadow_gates"
SHADOW_SIGNALS_FILE = SHADOW_DIR / "shadow_gate_signals.csv"
SHADOW_RUNS_FILE = SHADOW_DIR / "shadow_gate_runs.csv"

RETURN_COLUMNS = {
    "4h": "return_after_4h_pct",
    "12h": "return_after_12h_pct",
    "24h": "return_after_24h_pct",
}

LIVE_KNOWN_NUMERIC_COLUMNS = [
    "score",
    "trend_score",
    "momentum_score",
    "volume_score",
    "structure_score",
    "historical_edge_score",
    "long_score",
    "short_score",
]

DIRECTIONAL_SIDES = {"LONG", "SHORT"}


@dataclass
class ShadowGateSpec:
    name: str
    family: str
    priority: int
    description: str
    filters: Dict[str, object] = field(default_factory=dict)
    origin: str = "BACKTEST_GATE_SIMULATOR_v5.3.2"
    mode: str = "SHADOW_ONLY"


@dataclass
class ShadowGateMetric:
    gate: str
    family: str
    priority: int
    verdict: str
    total_signals: int
    evaluated_samples: int
    pending_samples: int
    partial_samples: int
    avg_return_pct: float
    median_return_pct: float
    win_rate: float
    target_1_hit_rate: float
    stop_hit_rate: float
    mfe_mean_pct: float
    mae_mean_pct: float
    mfe_mae_ratio: float
    best_return_pct: float
    worst_return_pct: float
    latest_signal_utc: str = ""
    latest_candle_timestamp: str = ""
    description: str = ""
    warnings: List[str] = field(default_factory=list)
    filters: Dict[str, object] = field(default_factory=dict)


@dataclass
class ShadowGateReport:
    run_id: str
    generated_utc: str
    status: str
    horizon: str
    min_samples: int
    decisions: int
    directional_decisions: int
    shadow_signals: int
    evaluated_shadow_samples: int
    pending_shadow_samples: int
    gates_tracked: int
    confirmed_candidates: int
    building_candidates: int
    rejected_candidates: int
    top_gates: List[Dict]
    gate_metrics: List[Dict]
    recent_signals: List[Dict]
    blockers: List[str]
    recommendations: List[str]
    warnings: List[str]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id() -> str:
    return "shadow_gate_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator * 100, 2) if denominator else 0.0


def _safe_str(value, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return default
    return text


def _safe_float(value, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        text = str(value).replace(",", "").strip()
        if not text or text.lower() in {"nan", "none", "null", "نامشخص"}:
            return default
        return float(text)
    except Exception:
        return default


def _bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def _read_csv_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        _, rows = read_csv_dicts_lenient(path)
        return pd.DataFrame(rows)


def _normalize_risk(value: object) -> str:
    text = _safe_str(value).lower().replace("_", " ").replace("-", " ")
    if not text:
        return ""
    if "medium" in text or text in {"مدیوم", "متوسط"}:
        return "MEDIUM"
    if "low" in text or "conservative" in text or text in {"کم", "پایین"}:
        return "LOW"
    if "high" in text or text in {"زیاد", "بالا"}:
        return "HIGH"
    return text.upper()


def _prepare_decisions(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    work = df.copy()
    if "_extra" in work.columns:
        work = work.drop(columns=["_extra"])

    defaults = {
        "decision_id": "",
        "logged_at_utc": "",
        "candle_timestamp": "",
        "symbol": "",
        "timeframe": "",
        "side": "NEUTRAL",
        "score": 0,
        "confidence_label": "",
        "risk_label": "",
        "actionability": "",
        "is_actionable": "",
        "regime_label": "",
        "regime_confidence": "",
        "regime_source": "",
        "regime_label_quality": "",
        "trend_state": "",
        "volatility_state": "",
        "market_phase": "",
        "trend_score": 0,
        "momentum_score": 0,
        "volume_score": 0,
        "structure_score": 0,
        "historical_edge_score": 0,
        "long_score": 0,
        "short_score": 0,
    }
    for col, default in defaults.items():
        if col not in work.columns:
            work[col] = default

    for col in LIVE_KNOWN_NUMERIC_COLUMNS:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)

    for col in ["decision_id", "logged_at_utc", "candle_timestamp", "symbol", "timeframe", "side", "confidence_label", "risk_label", "actionability", "regime_label"]:
        work[col] = work[col].astype(str).fillna("").str.strip()

    # Fallback stable id for very old logs.
    missing_id = work["decision_id"].astype(str).str.len() == 0
    if missing_id.any():
        fallback = (
            work["candle_timestamp"].astype(str) + "|" +
            work["symbol"].astype(str) + "|" +
            work["timeframe"].astype(str) + "|" +
            work["side"].astype(str) + "|" +
            work["score"].astype(str)
        )
        work.loc[missing_id, "decision_id"] = fallback.loc[missing_id].apply(lambda x: "legacy_" + str(abs(hash(x)))[:12])

    work["side"] = work["side"].astype(str).str.upper()
    work["risk_normalized"] = work["risk_label"].apply(_normalize_risk)
    return work


def _prepare_evaluations(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    work = df.copy()
    if "decision_id" not in work.columns:
        return pd.DataFrame()
    for col in ["decision_id", "evaluation_status", "symbol", "timeframe", "side"]:
        if col not in work.columns:
            work[col] = ""
        work[col] = work[col].astype(str).fillna("").str.strip()
    for col in list(RETURN_COLUMNS.values()) + ["mfe_pct", "mae_pct"]:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")
    return work


def base_shadow_gates() -> List[ShadowGateSpec]:
    """Backtest-derived gates from v5.3.2/v6.0 to track in Forward/Shadow mode."""
    return [
        ShadowGateSpec(
            name="VOLUME_SCORE_GE_10",
            family="primary_backtest_candidate",
            priority=1,
            description="Backtest candidate قوی: volume_score >= 10.",
            filters={"volume_score_min": 10},
            origin="BACKTEST_GATE_SIMULATOR_v5.3.2",
        ),
        ShadowGateSpec(
            name="RISK_MEDIUM",
            family="primary_backtest_candidate",
            priority=2,
            description="Backtest candidate با sample بیشتر: risk_label = Medium.",
            filters={"risk_normalized_in": ["MEDIUM"]},
            origin="BACKTEST_GATE_SIMULATOR_v5.3.2",
        ),
        ShadowGateSpec(
            name="HISTORICAL_EDGE_SCORE_GE_1",
            family="primary_backtest_candidate",
            priority=3,
            description="Backtest candidate با stop کمتر: historical_edge_score >= 1.",
            filters={"historical_edge_score_min": 1},
            origin="BACKTEST_GATE_SIMULATOR_v5.3.2",
        ),
        ShadowGateSpec(
            name="STRUCTURE_SCORE_GE_10",
            family="review_backtest_candidate",
            priority=4,
            description="مثبت ولی نیازمند review: structure_score >= 10.",
            filters={"structure_score_min": 10},
            origin="BACKTEST_GATE_SIMULATOR_v5.3.2",
        ),
        ShadowGateSpec(
            name="SCORE_GE_80",
            family="small_sample_positive",
            priority=5,
            description="مثبت کم‌نمونه: score >= 80؛ فقط watchlist تحقیقاتی.",
            filters={"score_min": 80},
            origin="BACKTEST_GATE_SIMULATOR_v5.3.2",
        ),
        ShadowGateSpec(
            name="DOGE_SHORT_WATCH",
            family="symbol_side_watch",
            priority=6,
            description="مثبت کم‌نمونه: DOGE/USDT SHORT.",
            filters={"symbol_in": ["DOGE/USDT"], "side_in": ["SHORT"]},
            origin="BACKTEST_GATE_SIMULATOR_v5.3.2",
        ),
        ShadowGateSpec(
            name="BNB_LONG_SCORE_GE_60",
            family="symbol_side_watch",
            priority=7,
            description="مثبت کم‌نمونه: BNB/USDT LONG + score>=60.",
            filters={"symbol_in": ["BNB/USDT"], "side_in": ["LONG"], "score_min": 60},
            origin="BACKTEST_GATE_SIMULATOR_v5.3.2",
        ),
    ]


def regime_shadow_gates() -> List[ShadowGateSpec]:
    """Regime-specific shadow gates activated from v6.1 Regime-Gate Matrix.

    These are deliberately SHADOW_ONLY. They do not change Paper/Live behavior.
    They are encoded statically from the v6.1 proposals so GitHub Actions can
    keep collecting Forward samples even before the next matrix report is saved.
    """
    return [
        ShadowGateSpec(
            name="REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10",
            family="regime_gate_matrix_candidate",
            priority=0,
            description="v6.1 regime proposal: TRENDING_BEAR + structure_score >= 10.",
            filters={"regime_label_in": ["TRENDING_BEAR"], "structure_score_min": 10},
            origin="REGIME_GATE_MATRIX_v6.1.0",
        ),
        ShadowGateSpec(
            name="REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT",
            family="regime_gate_matrix_candidate",
            priority=0,
            description="v6.1 regime proposal: TRENDING_BEAR + structure_score >= 10 + SHORT.",
            filters={"regime_label_in": ["TRENDING_BEAR"], "structure_score_min": 10, "side_in": ["SHORT"]},
            origin="REGIME_GATE_MATRIX_v6.1.0",
        ),
        ShadowGateSpec(
            name="REGIME_TRENDING_BEAR__RISK_MEDIUM",
            family="regime_gate_matrix_candidate",
            priority=0,
            description="v6.1 regime proposal: TRENDING_BEAR + risk_label = Medium.",
            filters={"regime_label_in": ["TRENDING_BEAR"], "risk_normalized_in": ["MEDIUM"]},
            origin="REGIME_GATE_MATRIX_v6.1.0",
        ),
        ShadowGateSpec(
            name="REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT",
            family="regime_gate_matrix_candidate",
            priority=0,
            description="v6.1 regime proposal: TRENDING_BEAR + risk_label = Medium + SHORT.",
            filters={"regime_label_in": ["TRENDING_BEAR"], "risk_normalized_in": ["MEDIUM"], "side_in": ["SHORT"]},
            origin="REGIME_GATE_MATRIX_v6.1.0",
        ),
    ]


def candidate_shadow_gates(*, include_regime: bool = True) -> List[ShadowGateSpec]:
    """All shadow gates currently tracked.

    Base gates come from v5.3.2/v6.0. Regime-specific gates come from v6.1 and
    are activated in v6.2 for Forward-only validation. All gates are live-known:
    they use only decision-time fields such as symbol, side, regime_label,
    risk_label and component scores. Outcome columns are used only for evaluation.
    """
    gates = base_shadow_gates()
    if include_regime:
        gates = regime_shadow_gates() + gates
    # Deterministic order: regime activators first, then older gates.
    return sorted(gates, key=lambda g: (g.priority, g.name))

def _apply_gate(df: pd.DataFrame, spec: ShadowGateSpec) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    mask = pd.Series([True] * len(df), index=df.index)
    filters = spec.filters or {}

    def has(col: str) -> bool:
        return col in df.columns

    # Exact/list filters. Support both native shadow filter keys and the v6 research_utils filter style.
    if "symbol" in filters and has("symbol"):
        mask &= df["symbol"].astype(str).str.upper() == str(filters["symbol"]).upper()
    if "symbol_in" in filters and has("symbol"):
        mask &= df["symbol"].astype(str).str.upper().isin([str(x).upper() for x in filters["symbol_in"]])
    if "side" in filters and has("side"):
        mask &= df["side"].astype(str).str.upper() == str(filters["side"]).upper()
    if "side_in" in filters and has("side"):
        mask &= df["side"].astype(str).str.upper().isin([str(x).upper() for x in filters["side_in"]])
    if "regime_label" in filters and has("regime_label"):
        mask &= df["regime_label"].astype(str).str.upper() == str(filters["regime_label"]).upper()
    if "regime_label_in" in filters and has("regime_label"):
        mask &= df["regime_label"].astype(str).str.upper().isin([str(x).upper() for x in filters["regime_label_in"]])
    if "actionability" in filters and has("actionability"):
        mask &= df["actionability"].astype(str).str.upper() == str(filters["actionability"]).upper()
    if "actionability_in" in filters and has("actionability"):
        mask &= df["actionability"].astype(str).str.upper().isin([str(x).upper() for x in filters["actionability_in"]])
    if "risk_label" in filters and has("risk_normalized"):
        mask &= df["risk_normalized"].astype(str).str.upper() == _normalize_risk(filters["risk_label"])
    if "risk_normalized_in" in filters and has("risk_normalized"):
        mask &= df["risk_normalized"].astype(str).str.upper().isin([str(x).upper() for x in filters["risk_normalized_in"]])
    if "confidence_in" in filters and has("confidence_label"):
        mask &= df["confidence_label"].astype(str).str.upper().isin([str(x).upper() for x in filters["confidence_in"]])

    for col in LIVE_KNOWN_NUMERIC_COLUMNS:
        if not has(col):
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        min_key = f"{col}_min"
        max_key = f"{col}_max"
        ge_key = f"{col}__ge"
        le_key = f"{col}__le"
        if min_key in filters:
            mask &= values >= float(filters[min_key])
        if max_key in filters:
            mask &= values <= float(filters[max_key])
        if ge_key in filters:
            mask &= values >= float(filters[ge_key])
        if le_key in filters:
            mask &= values <= float(filters[le_key])

    return df[mask].copy()


def _make_shadow_signal_rows(decisions: pd.DataFrame, evaluations: pd.DataFrame, gates: List[ShadowGateSpec], horizon: str) -> pd.DataFrame:
    if decisions.empty:
        return pd.DataFrame()
    directional = decisions[decisions["side"].isin(DIRECTIONAL_SIDES)].copy()
    if directional.empty:
        return pd.DataFrame()

    eval_cols = [
        "decision_id", "evaluation_status", "available_future_candles",
        "return_after_4h_pct", "return_after_12h_pct", "return_after_24h_pct",
        "target_1_hit", "target_2_hit", "target_3_hit", "stop_hit", "mfe_pct", "mae_pct", "evaluated_candles",
    ]
    eval_work = evaluations.copy()
    if eval_work.empty:
        eval_work = pd.DataFrame(columns=eval_cols)
    for col in eval_cols:
        if col not in eval_work.columns:
            eval_work[col] = ""
    eval_work = eval_work[eval_cols].drop_duplicates(subset=["decision_id"], keep="last")

    rows: List[Dict] = []
    return_col = RETURN_COLUMNS.get(horizon, RETURN_COLUMNS["24h"])
    generated_utc = utc_now_iso()

    for gate in gates:
        selected = _apply_gate(directional, gate)
        if selected.empty:
            continue
        joined = selected.merge(eval_work, on="decision_id", how="left", suffixes=("", "_eval"))
        for _, row in joined.iterrows():
            eval_status = _safe_str(row.get("evaluation_status"), "PENDING").upper()
            selected_return = _safe_float(row.get(return_col), None)
            if not eval_status or eval_status == "NAN":
                eval_status = "PENDING"
            shadow_status = "EVALUATED" if selected_return is not None and eval_status == "COMPLETE" else ("PARTIAL" if eval_status == "PARTIAL" else "PENDING")
            rows.append({
                "shadow_logged_at_utc": generated_utc,
                "gate_name": gate.name,
                "gate_family": gate.family,
                "gate_priority": gate.priority,
                "gate_origin": gate.origin,
                "gate_mode": gate.mode,
                "gate_description": gate.description,
                "decision_id": row.get("decision_id", ""),
                "decision_logged_at_utc": row.get("logged_at_utc", ""),
                "candle_timestamp": row.get("candle_timestamp", ""),
                "symbol": row.get("symbol", ""),
                "timeframe": row.get("timeframe", ""),
                "side": row.get("side", ""),
                "score": row.get("score", ""),
                "actionability": row.get("actionability", ""),
                "confidence_label": row.get("confidence_label", ""),
                "risk_label": row.get("risk_label", ""),
                "risk_normalized": row.get("risk_normalized", ""),
                "regime_label": row.get("regime_label", ""),
                "trend_score": row.get("trend_score", ""),
                "momentum_score": row.get("momentum_score", ""),
                "volume_score": row.get("volume_score", ""),
                "structure_score": row.get("structure_score", ""),
                "historical_edge_score": row.get("historical_edge_score", ""),
                "long_score": row.get("long_score", ""),
                "short_score": row.get("short_score", ""),
                "shadow_status": shadow_status,
                "evaluation_status": eval_status,
                "selected_horizon": horizon,
                "selected_return_pct": selected_return if selected_return is not None else "",
                "return_after_4h_pct": row.get("return_after_4h_pct", ""),
                "return_after_12h_pct": row.get("return_after_12h_pct", ""),
                "return_after_24h_pct": row.get("return_after_24h_pct", ""),
                "target_1_hit": row.get("target_1_hit", ""),
                "target_2_hit": row.get("target_2_hit", ""),
                "target_3_hit": row.get("target_3_hit", ""),
                "stop_hit": row.get("stop_hit", ""),
                "mfe_pct": row.get("mfe_pct", ""),
                "mae_pct": row.get("mae_pct", ""),
                "filters": json.dumps(gate.filters, ensure_ascii=False),
            })

    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    out = out.drop_duplicates(subset=["gate_name", "decision_id"], keep="last")
    return out


def _metric_for_gate(group: pd.DataFrame, spec: Optional[ShadowGateSpec], horizon: str, min_samples: int) -> ShadowGateMetric:
    total = int(len(group))
    evaluated = group[group["shadow_status"].astype(str) == "EVALUATED"].copy() if not group.empty else pd.DataFrame()
    partial = int((group.get("shadow_status", pd.Series(dtype=str)).astype(str) == "PARTIAL").sum()) if not group.empty else 0
    pending = int(total - len(evaluated) - partial)
    ret = pd.to_numeric(evaluated.get("selected_return_pct", pd.Series(dtype=float)), errors="coerce").dropna()
    t1 = _bool_series(evaluated.get("target_1_hit", pd.Series(dtype=str))).sum() if not evaluated.empty else 0
    st = _bool_series(evaluated.get("stop_hit", pd.Series(dtype=str))).sum() if not evaluated.empty else 0
    mfe = pd.to_numeric(evaluated.get("mfe_pct", pd.Series(dtype=float)), errors="coerce").dropna()
    mae = pd.to_numeric(evaluated.get("mae_pct", pd.Series(dtype=float)), errors="coerce").dropna()

    samples = int(len(ret))
    avg = round(float(ret.mean()), 4) if samples else 0.0
    win = _rate(int((ret > 0).sum()), samples)
    t1_rate = _rate(int(t1), samples)
    stop_rate = _rate(int(st), samples)
    mfe_mean = float(mfe.mean()) if len(mfe) else 0.0
    mae_mean = float(mae.mean()) if len(mae) else 0.0
    mfe_mae = round(mfe_mean / abs(mae_mean), 3) if mae_mean else 0.0

    warnings: List[str] = []
    if samples < min_samples:
        verdict = "SHADOW_BUILDING"
        warnings.append(f"Forward evaluated samples کمتر از حداقل {min_samples} است: {samples}")
    elif avg > 0 and win >= 50 and t1_rate >= stop_rate and mfe_mae >= 1.0:
        verdict = "SHADOW_CONFIRMED_CANDIDATE"
    elif avg > 0:
        verdict = "SHADOW_POSITIVE_NEEDS_REVIEW"
        warnings.append("بازده Forward مثبت است، اما همه معیارهای کیفیت کامل نیستند.")
    else:
        verdict = "SHADOW_REJECT_NEGATIVE_FORWARD"
        warnings.append("Forward shadow edge مثبت نیست.")

    latest_signal_utc = ""
    latest_candle = ""
    if not group.empty:
        try:
            latest = group.sort_values(["decision_logged_at_utc", "candle_timestamp"]).iloc[-1]
            latest_signal_utc = _safe_str(latest.get("decision_logged_at_utc"))
            latest_candle = _safe_str(latest.get("candle_timestamp"))
        except Exception:
            pass

    return ShadowGateMetric(
        gate=str(group["gate_name"].iloc[0]) if not group.empty else (spec.name if spec else "UNKNOWN"),
        family=str(group["gate_family"].iloc[0]) if not group.empty else (spec.family if spec else "unknown"),
        priority=int(group["gate_priority"].iloc[0]) if not group.empty and str(group["gate_priority"].iloc[0]).strip() else (spec.priority if spec else 999),
        verdict=verdict,
        total_signals=total,
        evaluated_samples=samples,
        pending_samples=max(0, pending),
        partial_samples=max(0, partial),
        avg_return_pct=avg,
        median_return_pct=round(float(ret.median()), 4) if samples else 0.0,
        win_rate=win,
        target_1_hit_rate=t1_rate,
        stop_hit_rate=stop_rate,
        mfe_mean_pct=round(mfe_mean, 4),
        mae_mean_pct=round(mae_mean, 4),
        mfe_mae_ratio=mfe_mae,
        best_return_pct=round(float(ret.max()), 4) if samples else 0.0,
        worst_return_pct=round(float(ret.min()), 4) if samples else 0.0,
        latest_signal_utc=latest_signal_utc,
        latest_candle_timestamp=latest_candle,
        description=spec.description if spec else str(group.get("gate_description", pd.Series([""])).iloc[0]),
        warnings=warnings,
        filters=spec.filters if spec else {},
    )


def _sort_metrics(metrics: List[ShadowGateMetric]) -> List[ShadowGateMetric]:
    verdict_rank = {
        "SHADOW_CONFIRMED_CANDIDATE": 5,
        "SHADOW_POSITIVE_NEEDS_REVIEW": 4,
        "SHADOW_BUILDING": 3,
        "SHADOW_REJECT_NEGATIVE_FORWARD": 1,
    }
    return sorted(
        metrics,
        key=lambda m: (
            verdict_rank.get(m.verdict, 0),
            m.evaluated_samples,
            m.avg_return_pct,
            -m.stop_hit_rate,
            -m.priority,
        ),
        reverse=True,
    )


def _build_recommendations(metrics: List[ShadowGateMetric], min_samples: int) -> Tuple[List[str], List[str]]:
    blockers: List[str] = []
    recs: List[str] = []
    confirmed = [m for m in metrics if m.verdict == "SHADOW_CONFIRMED_CANDIDATE"]
    positive_review = [m for m in metrics if m.verdict == "SHADOW_POSITIVE_NEEDS_REVIEW"]
    building = [m for m in metrics if m.verdict == "SHADOW_BUILDING"]

    if not metrics:
        blockers.append("هیچ shadow signal هنوز ثبت نشده است.")
        recs.append("اجازه بده GitHub Actions چند چرخه Forward دیگر اجرا کند یا monitor.py --once را اجرا کن.")
        return blockers, recs

    total_eval = sum(m.evaluated_samples for m in metrics)
    if total_eval < min_samples:
        blockers.append(f"کل نمونه‌های ارزیابی‌شده Shadow کمتر از {min_samples} است: {total_eval}")

    if confirmed:
        top = confirmed[0]
        recs.append(f"بهترین gate تأییدشده در Forward Shadow: {top.gate} | avg={top.avg_return_pct}% | eval={top.evaluated_samples}.")
        recs.append("حتی با تأیید Shadow، Paper واقعی فقط بعد از بررسی Forward/Paper و Readiness مجاز است.")
    elif positive_review:
        top = positive_review[0]
        recs.append(f"Forward Shadow مثبت ولی نیازمند review: {top.gate} | avg={top.avg_return_pct}% | eval={top.evaluated_samples}.")
    elif building:
        top = building[0]
        recs.append(f"Shadow هنوز در حال ساخت داده است؛ فعال‌ترین gate: {top.gate} | signals={top.total_signals}, evaluated={top.evaluated_samples}.")
        recs.append(f"برای هر gate حداقل {min_samples} نمونه Forward کامل لازم است.")
    else:
        recs.append("هیچ gate در Forward Shadow مثبت نیست؛ candidateهای Backtest فعلاً تأیید نشده‌اند.")

    regime = [m for m in metrics if m.family == "regime_gate_matrix_candidate"]
    if regime:
        active_regime = [m for m in regime if m.total_signals > 0]
        if active_regime:
            top_regime = sorted(active_regime, key=lambda m: (m.evaluated_samples, m.avg_return_pct), reverse=True)[0]
            recs.append(f"فعال‌ترین Regime Shadow gate: {top_regime.gate} | signals={top_regime.total_signals}, eval={top_regime.evaluated_samples}.")
        else:
            recs.append("Regime Shadow gateهای v6.1 فعال شده‌اند، اما هنوز هیچ تصمیم Forward آن‌ها را پاس نکرده است.")
    primary = [m for m in metrics if m.family == "primary_backtest_candidate"]
    if primary:
        recs.append("سه gate پایه که باید زیر نظر بمانند: VOLUME_SCORE_GE_10، RISK_MEDIUM، HISTORICAL_EDGE_SCORE_GE_1.")
    return blockers, recs


def run_shadow_gate_validation(
    *,
    horizon: str = "24h",
    min_samples: int = 30,
    decisions_path: Path = DECISIONS_FILE,
    evaluations_path: Path = EVALUATIONS_FILE,
) -> ShadowGateReport:
    horizon = str(horizon).lower().replace(" ", "")
    if horizon not in RETURN_COLUMNS:
        horizon = "24h"
    run_id = make_run_id()
    decisions_raw = _read_csv_df(decisions_path)
    evaluations_raw = _read_csv_df(evaluations_path)
    decisions = _prepare_decisions(decisions_raw)
    evaluations = _prepare_evaluations(evaluations_raw)
    gates = candidate_shadow_gates()

    signals = _make_shadow_signal_rows(decisions, evaluations, gates, horizon=horizon)
    metrics: List[ShadowGateMetric] = []
    for gate in gates:
        if signals.empty:
            group = pd.DataFrame()
        else:
            group = signals[signals["gate_name"].astype(str) == gate.name].copy()
        # Keep empty gate metrics so the operator can see all tracked gates.
        if group.empty:
            metrics.append(ShadowGateMetric(
                gate=gate.name,
                family=gate.family,
                priority=gate.priority,
                verdict="SHADOW_BUILDING",
                total_signals=0,
                evaluated_samples=0,
                pending_samples=0,
                partial_samples=0,
                avg_return_pct=0.0,
                median_return_pct=0.0,
                win_rate=0.0,
                target_1_hit_rate=0.0,
                stop_hit_rate=0.0,
                mfe_mean_pct=0.0,
                mae_mean_pct=0.0,
                mfe_mae_ratio=0.0,
                best_return_pct=0.0,
                worst_return_pct=0.0,
                description=gate.description,
                warnings=["هنوز هیچ تصمیم Forward این gate را پاس نکرده است."],
                filters=gate.filters,
            ))
        else:
            metrics.append(_metric_for_gate(group, gate, horizon=horizon, min_samples=min_samples))

    metrics = _sort_metrics(metrics)
    blockers, recs = _build_recommendations(metrics, min_samples=min_samples)
    directional = decisions[decisions["side"].isin(DIRECTIONAL_SIDES)] if not decisions.empty else pd.DataFrame()
    evaluated_total = int(sum(m.evaluated_samples for m in metrics))
    pending_total = int(sum(m.pending_samples for m in metrics))
    confirmed = int(sum(1 for m in metrics if m.verdict == "SHADOW_CONFIRMED_CANDIDATE"))
    building = int(sum(1 for m in metrics if m.verdict == "SHADOW_BUILDING"))
    rejected = int(sum(1 for m in metrics if m.verdict == "SHADOW_REJECT_NEGATIVE_FORWARD"))

    if confirmed:
        status = "SHADOW_CONFIRMED_CANDIDATES"
    elif signals.empty:
        status = "SHADOW_WAITING_FOR_SIGNALS"
    elif evaluated_total < min_samples:
        status = "SHADOW_COLLECTING_FORWARD_DATA"
    else:
        status = "SHADOW_REVIEW_REQUIRED"

    recent: List[Dict] = []
    if not signals.empty:
        display_cols = [
            "gate_name", "gate_family", "shadow_status", "decision_logged_at_utc", "candle_timestamp", "symbol", "side", "score", "selected_return_pct", "actionability", "risk_label", "regime_label",
        ]
        for col in display_cols:
            if col not in signals.columns:
                signals[col] = ""
        recent = signals.sort_values(["decision_logged_at_utc", "candle_timestamp"]).tail(20)[display_cols].to_dict("records")

    warnings = [
        "Shadow Gate هیچ Paper Trade و هیچ سفارش واقعی ایجاد نمی‌کند؛ فقط برچسب تحقیقاتی می‌زند.",
        "Gateهای پایه از Backtest و Gateهای Regime از v6.1 Regime-Gate Matrix آمده‌اند و باید در Forward مستقل تأیید شوند.",
        "تا وقتی هر gate، مخصوصاً gateهای Regime، حداقل 30 نمونه Forward کامل ندارد، نتیجه آماری قابل اتکا نیست.",
    ]

    return ShadowGateReport(
        run_id=run_id,
        generated_utc=utc_now_iso(),
        status=status,
        horizon=horizon,
        min_samples=min_samples,
        decisions=int(len(decisions)),
        directional_decisions=int(len(directional)),
        shadow_signals=int(len(signals)) if not signals.empty else 0,
        evaluated_shadow_samples=evaluated_total,
        pending_shadow_samples=pending_total,
        gates_tracked=int(len(gates)),
        confirmed_candidates=confirmed,
        building_candidates=building,
        rejected_candidates=rejected,
        top_gates=[asdict(m) for m in metrics[:10]],
        gate_metrics=[asdict(m) for m in metrics],
        recent_signals=recent,
        blockers=blockers,
        recommendations=recs,
        warnings=warnings,
    )


def _fmt_metric(row: Dict) -> str:
    warn = row.get("warnings") or []
    warn_text = f" | warn={warn[0]}" if warn else ""
    return (
        f"- {row.get('gate')} [{row.get('verdict')}]: "
        f"signals={row.get('total_signals')} | eval={row.get('evaluated_samples')} | "
        f"pending={row.get('pending_samples')} | avg={row.get('avg_return_pct')}% | "
        f"win={row.get('win_rate')}% | T1={row.get('target_1_hit_rate')}% | "
        f"Stop={row.get('stop_hit_rate')}% | MFE/MAE={row.get('mfe_mae_ratio')}{warn_text}"
    )


def format_shadow_gate_console(report: ShadowGateReport, *, detail: bool = True, top: int = 10) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("🧪 Freakto Regime Shadow Gate Activator v6.2.0")
    lines.append("=" * 110)
    lines.append(f"Status                 : {report.status}")
    lines.append(f"Run ID                 : {report.run_id}")
    lines.append(f"Horizon                : {report.horizon}")
    lines.append(f"Min Samples            : {report.min_samples}")
    lines.append(f"Decisions              : {report.decisions}")
    lines.append(f"Directional Decisions  : {report.directional_decisions}")
    lines.append(f"Gates Tracked          : {report.gates_tracked}")
    lines.append(f"Shadow Signals         : {report.shadow_signals}")
    lines.append(f"Evaluated Shadow       : {report.evaluated_shadow_samples}")
    lines.append(f"Pending Shadow         : {report.pending_shadow_samples}")
    lines.append(f"Confirmed Candidates   : {report.confirmed_candidates}")
    lines.append(f"Building Candidates    : {report.building_candidates}")
    lines.append(f"Rejected Candidates    : {report.rejected_candidates}")

    if report.top_gates:
        lines.append("")
        lines.append("Gate Shadow Metrics:")
        for row in report.top_gates[:top]:
            lines.append(_fmt_metric(row))

    if detail and report.recent_signals:
        lines.append("")
        lines.append("Recent Shadow Signals:")
        for row in report.recent_signals[-10:]:
            lines.append(
                f"- {row.get('gate_name')} | {row.get('shadow_status')} | {row.get('symbol')} {row.get('side')} "
                f"score={row.get('score')} | return={row.get('selected_return_pct')} | candle={row.get('candle_timestamp')}"
            )

    if report.blockers:
        lines.append("")
        lines.append("Shadow Blockers:")
        for item in report.blockers:
            lines.append(f"⛔ {item}")

    if report.recommendations:
        lines.append("")
        lines.append("Shadow Recommendations:")
        for item in report.recommendations:
            lines.append(f"→ {item}")

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for item in report.warnings:
            lines.append(f"⚠️ {item}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_shadow_gate_report(report: ShadowGateReport) -> str:
    lines: List[str] = []
    lines.append("# Freakto Regime Shadow Gate Activator v6.2.0")
    lines.append("")
    lines.append("## Summary")
    for key in [
        "status", "generated_utc", "horizon", "min_samples", "decisions", "directional_decisions",
        "gates_tracked", "shadow_signals", "evaluated_shadow_samples", "pending_shadow_samples",
        "confirmed_candidates", "building_candidates", "rejected_candidates",
    ]:
        lines.append(f"- {key}: `{getattr(report, key)}`")
    lines.append("")
    lines.append("## Gate Metrics")
    lines.append("| Gate | Verdict | Signals | Evaluated | Pending | Avg | Win | T1 | Stop | MFE/MAE | Description |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in report.gate_metrics:
        lines.append(
            f"| {row.get('gate')} | {row.get('verdict')} | {row.get('total_signals')} | {row.get('evaluated_samples')} | "
            f"{row.get('pending_samples')} | {row.get('avg_return_pct')}% | {row.get('win_rate')}% | "
            f"{row.get('target_1_hit_rate')}% | {row.get('stop_hit_rate')}% | {row.get('mfe_mae_ratio')} | {row.get('description')} |"
        )
    lines.append("")
    if report.recent_signals:
        lines.append("## Recent Signals")
        lines.append("| Gate | Status | Symbol | Side | Score | Return | Candle |")
        lines.append("|---|---|---|---|---:|---:|---|")
        for row in report.recent_signals:
            lines.append(
                f"| {row.get('gate_name')} | {row.get('shadow_status')} | {row.get('symbol')} | {row.get('side')} | "
                f"{row.get('score')} | {row.get('selected_return_pct')} | {row.get('candle_timestamp')} |"
            )
        lines.append("")
    lines.append("## Recommendations")
    for item in report.recommendations:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Blockers")
    if report.blockers:
        for item in report.blockers:
            lines.append(f"- {item}")
    else:
        lines.append("- No major blocker.")
    lines.append("")
    lines.append("## Safety Notes")
    for item in report.warnings:
        lines.append(f"- {item}")
    return "\n".join(lines)


def _write_csv(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _append_run(report: ShadowGateReport, json_path: Path, report_path: Path) -> None:
    SHADOW_RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "run_id": report.run_id,
        "generated_utc": report.generated_utc,
        "status": report.status,
        "horizon": report.horizon,
        "min_samples": report.min_samples,
        "shadow_signals": report.shadow_signals,
        "evaluated_shadow_samples": report.evaluated_shadow_samples,
        "confirmed_candidates": report.confirmed_candidates,
        "building_candidates": report.building_candidates,
        "rejected_candidates": report.rejected_candidates,
        "json_path": str(json_path),
        "report_path": str(report_path),
    }
    exists = SHADOW_RUNS_FILE.exists() and SHADOW_RUNS_FILE.stat().st_size > 0
    with SHADOW_RUNS_FILE.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(row.keys()), extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def save_shadow_gate_validation(report: ShadowGateReport) -> Tuple[Path, Path, Path, Path]:
    SHADOW_DIR.mkdir(parents=True, exist_ok=True)
    json_path = SHADOW_DIR / f"shadow_gate_status_{report.run_id}.json"
    report_path = SHADOW_DIR / f"shadow_gate_report_{report.run_id}.md"
    metrics_csv = SHADOW_DIR / f"shadow_gate_metrics_{report.run_id}.csv"
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(format_shadow_gate_report(report), encoding="utf-8")
    _write_csv(metrics_csv, report.gate_metrics)

    # Rebuild the deterministic signal ledger each run from current decisions + evaluations.
    decisions = _prepare_decisions(_read_csv_df(DECISIONS_FILE))
    evaluations = _prepare_evaluations(_read_csv_df(EVALUATIONS_FILE))
    signals = _make_shadow_signal_rows(decisions, evaluations, candidate_shadow_gates(), horizon=report.horizon)
    if signals.empty:
        SHADOW_SIGNALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SHADOW_SIGNALS_FILE.write_text("", encoding="utf-8-sig")
    else:
        signals.to_csv(SHADOW_SIGNALS_FILE, index=False, encoding="utf-8-sig")

    _append_run(report, json_path=json_path, report_path=report_path)
    return json_path, report_path, metrics_csv, SHADOW_SIGNALS_FILE
