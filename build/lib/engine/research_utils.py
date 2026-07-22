"""
Freakto v6.0.0 - Research Utility Layer

Small, dependency-light helpers used by the v6 research/robustness suite.
All functions are research-only and never place trades.
"""
from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from engine.csv_utils import read_csv_dicts_lenient

LOG_DIR = Path("logs")
RESEARCH_DIR = LOG_DIR / "research"
BACKTEST_EVALS = LOG_DIR / "historical_backtest_evaluations.csv"
FORWARD_EVALS = LOG_DIR / "decision_evaluations.csv"
DECISIONS = LOG_DIR / "decisions.csv"
FORWARD_RUNS = LOG_DIR / "forward_test_runs.csv"
SHADOW_SIGNALS = LOG_DIR / "shadow_gates" / "shadow_gate_signals.csv"
AIRDROP_WATCHLIST = Path("data") / "airdrop_watchlist.json"

RETURN_COLUMNS = {
    "4h": "return_after_4h_pct",
    "12h": "return_after_12h_pct",
    "24h": "return_after_24h_pct",
}
OUTCOME_COLUMNS = set(RETURN_COLUMNS.values()) | {"target_1_hit", "target_2_hit", "target_3_hit", "stop_hit", "mfe_pct", "mae_pct"}
LIVE_KNOWN_COLUMNS = [
    "symbol", "side", "score", "actionability", "confidence_label", "risk_label", "regime_label",
    "trend_score", "momentum_score", "volume_score", "structure_score", "historical_edge_score",
    "long_score", "short_score", "is_actionable", "provider", "timeframe", "candle_timestamp",
]
NUMERIC_COLUMNS = [
    "score", "trend_score", "momentum_score", "volume_score", "structure_score", "historical_edge_score",
    "long_score", "short_score", "mfe_pct", "mae_pct", *RETURN_COLUMNS.values(),
]
DIRECTIONAL_SIDES = {"LONG", "SHORT"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_id(prefix: str) -> str:
    return prefix + "_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def pct(n: int, d: int) -> float:
    return round(n / d * 100, 2) if d else 0.0


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        text = str(value).replace(",", "").strip()
        if not text or text.lower() in {"nan", "none", "null", "نامشخص"}:
            return default
        val = float(text)
        if math.isnan(val):
            return default
        return val
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    val = safe_float(value, None)
    return default if val is None else int(val)


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def read_csv_df(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        _, rows = read_csv_dicts_lenient(path)
        return pd.DataFrame(rows)


def write_json(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path


def write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def normalize_text_series(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip()


def prepare_eval_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    w = df.copy()
    for col in NUMERIC_COLUMNS:
        if col in w.columns:
            w[col] = pd.to_numeric(w[col], errors="coerce")
    defaults = {
        "source": "UNKNOWN",
        "evaluation_status": "",
        "symbol": "UNKNOWN",
        "timeframe": "",
        "provider": "UNKNOWN",
        "side": "NEUTRAL",
        "actionability": "",
        "confidence_label": "",
        "risk_label": "",
        "regime_label": "UNKNOWN",
        "candle_timestamp": "",
        "decision_id": "",
    }
    for col, default in defaults.items():
        if col not in w.columns:
            w[col] = default
        w[col] = normalize_text_series(w[col])
    for col in ["target_1_hit", "target_2_hit", "target_3_hit", "stop_hit", "is_actionable"]:
        if col in w.columns:
            # leave as mixed but provide normalized bool columns where needed
            pass
    return w


def load_backtest_df() -> pd.DataFrame:
    return prepare_eval_df(read_csv_df(BACKTEST_EVALS))


def load_forward_eval_df() -> pd.DataFrame:
    return prepare_eval_df(read_csv_df(FORWARD_EVALS))


def load_decisions_df() -> pd.DataFrame:
    df = read_csv_df(DECISIONS)
    if df.empty:
        return df
    return prepare_eval_df(df)


def directional_complete(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    w = prepare_eval_df(df)
    if "evaluation_status" in w.columns:
        w = w[w["evaluation_status"].astype(str).str.upper() == "COMPLETE"].copy()
    return w[w["side"].astype(str).str.upper().isin(DIRECTIONAL_SIDES)].copy()


def add_cost_columns(df: pd.DataFrame, horizon: str = "24h", fee_bps: float = 10.0, slippage_bps: float = 5.0) -> pd.DataFrame:
    w = df.copy()
    col = RETURN_COLUMNS.get(horizon, horizon)
    if col not in w.columns:
        w[col] = np.nan
    gross = pd.to_numeric(w[col], errors="coerce")
    total_cost_pct = (float(fee_bps) + float(slippage_bps)) / 100.0
    w["gross_return_pct"] = gross
    w["fee_bps"] = float(fee_bps)
    w["slippage_bps"] = float(slippage_bps)
    w["estimated_cost_pct"] = total_cost_pct
    w["net_return_pct"] = gross - total_cost_pct
    return w


def metric_summary(df: pd.DataFrame, horizon: str = "24h", use_net: bool = False, fee_bps: float = 10.0, slippage_bps: float = 5.0) -> Dict[str, Any]:
    if df is None or df.empty:
        return {
            "samples": 0,
            "avg_return_pct": 0.0,
            "median_return_pct": 0.0,
            "win_rate": 0.0,
            "target_1_hit_rate": 0.0,
            "stop_hit_rate": 0.0,
            "mfe_mean_pct": 0.0,
            "mae_mean_pct": 0.0,
            "mfe_mae_ratio": 0.0,
            "best_return_pct": 0.0,
            "worst_return_pct": 0.0,
            "std_return_pct": 0.0,
            "t_stat": 0.0,
            "confidence_95_low_pct": 0.0,
            "confidence_95_high_pct": 0.0,
        }
    w = add_cost_columns(df, horizon=horizon, fee_bps=fee_bps, slippage_bps=slippage_bps) if use_net else df.copy()
    col = "net_return_pct" if use_net else RETURN_COLUMNS.get(horizon, horizon)
    returns = pd.to_numeric(w.get(col, pd.Series(dtype=float)), errors="coerce").dropna()
    n = int(len(returns))
    if not n:
        return metric_summary(pd.DataFrame(), horizon=horizon)
    target = bool_series(w.get("target_1_hit", pd.Series([False] * len(w)))) if "target_1_hit" in w.columns else pd.Series([False] * len(w))
    stop = bool_series(w.get("stop_hit", pd.Series([False] * len(w)))) if "stop_hit" in w.columns else pd.Series([False] * len(w))
    mfe = pd.to_numeric(w.get("mfe_pct", pd.Series(dtype=float)), errors="coerce")
    mae = pd.to_numeric(w.get("mae_pct", pd.Series(dtype=float)), errors="coerce")
    std = float(returns.std(ddof=1)) if n > 1 else 0.0
    mean = float(returns.mean())
    se = std / math.sqrt(n) if n > 1 and std > 0 else 0.0
    t = mean / se if se else 0.0
    ci_low = mean - 1.96 * se if se else mean
    ci_high = mean + 1.96 * se if se else mean
    mfe_mean = float(mfe.mean()) if len(mfe.dropna()) else 0.0
    mae_mean = float(mae.mean()) if len(mae.dropna()) else 0.0
    ratio = abs(mfe_mean / mae_mean) if mae_mean else 0.0
    return {
        "samples": n,
        "avg_return_pct": round(mean, 4),
        "median_return_pct": round(float(returns.median()), 4),
        "win_rate": round(float((returns > 0).mean() * 100), 2),
        "target_1_hit_rate": pct(int(target.sum()), len(w)),
        "stop_hit_rate": pct(int(stop.sum()), len(w)),
        "mfe_mean_pct": round(mfe_mean, 4),
        "mae_mean_pct": round(mae_mean, 4),
        "mfe_mae_ratio": round(ratio, 3),
        "best_return_pct": round(float(returns.max()), 4),
        "worst_return_pct": round(float(returns.min()), 4),
        "std_return_pct": round(std, 4),
        "t_stat": round(t, 4),
        "confidence_95_low_pct": round(ci_low, 4),
        "confidence_95_high_pct": round(ci_high, 4),
    }


def apply_gate(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    mask = pd.Series([True] * len(df), index=df.index)
    for key, value in (filters or {}).items():
        if key.endswith("__ge"):
            col = key[:-4]
            if col not in df.columns:
                mask &= False
            else:
                mask &= pd.to_numeric(df[col], errors="coerce").fillna(-10**9) >= float(value)
        elif key.endswith("__le"):
            col = key[:-4]
            if col not in df.columns:
                mask &= False
            else:
                mask &= pd.to_numeric(df[col], errors="coerce").fillna(10**9) <= float(value)
        elif key.endswith("__in"):
            col = key[:-4]
            values = {str(v).upper() for v in (value if isinstance(value, list) else [value])}
            if col not in df.columns:
                mask &= False
            else:
                mask &= df[col].astype(str).str.upper().isin(values)
        else:
            if key not in df.columns:
                mask &= False
            else:
                mask &= df[key].astype(str).str.upper() == str(value).upper()
    return df[mask].copy()


def standard_gate_specs() -> List[Dict[str, Any]]:
    """Live-known gate specs used consistently across v6 modules."""
    specs = [
        {"name": "ACTIONABLE", "family": "actionability", "filters": {"actionability": "ACTIONABLE"}},
        {"name": "WATCHLIST", "family": "actionability", "filters": {"actionability": "WATCHLIST"}},
        {"name": "VOLUME_SCORE_GE_10", "family": "component", "filters": {"volume_score__ge": 10}},
        {"name": "RISK_MEDIUM", "family": "risk", "filters": {"risk_label": "Medium"}},
        {"name": "HISTORICAL_EDGE_SCORE_GE_1", "family": "component", "filters": {"historical_edge_score__ge": 1}},
        {"name": "STRUCTURE_SCORE_GE_10", "family": "component", "filters": {"structure_score__ge": 10}},
        {"name": "SCORE_GE_80", "family": "score", "filters": {"score__ge": 80}},
        {"name": "SCORE_GE_70", "family": "score", "filters": {"score__ge": 70}},
        {"name": "SCORE_60_69", "family": "score_bucket", "filters": {"score__ge": 60, "score__le": 69}},
        {"name": "LONG_ONLY", "family": "side", "filters": {"side": "LONG"}},
        {"name": "SHORT_ONLY", "family": "side", "filters": {"side": "SHORT"}},
        {"name": "DOGE_SHORT_WATCH", "family": "symbol_side", "filters": {"symbol": "DOGE/USDT", "side": "SHORT"}},
        {"name": "BNB_LONG_SCORE_GE_60", "family": "symbol_side_score", "filters": {"symbol": "BNB/USDT", "side": "LONG", "score__ge": 60}},
        {"name": "XRP_SHORT_SCORE_GE_60", "family": "symbol_side_score", "filters": {"symbol": "XRP/USDT", "side": "SHORT", "score__ge": 60}},
        {"name": "ACTIONABLE_SCORE_GE_80", "family": "quality", "filters": {"actionability": "ACTIONABLE", "score__ge": 80}},
        {"name": "QUALITY_VOLUME_HEDGE", "family": "quality", "filters": {"volume_score__ge": 10, "historical_edge_score__ge": 1}},
        {"name": "QUALITY_STRUCTURE_RISK_MEDIUM", "family": "quality", "filters": {"structure_score__ge": 10, "risk_label": "Medium"}},
    ]
    return specs


def time_ordered(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    w = df.copy()
    if "candle_timestamp" in w.columns:
        w["_dt"] = pd.to_datetime(w["candle_timestamp"], errors="coerce", utc=True)
    else:
        w["_dt"] = pd.NaT
    return w.sort_values(["_dt", "symbol"], na_position="last").reset_index(drop=True)


def split_time_windows(df: pd.DataFrame, n_windows: int = 5) -> List[pd.DataFrame]:
    w = time_ordered(df)
    if w.empty:
        return []
    n_windows = max(1, min(int(n_windows), len(w)))
    indices = np.array_split(np.arange(len(w)), n_windows)
    return [w.iloc[idx].copy().reset_index(drop=True) for idx in indices if len(idx) > 0]


def compact_table(rows: Sequence[Dict[str, Any]], columns: Sequence[str], max_rows: int = 10) -> str:
    if not rows:
        return "- هیچ داده‌ای موجود نیست."
    lines = []
    for row in list(rows)[:max_rows]:
        parts = [f"{col}={row.get(col, '')}" for col in columns]
        lines.append("- " + " | ".join(parts))
    return "\n".join(lines)


def save_dataframe_csv(path: Path, df: pd.DataFrame) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path
