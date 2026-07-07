"""
engine/backtest_gate_simulator.py

Freakto v5.3.2 - Backtest Gate Simulator

Purpose:
- Test research-only entry gates on historical BACKTEST evaluations.
- Find whether any live-available subset has positive historical edge.
- Avoid lookahead: gate filters use only fields that would be known at decision time
  (symbol, side, actionability, score, confidence/risk/regime/component scores).
- Future outcome columns (returns, target hits, stop hits, MFE/MAE) are used only
  for evaluation metrics, never as filter conditions.

Safety:
This module never sends orders and never creates paper trades. It only reads
logs/historical_backtest_evaluations.csv and writes gate simulation reports.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from engine.csv_utils import read_csv_dicts_lenient
from engine.historical_backtest import BACKTEST_EVALUATIONS_FILE


LOG_DIR = Path("logs")
GATE_SIM_DIR = LOG_DIR / "backtests" / "gate_simulator"

RETURN_COLUMNS = {
    "4h": "return_after_4h_pct",
    "12h": "return_after_12h_pct",
    "24h": "return_after_24h_pct",
}

KNOWN_COMPONENT_COLUMNS = [
    "trend_score",
    "momentum_score",
    "volume_score",
    "structure_score",
    "historical_edge_score",
    "long_score",
    "short_score",
]

LIVE_KNOWN_FILTER_FIELDS = {
    "symbol",
    "side",
    "score",
    "actionability",
    "confidence_label",
    "risk_label",
    "regime_label",
    "trend_score",
    "momentum_score",
    "volume_score",
    "structure_score",
    "historical_edge_score",
    "long_score",
    "short_score",
    "is_actionable",
}


@dataclass
class GateSpec:
    name: str
    family: str
    description: str
    filters: Dict[str, object] = field(default_factory=dict)
    live_safe: bool = True


@dataclass
class GateResult:
    gate: str
    family: str
    description: str
    verdict: str
    live_safe: bool
    samples: int
    rows: int
    sample_share_pct: float
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
    avg_4h_return_pct: float
    avg_12h_return_pct: float
    avg_24h_return_pct: float
    research_score: float
    warnings: List[str] = field(default_factory=list)
    filters: Dict[str, object] = field(default_factory=dict)


@dataclass
class GateSimulationReport:
    run_id: str
    generated_utc: str
    status: str
    horizon: str
    min_samples: int
    total_rows: int
    complete_rows: int
    directional_samples: int
    baseline_avg_return_pct: float
    baseline_win_rate: float
    baseline_target_1_hit_rate: float
    baseline_stop_hit_rate: float
    gates_tested: int
    positive_gates: int
    research_candidates: int
    small_sample_positive_gates: int
    top_gates: List[Dict]
    results: List[Dict]
    blockers: List[str]
    recommendations: List[str]
    warnings: List[str]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id() -> str:
    return "gate_sim_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _rate(num: int, den: int) -> float:
    return round(num / den * 100, 2) if den else 0.0


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


def _read_backtest_rows(path: Path = BACKTEST_EVALUATIONS_FILE) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        _, rows = read_csv_dicts_lenient(path)
        return pd.DataFrame(rows)


def _prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    work = df.copy()
    numeric_cols = list(RETURN_COLUMNS.values()) + KNOWN_COMPONENT_COLUMNS + ["score", "mfe_pct", "mae_pct"]
    for col in numeric_cols:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce")
    for col, default in {
        "evaluation_status": "",
        "side": "",
        "symbol": "UNKNOWN",
        "actionability": "",
        "confidence_label": "",
        "risk_label": "",
        "regime_label": "",
    }.items():
        if col not in work.columns:
            work[col] = default
    return work


def _directional_complete(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    complete = df[df["evaluation_status"].astype(str).str.upper() == "COMPLETE"].copy()
    return complete[complete["side"].astype(str).isin(["LONG", "SHORT"])].copy()


def _unique_values(df: pd.DataFrame, col: str, limit: int = 50) -> List[str]:
    if df.empty or col not in df.columns:
        return []
    values = []
    for value in df[col].dropna().astype(str).unique().tolist():
        value = value.strip()
        if value and value.lower() not in {"nan", "none", "null"}:
            values.append(value)
    return sorted(values)[:limit]


def _gate_name(prefix: str, *parts: object) -> str:
    text = "_".join([prefix] + [str(part).replace("/", "").replace(" ", "_").replace("|", "_") for part in parts if str(part).strip()])
    return text.upper()


def _score_bucket_label(low: int, high: Optional[int] = None) -> str:
    if high is None:
        return f"score >= {low}"
    return f"score {low}-{high}"


def build_gate_specs(df: pd.DataFrame) -> List[GateSpec]:
    """Build deterministic research gates using only live-known columns."""
    specs: List[GateSpec] = []

    def add(name: str, family: str, description: str, filters: Dict[str, object]) -> None:
        specs.append(GateSpec(name=name, family=family, description=description, filters=filters, live_safe=True))

    add("BASELINE_DIRECTIONAL", "baseline", "تمام تصمیم‌های جهت‌دار کامل؛ فقط برای مقایسه.", {})
    add("ACTIONABLE_ONLY", "actionability", "فقط تصمیم‌هایی که موتور ACTIONABLE کرده است.", {"actionability_in": ["ACTIONABLE", "HIGH_ACTIONABILITY"]})
    add("WATCHLIST_OR_ACTIONABLE", "actionability", "WATCHLIST یا ACTIONABLE؛ گیت نیمه‌محافظه‌کار.", {"actionability_in": ["WATCHLIST", "ACTIONABLE", "HIGH_ACTIONABILITY"]})
    add("WATCHLIST_ONLY", "actionability", "فقط WATCHLIST برای مقایسه با ACTIONABLE.", {"actionability_in": ["WATCHLIST"]})
    add("NOT_ACTIONABLE_ONLY", "actionability", "NOT_ACTIONABLE فقط برای کنترل منفی؛ معمولاً نباید candidate شود.", {"actionability_in": ["NOT_ACTIONABLE"]})

    for side in ["LONG", "SHORT"]:
        add(_gate_name(side, "only"), "side", f"فقط معاملات {side}.", {"side_in": [side]})
        add(_gate_name("actionable", side), "actionability_side", f"ACTIONABLE فقط سمت {side}.", {"side_in": [side], "actionability_in": ["ACTIONABLE", "HIGH_ACTIONABILITY"]})
        add(_gate_name("watch_or_actionable", side), "actionability_side", f"WATCHLIST/ACTIONABLE فقط سمت {side}.", {"side_in": [side], "actionability_in": ["WATCHLIST", "ACTIONABLE", "HIGH_ACTIONABILITY"]})

    for threshold in [50, 60, 70, 80]:
        add(_gate_name("score_ge", threshold), "score", _score_bucket_label(threshold), {"score_min": threshold})
        add(_gate_name("actionable_score_ge", threshold), "actionability_score", f"ACTIONABLE + score >= {threshold}.", {"actionability_in": ["ACTIONABLE", "HIGH_ACTIONABILITY"], "score_min": threshold})
        for side in ["LONG", "SHORT"]:
            add(_gate_name("score_ge", threshold, side), "score_side", f"score >= {threshold} + {side}.", {"score_min": threshold, "side_in": [side]})
            add(_gate_name("actionable_score_ge", threshold, side), "actionability_score_side", f"ACTIONABLE + score >= {threshold} + {side}.", {"actionability_in": ["ACTIONABLE", "HIGH_ACTIONABILITY"], "score_min": threshold, "side_in": [side]})

    for low, high in [(40, 49), (50, 59), (60, 69), (70, 79), (80, 89), (90, None)]:
        filters = {"score_min": low}
        if high is not None:
            filters["score_max"] = high
        add(_gate_name("score_bucket", low, high or "plus"), "score_bucket", _score_bucket_label(low, high), filters)

    for symbol in _unique_values(df, "symbol"):
        add(_gate_name("symbol", symbol), "symbol", f"فقط نماد {symbol}.", {"symbol_in": [symbol]})
        add(_gate_name("symbol_actionable", symbol), "symbol_actionability", f"{symbol} + ACTIONABLE.", {"symbol_in": [symbol], "actionability_in": ["ACTIONABLE", "HIGH_ACTIONABILITY"]})
        add(_gate_name("symbol_watch_or_actionable", symbol), "symbol_actionability", f"{symbol} + WATCHLIST/ACTIONABLE.", {"symbol_in": [symbol], "actionability_in": ["WATCHLIST", "ACTIONABLE", "HIGH_ACTIONABILITY"]})
        for side in ["LONG", "SHORT"]:
            add(_gate_name("symbol_side", symbol, side), "symbol_side", f"{symbol} فقط {side}.", {"symbol_in": [symbol], "side_in": [side]})
            add(_gate_name("symbol_side_actionable", symbol, side), "symbol_side_actionability", f"{symbol} + {side} + ACTIONABLE.", {"symbol_in": [symbol], "side_in": [side], "actionability_in": ["ACTIONABLE", "HIGH_ACTIONABILITY"]})
            add(_gate_name("symbol_side_score_ge_60", symbol, side), "symbol_side_score", f"{symbol} + {side} + score >= 60.", {"symbol_in": [symbol], "side_in": [side], "score_min": 60})
            add(_gate_name("symbol_side_score_ge_80", symbol, side), "symbol_side_score", f"{symbol} + {side} + score >= 80.", {"symbol_in": [symbol], "side_in": [side], "score_min": 80})

    for confidence in _unique_values(df, "confidence_label"):
        add(_gate_name("confidence", confidence), "confidence", f"فقط confidence={confidence}.", {"confidence_in": [confidence]})
    for risk in _unique_values(df, "risk_label"):
        add(_gate_name("risk", risk), "risk", f"فقط risk_label={risk}.", {"risk_in": [risk]})
    for regime in _unique_values(df, "regime_label"):
        add(_gate_name("regime", regime), "regime", f"فقط regime={regime}.", {"regime_in": [regime]})

    component_thresholds = {
        "trend_score": [5, 10, 15],
        "momentum_score": [5, 10, 15],
        "volume_score": [5, 10, 15],
        "structure_score": [5, 10, 15],
        "historical_edge_score": [1, 5, 10],
        "long_score": [50, 60, 70],
        "short_score": [50, 60, 70],
    }
    for col, thresholds in component_thresholds.items():
        if col not in df.columns:
            continue
        for threshold in thresholds:
            add(_gate_name(col, "ge", threshold), "component", f"{col} >= {threshold}.", {f"{col}_min": threshold})

    # Composite research gates: still live-safe because they only use known fields.
    if "score" in df.columns:
        add("QUALITY_CORE_SCORE60_ACTIONABLE", "composite", "ACTIONABLE + score>=60 + risk not High.", {"actionability_in": ["ACTIONABLE", "HIGH_ACTIONABILITY"], "score_min": 60, "risk_not_in": ["High", "VERY_HIGH", "High Risk"]})
        add("QUALITY_CORE_SCORE80_WATCH_OR_ACTIONABLE", "composite", "WATCHLIST/ACTIONABLE + score>=80.", {"actionability_in": ["WATCHLIST", "ACTIONABLE", "HIGH_ACTIONABILITY"], "score_min": 80})
        add("LONG_SCORE60_ACTIONABLE", "composite", "LONG + ACTIONABLE + score>=60.", {"side_in": ["LONG"], "actionability_in": ["ACTIONABLE", "HIGH_ACTIONABILITY"], "score_min": 60})
        add("SHORT_SCORE60_ACTIONABLE", "composite", "SHORT + ACTIONABLE + score>=60.", {"side_in": ["SHORT"], "actionability_in": ["ACTIONABLE", "HIGH_ACTIONABILITY"], "score_min": 60})

    return specs


def _apply_gate(df: pd.DataFrame, spec: GateSpec) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    mask = pd.Series([True] * len(df), index=df.index)
    filters = spec.filters or {}

    def has(col: str) -> bool:
        return col in df.columns

    if "symbol_in" in filters and has("symbol"):
        mask &= df["symbol"].astype(str).isin([str(x) for x in filters["symbol_in"]])
    if "side_in" in filters and has("side"):
        mask &= df["side"].astype(str).isin([str(x) for x in filters["side_in"]])
    if "actionability_in" in filters and has("actionability"):
        mask &= df["actionability"].astype(str).isin([str(x) for x in filters["actionability_in"]])
    if "confidence_in" in filters and has("confidence_label"):
        mask &= df["confidence_label"].astype(str).isin([str(x) for x in filters["confidence_in"]])
    if "risk_in" in filters and has("risk_label"):
        mask &= df["risk_label"].astype(str).isin([str(x) for x in filters["risk_in"]])
    if "risk_not_in" in filters and has("risk_label"):
        mask &= ~df["risk_label"].astype(str).isin([str(x) for x in filters["risk_not_in"]])
    if "regime_in" in filters and has("regime_label"):
        mask &= df["regime_label"].astype(str).isin([str(x) for x in filters["regime_in"]])

    numeric_filter_names = [
        "score",
        "trend_score",
        "momentum_score",
        "volume_score",
        "structure_score",
        "historical_edge_score",
        "long_score",
        "short_score",
    ]
    for col in numeric_filter_names:
        if not has(col):
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        min_key = f"{col}_min"
        max_key = f"{col}_max"
        if min_key in filters:
            mask &= values >= float(filters[min_key])
        if max_key in filters:
            mask &= values <= float(filters[max_key])

    # Convenience alias for score_min/score_max.
    if has("score"):
        score = pd.to_numeric(df["score"], errors="coerce")
        if "score_min" in filters:
            mask &= score >= float(filters["score_min"])
        if "score_max" in filters:
            mask &= score <= float(filters["score_max"])

    return df[mask].copy()


def _metrics(group: pd.DataFrame, horizon: str, total_directional: int, min_samples: int) -> Dict:
    return_col = RETURN_COLUMNS.get(horizon, RETURN_COLUMNS["24h"])
    ret = pd.to_numeric(group.get(return_col, pd.Series(dtype=float)), errors="coerce").dropna()
    ret4 = pd.to_numeric(group.get("return_after_4h_pct", pd.Series(dtype=float)), errors="coerce").dropna()
    ret12 = pd.to_numeric(group.get("return_after_12h_pct", pd.Series(dtype=float)), errors="coerce").dropna()
    ret24 = pd.to_numeric(group.get("return_after_24h_pct", pd.Series(dtype=float)), errors="coerce").dropna()
    t1 = _bool_series(group.get("target_1_hit", pd.Series(dtype=str))).sum() if "target_1_hit" in group else 0
    st = _bool_series(group.get("stop_hit", pd.Series(dtype=str))).sum() if "stop_hit" in group else 0
    mfe = pd.to_numeric(group.get("mfe_pct", pd.Series(dtype=float)), errors="coerce").dropna()
    mae = pd.to_numeric(group.get("mae_pct", pd.Series(dtype=float)), errors="coerce").dropna()

    samples = int(len(ret))
    avg_return = round(float(ret.mean()), 4) if samples else 0.0
    win_rate = _rate(int((ret > 0).sum()), samples)
    t1_rate = _rate(int(t1), int(len(group)))
    stop_rate = _rate(int(st), int(len(group)))
    mfe_mean = float(mfe.mean()) if len(mfe) else 0.0
    mae_mean = float(mae.mean()) if len(mae) else 0.0
    mae_abs = abs(mae_mean)
    mfe_mae_ratio = round(mfe_mean / mae_abs, 3) if mae_abs else 0.0
    sample_factor = min(1.0, math.sqrt(samples / min_samples)) if min_samples else 1.0
    research_score = (
        avg_return * sample_factor
        + 0.015 * (win_rate - 50.0)
        + 0.01 * (t1_rate - stop_rate)
        + 0.10 * (mfe_mae_ratio - 1.0)
    )

    return {
        "rows": int(len(group)),
        "samples": samples,
        "sample_share_pct": _rate(samples, total_directional),
        "avg_return_pct": avg_return,
        "median_return_pct": round(float(ret.median()), 4) if samples else 0.0,
        "best_return_pct": round(float(ret.max()), 4) if samples else 0.0,
        "worst_return_pct": round(float(ret.min()), 4) if samples else 0.0,
        "win_rate": win_rate,
        "target_1_hit_rate": t1_rate,
        "stop_hit_rate": stop_rate,
        "mfe_mean_pct": round(mfe_mean, 4),
        "mae_mean_pct": round(mae_mean, 4),
        "mfe_mae_ratio": mfe_mae_ratio,
        "avg_4h_return_pct": round(float(ret4.mean()), 4) if len(ret4) else 0.0,
        "avg_12h_return_pct": round(float(ret12.mean()), 4) if len(ret12) else 0.0,
        "avg_24h_return_pct": round(float(ret24.mean()), 4) if len(ret24) else 0.0,
        "research_score": round(float(research_score), 4),
    }


def _verdict(metrics: Dict, min_samples: int) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    samples = int(metrics.get("samples", 0))
    avg = float(metrics.get("avg_return_pct", 0.0))
    win = float(metrics.get("win_rate", 0.0))
    t1 = float(metrics.get("target_1_hit_rate", 0.0))
    stop = float(metrics.get("stop_hit_rate", 0.0))
    mfe_mae = float(metrics.get("mfe_mae_ratio", 0.0))

    if samples == 0:
        return "NO_SAMPLES", ["هیچ نمونه‌ای برای این gate وجود ندارد."]
    if samples < 10:
        return "REJECT_TOO_SMALL", [f"sample بسیار کم است: {samples}"]
    if samples < min_samples and avg > 0:
        warnings.append(f"مثبت است ولی sample کمتر از حداقل {min_samples} است.")
        if stop > t1:
            warnings.append("Stop rate از Target hit بیشتر است؛ ریسک بالاست.")
        return "SMALL_SAMPLE_POSITIVE", warnings
    if samples < min_samples:
        return "REJECT_INSUFFICIENT_SAMPLE", [f"sample کمتر از حداقل {min_samples} است."]

    if avg > 0 and t1 >= stop and mfe_mae >= 1.0 and win >= 50.0:
        return "RESEARCH_CANDIDATE", []
    if avg > 0 and t1 >= stop:
        warnings.append("مثبت است اما همه معیارهای کیفیت کامل نیستند.")
        return "POSITIVE_BUT_NEEDS_REVIEW", warnings
    if avg > 0:
        warnings.append("بازده مثبت است ولی Target/Stop یا کیفیت مسیر ضعیف است.")
        return "POSITIVE_BUT_RISKY", warnings
    if avg >= -0.10 and mfe_mae >= 0.90:
        return "NEAR_BREAKEVEN_WATCH", ["تقریباً نزدیک صفر است؛ شاید با خروج/stop بهتر قابل تحقیق باشد."]
    return "REJECT_NEGATIVE_EDGE", ["میانگین بازده منفی است."]


def simulate_gate(spec: GateSpec, df: pd.DataFrame, *, horizon: str, min_samples: int, total_directional: int) -> GateResult:
    selected = _apply_gate(df, spec)
    metrics = _metrics(selected, horizon=horizon, total_directional=total_directional, min_samples=min_samples)
    verdict, warnings = _verdict(metrics, min_samples=min_samples)
    return GateResult(
        gate=spec.name,
        family=spec.family,
        description=spec.description,
        verdict=verdict,
        live_safe=spec.live_safe,
        filters=spec.filters,
        warnings=warnings,
        **metrics,
    )


def _sort_results(results: List[GateResult]) -> List[GateResult]:
    verdict_rank = {
        "RESEARCH_CANDIDATE": 6,
        "POSITIVE_BUT_NEEDS_REVIEW": 5,
        "POSITIVE_BUT_RISKY": 4,
        "SMALL_SAMPLE_POSITIVE": 3,
        "NEAR_BREAKEVEN_WATCH": 2,
        "REJECT_NEGATIVE_EDGE": 1,
        "REJECT_INSUFFICIENT_SAMPLE": 0,
        "REJECT_TOO_SMALL": -1,
        "NO_SAMPLES": -2,
    }
    return sorted(
        results,
        key=lambda r: (
            verdict_rank.get(r.verdict, 0),
            r.research_score,
            r.avg_return_pct,
            min(r.samples, 100),
        ),
        reverse=True,
    )


def _build_recommendations(results: List[GateResult], baseline: Dict, min_samples: int) -> Tuple[List[str], List[str]]:
    blockers: List[str] = []
    recs: List[str] = []
    baseline_avg = float(baseline.get("avg_return_pct", 0.0))
    baseline_samples = int(baseline.get("samples", 0))
    if baseline_samples < 100:
        blockers.append(f"نمونه‌های جهت‌دار Backtest کمتر از 100 است: {baseline_samples}")
    if baseline_avg <= 0:
        blockers.append("Baseline Backtest هنوز میانگین مثبت ندارد.")

    research = [r for r in results if r.verdict == "RESEARCH_CANDIDATE"]
    positives = [r for r in results if r.verdict in {"RESEARCH_CANDIDATE", "POSITIVE_BUT_NEEDS_REVIEW", "POSITIVE_BUT_RISKY"}]
    small_pos = [r for r in results if r.verdict == "SMALL_SAMPLE_POSITIVE"]
    near = [r for r in results if r.verdict == "NEAR_BREAKEVEN_WATCH"]

    if research:
        top = research[0]
        recs.append(f"بهترین gate تحقیقاتی با sample کافی: {top.gate} | avg={top.avg_return_pct}% | samples={top.samples} | verdict={top.verdict}.")
        recs.append("این gate هنوز فقط research candidate است؛ قبل از Paper واقعی باید در Forward/Paper آینده هم تأیید شود.")
    elif positives:
        top = positives[0]
        recs.append(f"gate مثبت با sample کافی اما نیازمند بررسی: {top.gate} | avg={top.avg_return_pct}% | samples={top.samples} | verdict={top.verdict}.")
        recs.append("قبل از فعال‌سازی به‌عنوان گیت عملی، دلیل ریسک Target/Stop یا win-rate را بررسی کن.")
    elif small_pos:
        top = small_pos[0]
        recs.append(f"فقط candidateهای مثبت کم‌نمونه پیدا شد؛ بهترین: {top.gate} | avg={top.avg_return_pct}% | samples={top.samples}.")
        recs.append(f"این gate باید تا حداقل {min_samples} sample در Backtest/Forward گسترش داده شود؛ فعلاً Paper جدی مجاز نیست.")
    elif near:
        top = near[0]
        recs.append(f"هیچ gate مثبت کافی پیدا نشد؛ نزدیک‌ترین حالت: {top.gate} با avg={top.avg_return_pct}% و samples={top.samples}.")
        recs.append("تمرکز بعدی باید روی اصلاح خروج، stop/target و entry timing باشد، نه زیاد کردن معاملات.")
    else:
        recs.append("هیچ gate قابل دفاع تاریخی پیدا نشد؛ موتور ورود باید قبل از Paper/Live سخت‌تر یا بازطراحی شود.")

    # Specific caution for high-score and actionable if they are weak.
    actionable = next((r for r in results if r.gate == "ACTIONABLE_ONLY"), None)
    score80 = next((r for r in results if r.gate == "SCORE_GE_80"), None)
    if actionable and actionable.avg_return_pct <= 0:
        recs.append(f"ACTIONABLE فعلی هنوز مثبت نیست: avg={actionable.avg_return_pct}%، stop={actionable.stop_hit_rate}%. گیت actionability باید سخت‌تر شود.")
    if score80 and score80.samples > 0:
        recs.append(f"score>=80 را جدا نگه دار: samples={score80.samples}, avg={score80.avg_return_pct}%. اگر sample کم است، فقط research watchlist باشد.")

    return blockers, recs


def run_gate_simulation(
    path: Path = BACKTEST_EVALUATIONS_FILE,
    *,
    horizon: str = "24h",
    min_samples: int = 30,
    include_zero_sample: bool = False,
) -> GateSimulationReport:
    horizon = str(horizon).lower().replace(" ", "")
    if horizon not in RETURN_COLUMNS:
        horizon = "24h"
    run_id = make_run_id()
    raw = _read_backtest_rows(path)
    df = _prepare_df(raw)
    if df.empty:
        return GateSimulationReport(
            run_id=run_id,
            generated_utc=utc_now_iso(),
            status="NO_BACKTEST_DATA",
            horizon=horizon,
            min_samples=min_samples,
            total_rows=0,
            complete_rows=0,
            directional_samples=0,
            baseline_avg_return_pct=0.0,
            baseline_win_rate=0.0,
            baseline_target_1_hit_rate=0.0,
            baseline_stop_hit_rate=0.0,
            gates_tested=0,
            positive_gates=0,
            research_candidates=0,
            small_sample_positive_gates=0,
            top_gates=[],
            results=[],
            blockers=["هیچ فایل historical_backtest_evaluations.csv پیدا نشد."],
            recommendations=["اول historical_backtest_dashboard.py را اجرا کن، سپس gate simulator را اجرا کن."],
            warnings=["این ابزار فقط research است و هیچ معامله‌ای ثبت نمی‌کند."],
        )

    complete = df[df["evaluation_status"].astype(str).str.upper() == "COMPLETE"].copy()
    directional = _directional_complete(df)
    total_directional = int(len(directional))
    specs = build_gate_specs(directional)
    results = [simulate_gate(spec, directional, horizon=horizon, min_samples=min_samples, total_directional=total_directional) for spec in specs]
    if not include_zero_sample:
        results = [r for r in results if r.samples > 0]
    results = _sort_results(results)
    baseline_metrics = _metrics(directional, horizon=horizon, total_directional=total_directional, min_samples=min_samples)
    blockers, recs = _build_recommendations(results, baseline_metrics, min_samples=min_samples)
    warnings = [
        "Gate Simulator فقط فیلترهای live-known را تست می‌کند؛ target/stop/return/MFE/MAE برای فیلتر استفاده نشده‌اند.",
        "BACKTEST جای FORWARD_TEST و Paper واقعی را نمی‌گیرد؛ candidateها فقط برای تحقیق هستند.",
        "subsetهای کم‌نمونه می‌توانند overfit باشند؛ sample حداقل و تأیید forward لازم است.",
    ]
    research_candidates = sum(1 for r in results if r.verdict == "RESEARCH_CANDIDATE")
    positive_gates = sum(1 for r in results if r.avg_return_pct > 0 and r.samples >= min_samples)
    small_sample_positive = sum(1 for r in results if r.verdict == "SMALL_SAMPLE_POSITIVE")
    status = "GATE_RESEARCH_CANDIDATES_FOUND" if research_candidates else "GATE_RESEARCH_ONLY"
    if total_directional < 30:
        status = "GATE_SIM_BUILDING"

    return GateSimulationReport(
        run_id=run_id,
        generated_utc=utc_now_iso(),
        status=status,
        horizon=horizon,
        min_samples=min_samples,
        total_rows=int(len(df)),
        complete_rows=int(len(complete)),
        directional_samples=total_directional,
        baseline_avg_return_pct=float(baseline_metrics.get("avg_return_pct", 0.0)),
        baseline_win_rate=float(baseline_metrics.get("win_rate", 0.0)),
        baseline_target_1_hit_rate=float(baseline_metrics.get("target_1_hit_rate", 0.0)),
        baseline_stop_hit_rate=float(baseline_metrics.get("stop_hit_rate", 0.0)),
        gates_tested=int(len(results)),
        positive_gates=int(positive_gates),
        research_candidates=int(research_candidates),
        small_sample_positive_gates=int(small_sample_positive),
        top_gates=[asdict(r) for r in results[:20]],
        results=[asdict(r) for r in results],
        blockers=blockers,
        recommendations=recs,
        warnings=warnings,
    )


def _fmt_gate(row: Dict) -> str:
    warnings = row.get("warnings") or []
    warn = f" | warn={'; '.join(warnings[:1])}" if warnings else ""
    return (
        f"- {row.get('gate')} [{row.get('verdict')}]: samples={row.get('samples')} | "
        f"avg={row.get('avg_return_pct')}% | win={row.get('win_rate')}% | "
        f"T1={row.get('target_1_hit_rate')}% | Stop={row.get('stop_hit_rate')}% | "
        f"MFE/MAE={row.get('mfe_mae_ratio')} | score={row.get('research_score')}{warn}"
    )


def _section_rows(results: List[Dict], predicate, limit: int) -> List[Dict]:
    return [row for row in results if predicate(row)][:limit]


def format_gate_simulation_console(report: GateSimulationReport, *, detail: bool = True, top: int = 12) -> str:
    lines: List[str] = []
    lines.append("=" * 110)
    lines.append("🧪 Freakto Backtest Gate Simulator v5.3.2")
    lines.append("=" * 110)
    lines.append(f"Status                 : {report.status}")
    lines.append(f"Run ID                 : {report.run_id}")
    lines.append(f"Horizon                : {report.horizon}")
    lines.append(f"Min Samples            : {report.min_samples}")
    lines.append(f"Rows / Complete        : {report.total_rows} / {report.complete_rows}")
    lines.append(f"Directional Samples    : {report.directional_samples}")
    lines.append(f"Baseline Avg Return    : {report.baseline_avg_return_pct:.4f}%")
    lines.append(f"Baseline Win Rate      : {report.baseline_win_rate:.2f}%")
    lines.append(f"Baseline T1 / Stop     : {report.baseline_target_1_hit_rate:.2f}% / {report.baseline_stop_hit_rate:.2f}%")
    lines.append(f"Gates Tested           : {report.gates_tested}")
    lines.append(f"Positive Gates         : {report.positive_gates}")
    lines.append(f"Research Candidates    : {report.research_candidates}")
    lines.append(f"Small Positive Gates   : {report.small_sample_positive_gates}")

    if report.top_gates:
        lines.append("")
        lines.append("Top Gates:")
        for row in report.top_gates[:top]:
            lines.append(_fmt_gate(row))

    research = _section_rows(report.results, lambda r: r.get("verdict") == "RESEARCH_CANDIDATE", top)
    if research:
        lines.append("")
        lines.append("Research Candidates:")
        for row in research:
            lines.append(_fmt_gate(row))

    small_pos = _section_rows(report.results, lambda r: r.get("verdict") == "SMALL_SAMPLE_POSITIVE", top)
    if small_pos:
        lines.append("")
        lines.append("Small-Sample Positive Gates:")
        for row in small_pos:
            lines.append(_fmt_gate(row))

    if detail:
        by_family: Dict[str, List[Dict]] = {}
        for row in report.results:
            by_family.setdefault(str(row.get("family", "unknown")), []).append(row)
        for family in sorted(by_family.keys()):
            rows = by_family[family]
            if not rows:
                continue
            lines.append("")
            lines.append(f"Family: {family}")
            for row in rows[:8]:
                lines.append(_fmt_gate(row))

    if report.blockers:
        lines.append("")
        lines.append("Research Blockers:")
        for blocker in report.blockers:
            lines.append(f"⛔ {blocker}")

    if report.recommendations:
        lines.append("")
        lines.append("Gate Recommendations:")
        for rec in report.recommendations:
            lines.append(f"→ {rec}")

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in report.warnings:
            lines.append(f"⚠️ {warning}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_gate_simulation_report(report: GateSimulationReport) -> str:
    lines: List[str] = []
    lines.append("# Freakto Backtest Gate Simulator v5.3.2")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Status: `{report.status}`")
    lines.append(f"- Generated UTC: `{report.generated_utc}`")
    lines.append(f"- Horizon: `{report.horizon}`")
    lines.append(f"- Min Samples: `{report.min_samples}`")
    lines.append(f"- Rows / Complete: `{report.total_rows}/{report.complete_rows}`")
    lines.append(f"- Directional Samples: `{report.directional_samples}`")
    lines.append(f"- Baseline Avg Return: `{report.baseline_avg_return_pct:.4f}%`")
    lines.append(f"- Baseline Win Rate: `{report.baseline_win_rate:.2f}%`")
    lines.append(f"- Baseline T1 / Stop: `{report.baseline_target_1_hit_rate:.2f}% / {report.baseline_stop_hit_rate:.2f}%`")
    lines.append(f"- Gates Tested: `{report.gates_tested}`")
    lines.append(f"- Positive Gates: `{report.positive_gates}`")
    lines.append(f"- Research Candidates: `{report.research_candidates}`")
    lines.append(f"- Small Positive Gates: `{report.small_sample_positive_gates}`")
    lines.append("")

    lines.append("## Top Gates")
    lines.append("| Gate | Verdict | Family | Samples | Avg | Win | T1 | Stop | MFE/MAE | Research Score |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in report.top_gates[:30]:
        lines.append(
            f"| {row.get('gate')} | {row.get('verdict')} | {row.get('family')} | {row.get('samples')} | "
            f"{row.get('avg_return_pct')}% | {row.get('win_rate')}% | {row.get('target_1_hit_rate')}% | "
            f"{row.get('stop_hit_rate')}% | {row.get('mfe_mae_ratio')} | {row.get('research_score')} |"
        )
    lines.append("")

    lines.append("## All Gate Results")
    lines.append("| Gate | Verdict | Family | Samples | Share | Avg | Median | Best | Worst | Win | T1 | Stop | MFE | MAE | MFE/MAE | Description |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in report.results:
        lines.append(
            f"| {row.get('gate')} | {row.get('verdict')} | {row.get('family')} | {row.get('samples')} | "
            f"{row.get('sample_share_pct')}% | {row.get('avg_return_pct')}% | {row.get('median_return_pct')}% | "
            f"{row.get('best_return_pct')}% | {row.get('worst_return_pct')}% | {row.get('win_rate')}% | "
            f"{row.get('target_1_hit_rate')}% | {row.get('stop_hit_rate')}% | {row.get('mfe_mean_pct')}% | "
            f"{row.get('mae_mean_pct')}% | {row.get('mfe_mae_ratio')} | {row.get('description')} |"
        )
    lines.append("")

    lines.append("## Research Blockers")
    if report.blockers:
        for item in report.blockers:
            lines.append(f"- {item}")
    else:
        lines.append("- No major gate simulation blockers.")
    lines.append("")

    lines.append("## Recommendations")
    for item in report.recommendations:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Safety Notes")
    for item in report.warnings:
        lines.append(f"- {item}")
    return "\n".join(lines)


def _write_results_csv(path: Path, results: List[Dict]) -> None:
    if not results:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(results[0].keys())
    # flatten lists/dicts for CSV readability
    rows = []
    for row in results:
        out = {}
        for key, value in row.items():
            if isinstance(value, (list, dict)):
                out[key] = json.dumps(value, ensure_ascii=False)
            else:
                out[key] = value
        rows.append(out)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_gate_simulation(report: GateSimulationReport) -> Tuple[Path, Path, Path]:
    GATE_SIM_DIR.mkdir(parents=True, exist_ok=True)
    json_path = GATE_SIM_DIR / f"gate_simulation_{report.run_id}.json"
    report_path = GATE_SIM_DIR / f"gate_simulation_report_{report.run_id}.md"
    csv_path = GATE_SIM_DIR / f"gate_simulation_results_{report.run_id}.csv"
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(format_gate_simulation_report(report), encoding="utf-8")
    _write_results_csv(csv_path, report.results)
    return json_path, report_path, csv_path
