"""
Freakto v10.0 - Market Replay Engine

Candle-by-candle historical replay for the current technical Decision Engine.
The engine intentionally disables persisted Historical Edge and Learning
Override inputs while replaying, because those files may contain information
created after the historical candle.

This is a research/backtest component only. It never creates Paper or Live
orders.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from engine.historical_data_store import (
    DEFAULT_DATA_DIR,
    OHLCV_COLUMNS,
    floor_datetime_to_timeframe,
    load_history,
    parse_utc,
    symbol_slug,
    timeframe_to_milliseconds,
    utc_now_iso,
)
from engine.execution_model import adaptive_horizon, estimate_execution_cost
from engine.experiment_registry import ExperimentRegistry, fingerprint
from engine.model_contract import CURRENT_MODEL_CONTRACT


VERSION = "v10.3.0"
REPLAY_DIR = Path("logs") / "market_replay"
CHECKPOINT_DIR = REPLAY_DIR / "checkpoints"
CUMULATIVE_REPLAY_FILE = REPLAY_DIR / "market_replay_evaluations.csv"
RUNS_FILE = REPLAY_DIR / "market_replay_runs.csv"
DEFAULT_HORIZONS = (1, 3, 6)
REQUIRED_FEATURE_COLUMNS = [
    "close",
    "sma_10",
    "sma_30",
    "ema_10",
    "rsi_14",
    "macd_diff",
    "atr_pct",
]
OPTIONAL_CONTEXT_COLUMNS = [
    "cross_exchange_volume",
    "cross_exchange_volume_ratio",
    "cross_exchange_provider_count",
    "news_sentiment_score",
    "news_sentiment_summary",
    "onchain_active_addresses",
    "onchain_signal_score",
    "onchain_status",
]


@dataclass
class MarketReplayConfig:
    symbols: List[str]
    timeframe: str = "4h"
    start_utc: str = ""
    end_utc: str = ""
    data_dir: str = str(DEFAULT_DATA_DIR)
    min_window: int = 120
    step: int = 1
    min_side_score: int = 50
    horizons: List[int] = field(default_factory=lambda: list(DEFAULT_HORIZONS))
    include_neutral: bool = True
    max_decisions_per_symbol: int = 0
    fee_bps_per_side: float = 10.0
    slippage_bps_per_side: float = 5.0
    dynamic_execution_costs: bool = True
    max_slippage_bps_per_side: float = 100.0
    execution_delay_candles: int = 1
    adaptive_evaluation_horizon: bool = True
    context_file: str = ""
    context_max_age_hours: float = 24.0
    checkpoint_every: int = 250
    strict_leakage_audit: bool = True
    source: str = "MARKET_REPLAY"


@dataclass
class LeakageAudit:
    status: str
    points_checked: int
    feature_values_checked: int
    mismatches: int
    max_abs_difference: float
    details: List[str] = field(default_factory=list)


@dataclass
class ReplaySymbolResult:
    symbol: str
    timeframe: str
    ok: bool
    provider: str = ""
    candles_loaded: int = 0
    candles_in_range: int = 0
    decisions_written: int = 0
    first_decision_utc: str = ""
    last_decision_utc: str = ""
    leakage_audit: Optional[LeakageAudit] = None
    error: str = ""


@dataclass
class ReplayMetricRow:
    key: str
    rows: int
    directional_rows: int
    complete_rows: int
    win_rate_24h_pct: float
    avg_gross_24h_pct: float
    avg_net_24h_pct: float
    median_net_24h_pct: float
    target_1_hit_rate_pct: float
    stop_hit_rate_pct: float
    profit_factor_24h: float
    max_drawdown_proxy_pct: float


@dataclass
class MarketReplaySummary:
    run_id: str
    version: str
    status: str
    mode: str
    symbols_requested: int
    symbols_completed: int
    total_candles: int
    total_rows: int
    complete_rows: int
    directional_rows: int
    actionable_rows: int
    neutral_rows: int
    win_rate_24h_pct: float
    avg_gross_24h_pct: float
    avg_net_24h_pct: float
    profit_factor_24h: float
    leakage_audit_status: str
    historical_context_mode: str
    evaluation_horizon_candles: int
    evaluation_horizon_label: str
    by_split: List[Dict[str, Any]]
    by_symbol: List[Dict[str, Any]]
    by_side: List[Dict[str, Any]]
    by_regime: List[Dict[str, Any]]
    by_year: List[Dict[str, Any]]
    blockers: List[str]
    warnings: List[str]


@dataclass
class MarketReplayRun:
    run_id: str
    version: str
    started_utc: str
    finished_utc: str = ""
    ok: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    symbol_results: List[ReplaySymbolResult] = field(default_factory=list)
    output_csv: str = ""
    output_json: str = ""
    output_report: str = ""
    checkpoint_path: str = ""
    error_count: int = 0


def make_run_id() -> str:
    return "market_replay_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        text = str(value).replace(",", "").strip()
        if not text or text.lower() in {"nan", "none", "null", "نامشخص", "---"}:
            return default
        return float(text)
    except Exception:
        return default


def _parse_price(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).replace("`", "").replace(",", "").strip()
    if not text or "نامشخص" in text:
        return None
    return _safe_float(text)


def _parse_zone_midpoint(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = str(value).replace("`", "").replace(",", "").strip()
    if not text or "نامشخص" in text:
        return None
    parts = text.split(" - ") if " - " in text else [text]
    values = [_safe_float(part) for part in parts]
    values = [item for item in values if item is not None]
    return sum(values) / len(values) if values else None


def _parse_targets(values: Iterable[Any]) -> List[float]:
    result: List[float] = []
    for value in values or []:
        parsed = _parse_price(value)
        if parsed is not None:
            result.append(parsed)
    return result


def _component_points(opportunity, name: str) -> int:
    for component in getattr(opportunity, "components", []) or []:
        if component.name == name:
            return int(component.points)
    return 0


def _config_fingerprint(config: MarketReplayConfig) -> str:
    context_digest = ""
    if config.context_file and Path(config.context_file).exists():
        try:
            context_digest = hashlib.sha256(Path(config.context_file).read_bytes()).hexdigest()[:16]
        except Exception:
            context_digest = str(config.context_file)
    payload = {
        "timeframe": config.timeframe,
        "start_utc": config.start_utc,
        "end_utc": config.end_utc,
        "min_window": config.min_window,
        "step": config.step,
        "min_side_score": config.min_side_score,
        "horizons": list(config.horizons),
        "include_neutral": config.include_neutral,
        "fee_bps_per_side": config.fee_bps_per_side,
        "slippage_bps_per_side": config.slippage_bps_per_side,
        "dynamic_execution_costs": config.dynamic_execution_costs,
        "max_slippage_bps_per_side": config.max_slippage_bps_per_side,
        "execution_delay_candles": config.execution_delay_candles,
        "adaptive_evaluation_horizon": config.adaptive_evaluation_horizon,
        **CURRENT_MODEL_CONTRACT.as_dict(),
        "context_digest": context_digest,
        "context_max_age_hours": config.context_max_age_hours,
        "replay_safety": "learning_off_historical_edge_off",
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _data_fingerprint(frame: pd.DataFrame, provider: str) -> str:
    if frame is None or frame.empty:
        return "no_data"
    columns = [column for column in OHLCV_COLUMNS if column in frame.columns]
    hashed = pd.util.hash_pandas_object(frame[columns], index=False).values.tobytes()
    digest = hashlib.sha256(hashed + str(provider).encode("utf-8")).hexdigest()
    return digest[:16]


def _stable_decision_id(
    symbol: str, timeframe: str, timestamp: Any, experiment_id: str
) -> str:
    raw = f"REPLAY|{experiment_id}|{symbol}|{timeframe}|{pd.Timestamp(timestamp).isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _context_file_frame(path: str) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    file_path = Path(path)
    if not file_path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(file_path, low_memory=False)
    timestamp_column = "timestamp_utc" if "timestamp_utc" in frame.columns else "timestamp" if "timestamp" in frame.columns else ""
    if not timestamp_column:
        raise ValueError("historical context file needs timestamp_utc or timestamp")
    frame["timestamp"] = pd.to_datetime(frame[timestamp_column], utc=True, errors="coerce")
    frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").drop_duplicates(
        subset=["timestamp", "symbol"] if "symbol" in frame.columns else ["timestamp"], keep="last"
    )
    return frame.reset_index(drop=True)


def attach_historical_context(
    market: pd.DataFrame,
    context: pd.DataFrame,
    *,
    symbol: str,
    max_age_hours: float,
) -> Tuple[pd.DataFrame, int]:
    work = market.copy().sort_values("timestamp")
    for column in OPTIONAL_CONTEXT_COLUMNS:
        if column not in work.columns:
            work[column] = "" if column.endswith("summary") or column.endswith("status") else 0.0
    if context is None or context.empty:
        return work, 0

    ctx = context.copy()
    if "symbol" in ctx.columns:
        exact = ctx[ctx["symbol"].astype(str).isin([symbol, "*", "ALL", "all"])].copy()
        ctx = exact
    if ctx.empty:
        return work, 0

    available = [column for column in OPTIONAL_CONTEXT_COLUMNS if column in ctx.columns]
    if not available:
        return work, 0

    ctx = ctx[["timestamp"] + available].sort_values("timestamp")
    merged = pd.merge_asof(
        work.sort_values("timestamp"),
        ctx,
        on="timestamp",
        direction="backward",
        suffixes=("", "_historical_context"),
        tolerance=pd.Timedelta(hours=max(0.0, max_age_hours)),
    )
    matched = 0
    for column in available:
        context_column = f"{column}_historical_context"
        if context_column in merged.columns:
            nonempty = merged[context_column].notna()
            matched = max(matched, int(nonempty.sum()))
            merged.loc[nonempty, column] = merged.loc[nonempty, context_column]
            merged = merged.drop(columns=[context_column])
    return merged, matched


def _prepare_market_frame(raw: pd.DataFrame, *, symbol: str, config: MarketReplayConfig) -> Tuple[pd.DataFrame, str, int]:
    if raw is None or raw.empty:
        return pd.DataFrame(), "", 0
    work = raw.copy()
    work["timestamp"] = pd.to_datetime(work["timestamp"], utc=True, errors="coerce")
    work = work.dropna(subset=OHLCV_COLUMNS).sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    provider = str(work["provider"].dropna().iloc[-1]) if "provider" in work.columns and len(work) else "unknown"

    if config.start_utc:
        start = floor_datetime_to_timeframe(parse_utc(config.start_utc), config.timeframe)
        work = work[work["timestamp"] >= pd.Timestamp(start)]
    if config.end_utc:
        end = floor_datetime_to_timeframe(parse_utc(config.end_utc), config.timeframe)
        work = work[work["timestamp"] <= pd.Timestamp(end)]

    context = _context_file_frame(config.context_file)
    work, context_matches = attach_historical_context(
        work,
        context,
        symbol=symbol,
        max_age_hours=config.context_max_age_hours,
    )
    work = work.reset_index(drop=True)
    return work, provider, context_matches


def audit_causal_features(raw: pd.DataFrame, featured: pd.DataFrame, min_window: int) -> LeakageAudit:
    """Recompute selected windows and compare their latest feature values.

    `features.add_features` currently uses only trailing/causal indicators. This
    audit protects future refactors from silently adding a centered rolling
    window or negative shift.
    """
    from features import add_features

    if raw.empty or featured.empty:
        return LeakageAudit("FAILED_NO_DATA", 0, 0, 0, 0.0, ["No data to audit."])

    candidates = sorted(set([
        min(max(min_window, 40), len(raw) - 1),
        max(min_window, len(raw) // 2),
        len(raw) - 1,
    ]))
    mismatches = 0
    checked = 0
    max_difference = 0.0
    details: List[str] = []

    for idx in candidates:
        if idx < 1 or idx >= len(raw):
            continue
        partial = add_features(raw.iloc[: idx + 1].copy())
        for column in REQUIRED_FEATURE_COLUMNS:
            if column not in partial.columns or column not in featured.columns:
                continue
            left = _safe_float(partial.iloc[-1].get(column))
            right = _safe_float(featured.iloc[idx].get(column))
            if left is None and right is None:
                continue
            checked += 1
            if left is None or right is None:
                mismatches += 1
                details.append(f"idx={idx} {column}: one side is missing")
                continue
            difference = abs(left - right)
            max_difference = max(max_difference, difference)
            tolerance = max(1e-10, abs(right) * 1e-9)
            if difference > tolerance:
                mismatches += 1
                details.append(f"idx={idx} {column}: partial={left} full={right} diff={difference}")

    status = "PASSED_NO_LOOKAHEAD" if mismatches == 0 and checked else "FAILED_FEATURE_MISMATCH"
    return LeakageAudit(
        status=status,
        points_checked=len(candidates),
        feature_values_checked=checked,
        mismatches=mismatches,
        max_abs_difference=float(max_difference),
        details=details[:20],
    )


def _evaluate_replay_path(
    full_df: pd.DataFrame,
    *,
    signal_idx: int,
    side: str,
    entry_price: float,
    stop_price: Optional[float],
    targets: Sequence[float],
    horizons: Sequence[int],
    fee_bps_per_side: float,
    slippage_bps_per_side: float,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "available_future_candles": max(0, len(full_df) - signal_idx - 1),
        "evaluation_status": "PARTIAL",
        "target_1_hit": False,
        "target_2_hit": False,
        "target_3_hit": False,
        "stop_hit": False,
        "first_exit_reason": "NO_EXIT",
        "first_exit_candle_offset": None,
        "intrabar_ambiguity": False,
        "mfe_pct": None,
        "mae_pct": None,
    }
    horizons = sorted(set(int(value) for value in horizons if int(value) > 0))
    if not horizons:
        return result
    max_horizon = max(horizons)
    future = full_df.iloc[signal_idx + 1 : signal_idx + max_horizon + 1].copy()
    result["evaluated_candles"] = len(future)
    cost_pct = 2.0 * (float(fee_bps_per_side) + float(slippage_bps_per_side)) / 100.0
    completed = 0

    for horizon in horizons:
        raw_column = f"market_return_after_{horizon}c_pct"
        signed_column = f"gross_signed_return_after_{horizon}c_pct"
        net_column = f"net_signed_return_after_{horizon}c_pct"
        correct_column = f"direction_correct_after_{horizon}c"
        if signal_idx + horizon < len(full_df):
            future_close = float(full_df.iloc[signal_idx + horizon]["close"])
            raw_return = ((future_close - entry_price) / entry_price) * 100.0
            signed = raw_return if side == "LONG" else -raw_return if side == "SHORT" else 0.0
            net = signed - cost_pct if side in {"LONG", "SHORT"} else 0.0
            result[raw_column] = round(raw_return, 6)
            result[signed_column] = round(signed, 6) if side in {"LONG", "SHORT"} else None
            result[net_column] = round(net, 6) if side in {"LONG", "SHORT"} else None
            result[correct_column] = bool(signed > 0) if side in {"LONG", "SHORT"} else None
            completed += 1
        else:
            result[raw_column] = None
            result[signed_column] = None
            result[net_column] = None
            result[correct_column] = None

    if completed == len(horizons):
        result["evaluation_status"] = "COMPLETE"
    if future.empty:
        return result

    highs = future["high"].astype(float)
    lows = future["low"].astype(float)
    if side == "LONG":
        result["mfe_pct"] = round(((highs.max() - entry_price) / entry_price) * 100.0, 6)
        result["mae_pct"] = round(((lows.min() - entry_price) / entry_price) * 100.0, 6)
    elif side == "SHORT":
        result["mfe_pct"] = round(((entry_price - lows.min()) / entry_price) * 100.0, 6)
        result["mae_pct"] = round(((entry_price - highs.max()) / entry_price) * 100.0, 6)
    else:
        result["mfe_pct"] = round(((highs.max() - entry_price) / entry_price) * 100.0, 6)
        result["mae_pct"] = round(((lows.min() - entry_price) / entry_price) * 100.0, 6)
        return result

    target_hit_flags = [False, False, False]
    stop_ever_hit = False
    first_exit_set = False
    for offset, (_, candle) in enumerate(future.iterrows(), start=1):
        high = float(candle["high"])
        low = float(candle["low"])
        if side == "LONG":
            current_target_hits = [high >= target for target in targets[:3]]
            current_stop = stop_price is not None and low <= stop_price
        else:
            current_target_hits = [low <= target for target in targets[:3]]
            current_stop = stop_price is not None and high >= stop_price

        for idx, hit in enumerate(current_target_hits):
            if idx < 3 and hit:
                target_hit_flags[idx] = True
        if current_stop:
            stop_ever_hit = True

        if not first_exit_set:
            t1_this_candle = bool(current_target_hits[0]) if current_target_hits else False
            if current_stop and t1_this_candle:
                # OHLC does not reveal intrabar order. Conservative research
                # accounting treats the stop as first and records ambiguity.
                result["first_exit_reason"] = "STOP_FIRST_CONSERVATIVE_AMBIGUOUS"
                result["intrabar_ambiguity"] = True
                result["first_exit_candle_offset"] = offset
                first_exit_set = True
            elif current_stop:
                result["first_exit_reason"] = "STOP"
                result["first_exit_candle_offset"] = offset
                first_exit_set = True
            elif t1_this_candle:
                result["first_exit_reason"] = "TARGET_1"
                result["first_exit_candle_offset"] = offset
                first_exit_set = True

    result["target_1_hit"] = target_hit_flags[0]
    result["target_2_hit"] = target_hit_flags[1]
    result["target_3_hit"] = target_hit_flags[2]
    result["stop_hit"] = stop_ever_hit

    # Compatibility aliases for Freakto's standard 4h research tables.
    if str(getattr(full_df, "attrs", {}).get("timeframe", "")) == "4h":
        aliases = {1: "4h", 3: "12h", 6: "24h"}
        for horizon, label in aliases.items():
            if horizon not in horizons:
                continue
            result[f"market_return_after_{label}_pct"] = result.get(f"market_return_after_{horizon}c_pct")
            result[f"return_after_{label}_pct"] = result.get(f"gross_signed_return_after_{horizon}c_pct")
            result[f"net_return_after_{label}_pct"] = result.get(f"net_signed_return_after_{horizon}c_pct")

    return result


def _chronological_split(position: int, total: int) -> str:
    if total <= 0:
        return "UNKNOWN"
    ratio = (position + 1) / total
    if ratio <= 0.60:
        return "TRAIN_60"
    if ratio <= 0.80:
        return "VALIDATION_20"
    return "TEST_20"


def _row_from_opportunity(
    *,
    run_id: str,
    config: MarketReplayConfig,
    provider: str,
    symbol: str,
    signal_idx: int,
    replay_position: int,
    replay_total: int,
    full_df: pd.DataFrame,
    opportunity,
    context_mode: str,
    experiment_id: str,
    data_fingerprint: str,
) -> Dict[str, Any]:
    timestamp = full_df.iloc[signal_idx]["timestamp"]
    delay = max(1, int(config.execution_delay_candles))
    entry_idx = signal_idx + delay
    if entry_idx >= len(full_df):
        raise ValueError("no execution candle is available after the decision")
    # The decision is made after signal candle close.  A paper/replay fill is
    # therefore based on the next available candle open, never that same close.
    entry_price = float(full_df.iloc[entry_idx]["open"])
    side = str(opportunity.side)
    stop_price = _parse_price(opportunity.stop_zone)
    targets = _parse_targets(opportunity.targets)
    raw = getattr(opportunity, "raw", {}) or {}
    primary_horizon = max([int(value) for value in config.horizons if int(value) > 0] or [6])
    regime_label = str(raw.get("regime_label", ""))
    adaptive_primary = adaptive_horizon(primary_horizon, regime_label) if config.adaptive_evaluation_horizon else primary_horizon
    evaluation_horizons = sorted(set([*config.horizons, adaptive_primary]))
    cost = estimate_execution_cost(
        full_df.iloc[signal_idx],
        fee_bps_per_side=config.fee_bps_per_side,
        base_slippage_bps_per_side=config.slippage_bps_per_side,
        dynamic=config.dynamic_execution_costs,
        max_slippage_bps_per_side=config.max_slippage_bps_per_side,
    )
    path = _evaluate_replay_path(
        full_df,
        signal_idx=entry_idx - 1,
        side=side,
        entry_price=entry_price,
        stop_price=stop_price,
        targets=targets,
        horizons=evaluation_horizons,
        fee_bps_per_side=cost.fee_bps_per_side,
        slippage_bps_per_side=cost.slippage_bps_per_side,
    )
    row: Dict[str, Any] = {
        "source": config.source,
        "run_id": run_id,
        "decision_id": _stable_decision_id(symbol, config.timeframe, timestamp, experiment_id),
        "replay_experiment_id": experiment_id,
        "replay_data_fingerprint": data_fingerprint,
        "candle_timestamp": pd.Timestamp(timestamp).isoformat(),
        "feature_cutoff_timestamp": pd.Timestamp(timestamp).isoformat(),
        "decision_time_basis": "AFTER_BAR_CLOSE",
        "execution_timestamp": pd.Timestamp(full_df.iloc[entry_idx]["timestamp"]).isoformat(),
        "execution_price_basis": "NEXT_AVAILABLE_BAR_OPEN",
        "execution_delay_candles": delay,
        "symbol": symbol,
        "timeframe": config.timeframe,
        "provider": provider,
        "replay_split": _chronological_split(replay_position, replay_total),
        "replay_position": replay_position,
        "replay_total_positions": replay_total,
        "replay_safe": bool(raw.get("replay_safe", False)),
        "learning_overrides_enabled": bool(raw.get("allow_learning_overrides", False)),
        "historical_edge_enabled": bool(raw.get("allow_historical_edge", False)),
        "historical_context_mode": context_mode,
        "side": side,
        "score": int(opportunity.score),
        "confidence_label": opportunity.confidence_label,
        "risk_label": opportunity.risk_label,
        "actionability": opportunity.actionability_label,
        "is_actionable": bool(opportunity.is_actionable),
        "entry_price": round(entry_price, 10),
        "entry_zone": opportunity.entry_zone,
        "stop_zone": opportunity.stop_zone,
        "targets": json.dumps(opportunity.targets, ensure_ascii=False),
        "fee_bps_per_side": cost.fee_bps_per_side,
        "slippage_bps_per_side": cost.slippage_bps_per_side,
        "round_trip_cost_pct": cost.round_trip_cost_pct,
        "execution_volatility_multiplier": cost.volatility_multiplier,
        "execution_liquidity_multiplier": cost.liquidity_multiplier,
        "dynamic_execution_costs": bool(config.dynamic_execution_costs),
        "adaptive_horizon_candles": adaptive_primary,
        **CURRENT_MODEL_CONTRACT.as_dict(),
        "regime_label": raw.get("regime_label", ""),
        "regime_confidence": raw.get("regime_confidence", ""),
        "long_score": raw.get("long_score", ""),
        "short_score": raw.get("short_score", ""),
        "trend_score": _component_points(opportunity, "Trend"),
        "momentum_score": _component_points(opportunity, "Momentum"),
        "volume_score": _component_points(opportunity, "Volume"),
        "structure_score": _component_points(opportunity, "Structure"),
        "regime_score": _component_points(opportunity, "Regime Adjustment"),
        "risk_penalty": _component_points(opportunity, "Risk Penalty"),
        "external_context_score": _component_points(opportunity, "External Context"),
        "adaptive_adjustment": _component_points(opportunity, "Adaptive Adjustment"),
        "historical_edge_score": _component_points(opportunity, "Historical Edge"),
        "news_sentiment_score": raw.get("news_sentiment_score", 0.0),
        "onchain_signal_score": raw.get("onchain_signal_score", 0.0),
        "cross_exchange_volume_ratio": raw.get("cross_exchange_volume_ratio", 1.0),
    }
    row.update(path)

    # v10.1.5 canonical evaluation recorder.  The replay engine already
    # calculates horizon metrics above; these aliases make the primary
    # research outcome explicit and stable for downstream optimization.
    primary_label = _horizon_label(config.timeframe, primary_horizon)
    market_col = f"market_return_after_{primary_horizon}c_pct"
    gross_col = f"gross_signed_return_after_{primary_horizon}c_pct"
    net_col = f"net_signed_return_after_{primary_horizon}c_pct"
    correct_col = f"direction_correct_after_{primary_horizon}c"
    market_return = row.get(market_col)
    gross_return = row.get(gross_col)
    net_return = row.get(net_col)
    exit_price = None
    if market_return is not None:
        try:
            exit_price = round(entry_price * (1.0 + float(market_return) / 100.0), 10)
        except (TypeError, ValueError):
            exit_price = None
    directional = side in {"LONG", "SHORT"}
    row.update({
        "evaluation_recorder_version": VERSION,
        "primary_evaluation_horizon_candles": primary_horizon,
        "primary_evaluation_horizon_label": primary_label,
        "exit_price": exit_price,
        "market_return_pct": market_return,
        "gross_return_pct": gross_return if directional else None,
        "net_return_pct": net_return if directional else None,
        "win": bool(float(net_return) > 0) if directional and net_return is not None else None,
        "direction_correct": row.get(correct_col) if directional else None,
        "target_hit": bool(row.get("target_1_hit", False)) if directional else None,
        "outcome_label": (
            "WIN" if directional and net_return is not None and float(net_return) > 0
            else "LOSS" if directional and net_return is not None
            else "NEUTRAL" if not directional
            else "PENDING"
        ),
        "evaluation_metric_source": f"{gross_col}|{net_col}",
        "adaptive_gross_return_pct": row.get(f"gross_signed_return_after_{adaptive_primary}c_pct"),
        "adaptive_net_return_pct": row.get(f"net_signed_return_after_{adaptive_primary}c_pct"),
    })
    # Compatibility aliases used by older optimization prototypes.
    row["return"] = row.get("gross_return_pct")
    row["net_return"] = row.get("net_return_pct")
    return row


def _checkpoint_paths(run_id: str) -> Tuple[Path, Path]:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR / f"{run_id}.json", CHECKPOINT_DIR / f"{run_id}.rows.csv"


def _load_checkpoint(run_id: str) -> Tuple[Dict[str, Any], pd.DataFrame]:
    checkpoint_path, rows_path = _checkpoint_paths(run_id)
    checkpoint: Dict[str, Any] = {}
    rows = pd.DataFrame()
    if checkpoint_path.exists():
        checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if rows_path.exists() and rows_path.stat().st_size:
        rows = pd.read_csv(rows_path, encoding="utf-8-sig")
    return checkpoint, rows


def _save_checkpoint(run: MarketReplayRun, state: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
    checkpoint_path, rows_path = _checkpoint_paths(run.run_id)
    payload = {
        "version": VERSION,
        "run": asdict(run),
        "state": state,
        "updated_utc": utc_now_iso(),
    }
    checkpoint_temp = checkpoint_path.with_name(checkpoint_path.name + ".tmp")
    checkpoint_temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    checkpoint_temp.replace(checkpoint_path)
    if rows:
        rows_temp = rows_path.with_name(rows_path.name + ".tmp")
        pd.DataFrame(rows).to_csv(rows_temp, index=False, encoding="utf-8-sig")
        rows_temp.replace(rows_path)
    run.checkpoint_path = str(checkpoint_path)


def _write_union_csv(path: Path, new_rows: pd.DataFrame, *, dedupe_columns: Sequence[str] = ()) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        try:
            old = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
            combined = pd.concat([old, new_rows], ignore_index=True, sort=False)
        except Exception:
            combined = new_rows.copy()
    else:
        combined = new_rows.copy()
    if dedupe_columns and all(column in combined.columns for column in dedupe_columns):
        combined = combined.drop_duplicates(subset=list(dedupe_columns), keep="last")
    temp = path.with_name(path.name + ".tmp")
    combined.to_csv(temp, index=False, encoding="utf-8-sig")
    temp.replace(path)


def _bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def _horizon_label(timeframe: str, horizon_candles: int) -> str:
    try:
        total_ms = timeframe_to_milliseconds(timeframe) * int(horizon_candles)
        hours = total_ms / 3_600_000
        if hours >= 24 and abs(hours % 24) < 1e-9:
            return f"{int(hours / 24)}d"
        if abs(hours - round(hours)) < 1e-9:
            return f"{int(round(hours))}h"
        return f"{hours:.2f}h"
    except Exception:
        return f"{int(horizon_candles)}c"


def _metric_row(group: pd.DataFrame, key: str, horizon_candles: int = 6) -> ReplayMetricRow:
    complete = group[group.get("evaluation_status", pd.Series(index=group.index, dtype=str)).astype(str) == "COMPLETE"]
    directional = complete[complete.get("side", pd.Series(index=complete.index, dtype=str)).isin(["LONG", "SHORT"])]
    gross_column = f"gross_signed_return_after_{int(horizon_candles)}c_pct"
    net_column = f"net_signed_return_after_{int(horizon_candles)}c_pct"
    gross = pd.to_numeric(directional.get(gross_column, pd.Series(dtype=float)), errors="coerce").dropna()
    net = pd.to_numeric(directional.get(net_column, pd.Series(dtype=float)), errors="coerce").dropna()
    target_hits = int(_bool_series(directional.get("target_1_hit", pd.Series(dtype=str))).sum()) if len(directional) else 0
    stop_hits = int(_bool_series(directional.get("stop_hit", pd.Series(dtype=str))).sum()) if len(directional) else 0
    wins = net[net > 0]
    losses = net[net < 0]
    profit_factor = float(wins.sum() / abs(losses.sum())) if len(losses) and abs(losses.sum()) > 0 else float("inf") if len(wins) else 0.0
    equity = net.fillna(0).cumsum()
    drawdown = equity - equity.cummax() if len(equity) else pd.Series(dtype=float)
    return ReplayMetricRow(
        key=str(key),
        rows=int(len(group)),
        directional_rows=int(len(directional)),
        complete_rows=int(len(complete)),
        win_rate_24h_pct=round(float((net > 0).mean() * 100), 2) if len(net) else 0.0,
        avg_gross_24h_pct=round(float(gross.mean()), 6) if len(gross) else 0.0,
        avg_net_24h_pct=round(float(net.mean()), 6) if len(net) else 0.0,
        median_net_24h_pct=round(float(net.median()), 6) if len(net) else 0.0,
        target_1_hit_rate_pct=round(target_hits / len(directional) * 100, 2) if len(directional) else 0.0,
        stop_hit_rate_pct=round(stop_hits / len(directional) * 100, 2) if len(directional) else 0.0,
        profit_factor_24h=round(profit_factor, 4) if math.isfinite(profit_factor) else 999.0,
        max_drawdown_proxy_pct=round(float(drawdown.min()), 6) if len(drawdown) else 0.0,
    )


def _group_metrics(frame: pd.DataFrame, column: str, horizon_candles: int = 6) -> List[Dict[str, Any]]:
    if frame.empty or column not in frame.columns:
        return []
    rows: List[Dict[str, Any]] = []
    for key, group in frame.groupby(column, dropna=False, sort=False):
        row = asdict(_metric_row(group, str(key), horizon_candles=horizon_candles))
        row[column] = row.pop("key")
        rows.append(row)
    return sorted(rows, key=lambda item: item.get("rows", 0), reverse=True)


def summarize_market_replay(
    frame: pd.DataFrame,
    *,
    run_id: str,
    symbol_results: Sequence[ReplaySymbolResult],
    context_mode: str,
    metric_horizon_candles: int = 6,
    timeframe: str = "4h",
) -> MarketReplaySummary:
    if frame is None or frame.empty:
        return MarketReplaySummary(
            run_id=run_id,
            version=VERSION,
            status="NO_REPLAY_ROWS",
            mode="REPLAY_SAFE_TECHNICAL_CORE",
            symbols_requested=len(symbol_results),
            symbols_completed=sum(1 for item in symbol_results if item.ok),
            total_candles=sum(item.candles_in_range for item in symbol_results),
            total_rows=0,
            complete_rows=0,
            directional_rows=0,
            actionable_rows=0,
            neutral_rows=0,
            win_rate_24h_pct=0.0,
            avg_gross_24h_pct=0.0,
            avg_net_24h_pct=0.0,
            profit_factor_24h=0.0,
            leakage_audit_status="FAILED_NO_REPLAY_ROWS",
            historical_context_mode=context_mode,
            evaluation_horizon_candles=int(metric_horizon_candles),
            evaluation_horizon_label=_horizon_label(timeframe, metric_horizon_candles),
            by_split=[], by_symbol=[], by_side=[], by_regime=[], by_year=[],
            blockers=["هیچ ردیف Market Replay ساخته نشد."],
            warnings=[],
        )

    work = frame.copy()
    work["year"] = pd.to_datetime(work["candle_timestamp"], utc=True, errors="coerce").dt.year.astype("Int64").astype(str)
    overall = _metric_row(work, "ALL", horizon_candles=metric_horizon_candles)
    complete_rows = int((work.get("evaluation_status", "").astype(str) == "COMPLETE").sum())
    directional_rows = int(work.get("side", pd.Series(dtype=str)).isin(["LONG", "SHORT"]).sum())
    actionable_rows = int(work.get("actionability", pd.Series(dtype=str)).isin(["ACTIONABLE", "HIGH_ACTIONABILITY"]).sum())
    neutral_rows = int((work.get("side", pd.Series(dtype=str)) == "NEUTRAL").sum())
    audit_statuses = [item.leakage_audit.status for item in symbol_results if item.leakage_audit]
    leakage_status = "PASSED_NO_LOOKAHEAD" if audit_statuses and all(item == "PASSED_NO_LOOKAHEAD" for item in audit_statuses) else "FAILED_OR_NOT_AUDITED"

    blockers: List[str] = []
    if leakage_status != "PASSED_NO_LOOKAHEAD":
        blockers.append("No-lookahead feature audit پاس نشده است.")
    if complete_rows < 500:
        blockers.append(f"Replay complete rows کمتر از 500 است: {complete_rows}")
    test_rows = work[work.get("replay_split", "") == "TEST_20"]
    test_metric = _metric_row(test_rows, "TEST_20", horizon_candles=metric_horizon_candles) if len(test_rows) else None
    if test_metric is None or test_metric.directional_rows < 50:
        blockers.append("Test split directional samples کمتر از 50 است.")
    if test_metric is not None and test_metric.avg_net_24h_pct <= 0:
        blockers.append("میانگین Net Return در Test split مثبت نیست.")

    if leakage_status != "PASSED_NO_LOOKAHEAD":
        status = "REPLAY_BLOCKED_LEAKAGE_AUDIT"
    elif complete_rows < 500:
        status = "REPLAY_ACTIVE_LOW_SAMPLE"
    elif blockers:
        status = "REPLAY_RESEARCH_NOT_VALIDATED"
    else:
        status = "REPLAY_RESEARCH_VALIDATED"

    warnings = [
        "Market Replay نتیجه Backtest است و جای Forward/Paper را نمی‌گیرد.",
        "نسخه v10 به‌صورت پیش‌فرض Technical/Regime core را Replay می‌کند؛ خبر تاریخی فقط با context_file زمان‌دار وارد می‌شود.",
        "در کندلی که Stop و Target همزمان لمس شوند، ترتیب محافظه‌کارانه Stop-first ثبت می‌شود.",
        "هرگونه تنظیم وزن باید فقط با Validation/Test split و سپس Forward انجام شود.",
    ]

    return MarketReplaySummary(
        run_id=run_id,
        version=VERSION,
        status=status,
        mode="REPLAY_SAFE_TECHNICAL_CORE",
        symbols_requested=len(symbol_results),
        symbols_completed=sum(1 for item in symbol_results if item.ok),
        total_candles=sum(item.candles_in_range for item in symbol_results),
        total_rows=int(len(work)),
        complete_rows=complete_rows,
        directional_rows=directional_rows,
        actionable_rows=actionable_rows,
        neutral_rows=neutral_rows,
        win_rate_24h_pct=overall.win_rate_24h_pct,
        avg_gross_24h_pct=overall.avg_gross_24h_pct,
        avg_net_24h_pct=overall.avg_net_24h_pct,
        profit_factor_24h=overall.profit_factor_24h,
        leakage_audit_status=leakage_status,
        historical_context_mode=context_mode,
        evaluation_horizon_candles=int(metric_horizon_candles),
        evaluation_horizon_label=_horizon_label(timeframe, metric_horizon_candles),
        by_split=_group_metrics(work, "replay_split", horizon_candles=metric_horizon_candles),
        by_symbol=_group_metrics(work, "symbol", horizon_candles=metric_horizon_candles),
        by_side=_group_metrics(work, "side", horizon_candles=metric_horizon_candles),
        by_regime=_group_metrics(work, "regime_label", horizon_candles=metric_horizon_candles),
        by_year=_group_metrics(work, "year", horizon_candles=metric_horizon_candles),
        blockers=blockers,
        warnings=warnings,
    )


def run_market_replay(
    config: MarketReplayConfig,
    *,
    run_id: str = "",
    resume: bool = False,
    save: bool = True,
) -> Tuple[MarketReplayRun, MarketReplaySummary, pd.DataFrame]:
    from engine.decision import DecisionEngine
    from features import add_features

    run_id = run_id or make_run_id()
    run = MarketReplayRun(
        run_id=run_id,
        version=VERSION,
        started_utc=utc_now_iso(),
        config=asdict(config),
    )
    registry = ExperimentRegistry()
    registry_started = False
    if save:
        registry.start_run(
            run_id,
            "REPLAY",
            hyperparameters=asdict(config),
            data_start_utc=config.start_utc,
            data_end_utc=config.end_utc,
        )
        registry_started = True
    checkpoint_state: Dict[str, Any] = {"next_index": {}, "completed_symbols": []}
    accumulated_rows: List[Dict[str, Any]] = []
    if resume:
        checkpoint_payload, old_rows = _load_checkpoint(run_id)
        checkpoint_state = checkpoint_payload.get("state", checkpoint_state) if checkpoint_payload else checkpoint_state
        previous_run = checkpoint_payload.get("run", {}) if checkpoint_payload else {}
        if previous_run:
            run.started_utc = str(previous_run.get("started_utc") or run.started_utc)
            restored_results = []
            for item in previous_run.get("symbol_results", []) or []:
                if not isinstance(item, dict):
                    continue
                audit_data = item.get("leakage_audit")
                audit = LeakageAudit(**audit_data) if isinstance(audit_data, dict) else None
                restored = dict(item)
                restored["leakage_audit"] = audit
                restored_results.append(ReplaySymbolResult(**restored))
            run.symbol_results = restored_results
        if not old_rows.empty:
            accumulated_rows = old_rows.to_dict(orient="records")

    engine = DecisionEngine(
        min_side_score=config.min_side_score,
        allow_learning_overrides=False,
        allow_historical_edge=False,
    )
    context_mode = "TIMESTAMPED_CONTEXT_FILE" if config.context_file else "TECHNICAL_CORE_ONLY"
    config_fingerprint = _config_fingerprint(config)
    decision_counter = len(accumulated_rows)

    for symbol in config.symbols:
        if symbol in checkpoint_state.get("completed_symbols", []):
            continue
        symbol_result = ReplaySymbolResult(symbol=symbol, timeframe=config.timeframe, ok=False)
        try:
            raw = load_history(symbol, config.timeframe, config.data_dir)
            symbol_result.candles_loaded = len(raw)
            market, provider, context_matches = _prepare_market_frame(raw, symbol=symbol, config=config)
            symbol_result.provider = provider
            symbol_result.candles_in_range = len(market)
            symbol_data_fingerprint = _data_fingerprint(market, provider)
            experiment_id = hashlib.sha256(
                f"{config_fingerprint}|{symbol_data_fingerprint}".encode("utf-8")
            ).hexdigest()[:16]
            if market.empty:
                raise ValueError("historical dataset is empty for requested range")

            # Features are causal; compute once for speed and verify by
            # recomputing historical prefixes at selected audit points.
            featured = add_features(market.copy())
            featured.attrs["provider"] = provider
            featured.attrs["timeframe"] = config.timeframe
            symbol_result.leakage_audit = audit_causal_features(market, featured, config.min_window)
            if config.strict_leakage_audit and symbol_result.leakage_audit.status != "PASSED_NO_LOOKAHEAD":
                raise RuntimeError(f"feature leakage audit failed: {symbol_result.leakage_audit.status}")

            max_horizon = max(config.horizons) if config.horizons else 0
            if config.adaptive_evaluation_horizon:
                max_horizon *= 2
            last_signal_index = len(featured) - max_horizon - max(1, int(config.execution_delay_candles))
            first_signal_index = max(config.min_window, 35)
            if last_signal_index < first_signal_index:
                raise ValueError(f"insufficient replay candles after warmup: {len(featured)}")

            all_indices = list(range(first_signal_index, last_signal_index + 1, max(1, config.step)))
            position_by_index = {idx: position for position, idx in enumerate(all_indices)}
            start_from = int(checkpoint_state.get("next_index", {}).get(symbol, first_signal_index))
            indices = [idx for idx in all_indices if idx >= start_from]
            symbol_rows = 0
            first_timestamp = ""
            last_timestamp = ""

            for signal_idx in indices:
                replay_position = position_by_index[signal_idx]
                if config.max_decisions_per_symbol and symbol_rows >= config.max_decisions_per_symbol:
                    break
                window = featured.iloc[: signal_idx + 1].copy()
                window.attrs.update(featured.attrs)
                opportunity = engine.analyze(window, symbol=symbol, timeframe=config.timeframe)
                if not config.include_neutral and opportunity.side == "NEUTRAL":
                    checkpoint_state.setdefault("next_index", {})[symbol] = signal_idx + max(1, config.step)
                    continue

                row = _row_from_opportunity(
                    run_id=run_id,
                    config=config,
                    provider=provider,
                    symbol=symbol,
                    signal_idx=signal_idx,
                    replay_position=replay_position,
                    replay_total=len(all_indices),
                    full_df=featured,
                    opportunity=opportunity,
                    context_mode=context_mode,
                    experiment_id=experiment_id,
                    data_fingerprint=symbol_data_fingerprint,
                )
                accumulated_rows.append(row)
                symbol_rows += 1
                decision_counter += 1
                timestamp = row["candle_timestamp"]
                first_timestamp = first_timestamp or timestamp
                last_timestamp = timestamp
                checkpoint_state.setdefault("next_index", {})[symbol] = signal_idx + max(1, config.step)

                if save and config.checkpoint_every and decision_counter % max(1, config.checkpoint_every) == 0:
                    _save_checkpoint(run, checkpoint_state, accumulated_rows)

            symbol_result.ok = True
            symbol_result.decisions_written = symbol_rows
            symbol_result.first_decision_utc = first_timestamp
            symbol_result.last_decision_utc = last_timestamp
            checkpoint_state.setdefault("completed_symbols", []).append(symbol)
            run.symbol_results = [item for item in run.symbol_results if item.symbol != symbol]
            run.symbol_results.append(symbol_result)
            if save:
                _save_checkpoint(run, checkpoint_state, accumulated_rows)
            print(
                f"[OK] Replay {symbol}: candles={len(featured)} decisions={symbol_rows} "
                f"provider={provider} audit={symbol_result.leakage_audit.status} context_matches={context_matches}"
            )
        except Exception as exc:
            symbol_result.error = f"{type(exc).__name__}: {exc}"
            run.error_count += 1
            run.symbol_results = [item for item in run.symbol_results if item.symbol != symbol]
            run.symbol_results.append(symbol_result)
            print(f"[ERROR] Replay {symbol}: {symbol_result.error}")

    frame = pd.DataFrame(accumulated_rows)
    if not frame.empty and "decision_id" in frame.columns:
        frame = frame.drop_duplicates(subset=["decision_id"], keep="last").sort_values(["symbol", "candle_timestamp"]).reset_index(drop=True)

    run.finished_utc = utc_now_iso()
    completed_count = sum(1 for item in run.symbol_results if item.ok)
    run.ok = bool(len(frame)) and completed_count == len(config.symbols) and run.error_count == 0
    metric_horizon = max(config.horizons) if config.horizons else 6
    summary = summarize_market_replay(
        frame,
        run_id=run_id,
        symbol_results=run.symbol_results,
        context_mode=context_mode,
        metric_horizon_candles=metric_horizon,
        timeframe=config.timeframe,
    )

    if save:
        REPLAY_DIR.mkdir(parents=True, exist_ok=True)
        output_csv = REPLAY_DIR / f"{run_id}.csv"
        output_json = REPLAY_DIR / f"{run_id}.json"
        output_report = REPLAY_DIR / f"{run_id}_report.md"
        run.output_csv = str(output_csv)
        run.output_json = str(output_json)
        run.output_report = str(output_report)
        frame.to_csv(output_csv, index=False, encoding="utf-8-sig")
        _write_union_csv(CUMULATIVE_REPLAY_FILE, frame, dedupe_columns=["decision_id"])
        payload = {"run": asdict(run), "summary": asdict(summary)}
        output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        output_report.write_text(format_market_replay_report(run, summary), encoding="utf-8")
        _write_union_csv(RUNS_FILE, pd.DataFrame([{
            "run_id": run.run_id,
            "version": run.version,
            "started_utc": run.started_utc,
            "finished_utc": run.finished_utc,
            "ok": run.ok,
            "symbols_completed": sum(1 for item in run.symbol_results if item.ok),
            "rows": len(frame),
            "status": summary.status,
            "leakage_audit_status": summary.leakage_audit_status,
            "output_csv": run.output_csv,
            "output_report": run.output_report,
        }]), dedupe_columns=["run_id"])
        checkpoint_state["finished"] = True
        _save_checkpoint(run, checkpoint_state, accumulated_rows)

    if registry_started:
        if not frame.empty:
            registry.update_data_provenance(
                run_id,
                data_start_utc=str(frame["candle_timestamp"].min()),
                data_end_utc=str(frame["candle_timestamp"].max()),
                data_fingerprint=fingerprint(sorted(frame["replay_data_fingerprint"].astype(str).unique())),
            )
        registry.finish_run(
            run_id,
            "COMPLETED" if run.ok else "FAILED",
            {
                "summary": asdict(summary),
                "output_csv": run.output_csv,
                "output_report": run.output_report,
            },
        )

    return run, summary, frame


def load_market_replay_status(path: Path | str = CUMULATIVE_REPLAY_FILE) -> MarketReplaySummary:
    file_path = Path(path)
    if not file_path.exists() or file_path.stat().st_size == 0:
        return summarize_market_replay(
            pd.DataFrame(), run_id="market_replay_status", symbol_results=[], context_mode="UNKNOWN",
            metric_horizon_candles=6, timeframe="4h"
        )
    try:
        frame = pd.read_csv(file_path, encoding="utf-8-sig", low_memory=False)
    except Exception:
        frame = pd.DataFrame()
    results: List[ReplaySymbolResult] = []
    if not frame.empty and "symbol" in frame.columns:
        for symbol, group in frame.groupby("symbol"):
            audit_passed = bool(group.get("replay_safe", pd.Series(dtype=str)).astype(str).str.lower().isin({"true", "1"}).all())
            results.append(ReplaySymbolResult(
                symbol=str(symbol),
                timeframe=str(group.get("timeframe", pd.Series([""])).iloc[-1]),
                ok=True,
                candles_in_range=int(len(group)),
                decisions_written=int(len(group)),
                leakage_audit=LeakageAudit(
                    status="PASSED_NO_LOOKAHEAD" if audit_passed else "FAILED_OR_UNKNOWN",
                    points_checked=0,
                    feature_values_checked=0,
                    mismatches=0 if audit_passed else 1,
                    max_abs_difference=0.0,
                ),
            ))
    context_mode = str(frame.get("historical_context_mode", pd.Series(["UNKNOWN"])).iloc[-1]) if len(frame) else "UNKNOWN"
    horizon_candidates = []
    for column in frame.columns:
        if column.startswith("net_signed_return_after_") and column.endswith("c_pct"):
            try:
                horizon_candidates.append(int(column.split("after_", 1)[1].split("c_pct", 1)[0]))
            except Exception:
                pass
    metric_horizon = max(horizon_candidates) if horizon_candidates else 6
    timeframe = str(frame.get("timeframe", pd.Series(["4h"])).iloc[-1]) if len(frame) else "4h"
    return summarize_market_replay(
        frame, run_id="market_replay_status", symbol_results=results, context_mode=context_mode,
        metric_horizon_candles=metric_horizon, timeframe=timeframe
    )


def format_market_replay_console(summary: MarketReplaySummary, compact: bool = False) -> str:
    lines = [
        "=" * 112,
        f"Freakto Market Replay Engine {VERSION}",
        "=" * 112,
        f"Status                 : {summary.status}",
        f"Run ID                 : {summary.run_id}",
        f"Mode                   : {summary.mode}",
        f"Symbols Completed      : {summary.symbols_completed}/{summary.symbols_requested}",
        f"Candles / Rows         : {summary.total_candles} / {summary.total_rows}",
        f"Complete / Directional : {summary.complete_rows} / {summary.directional_rows}",
        f"Actionable / Neutral   : {summary.actionable_rows} / {summary.neutral_rows}",
        f"Evaluation Horizon     : {summary.evaluation_horizon_label} ({summary.evaluation_horizon_candles} candles)",
        f"Win Rate Horizon       : {summary.win_rate_24h_pct:.2f}%",
        f"Avg Gross / Net        : {summary.avg_gross_24h_pct:.4f}% / {summary.avg_net_24h_pct:.4f}%",
        f"Profit Factor          : {summary.profit_factor_24h}",
        f"Leakage Audit          : {summary.leakage_audit_status}",
        f"Historical Context     : {summary.historical_context_mode}",
    ]
    if summary.by_split:
        lines.extend(["", "Chronological Splits:"])
        for item in summary.by_split:
            lines.append(
                f"- {item.get('replay_split')}: rows={item.get('rows')} directional={item.get('directional_rows')} "
                f"win={item.get('win_rate_24h_pct')}% avg_net={item.get('avg_net_24h_pct')}% "
                f"PF={item.get('profit_factor_24h')}"
            )
    if not compact and summary.by_symbol:
        lines.extend(["", "By Symbol:"])
        for item in summary.by_symbol[:12]:
            lines.append(
                f"- {item.get('symbol')}: rows={item.get('rows')} win={item.get('win_rate_24h_pct')}% "
                f"avg_net={item.get('avg_net_24h_pct')}% PF={item.get('profit_factor_24h')}"
            )
    if summary.blockers:
        lines.extend(["", "Blockers:"])
        lines.extend(f"[BLOCKER] {item}" for item in summary.blockers)
    if summary.warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"[WARNING] {item}" for item in summary.warnings)
    lines.append("=" * 112)
    return "\n".join(lines)


def format_market_replay_report(run: MarketReplayRun, summary: MarketReplaySummary) -> str:
    lines = [
        f"# Freakto Market Replay Report {VERSION}",
        "",
        f"- Run ID: `{run.run_id}`",
        f"- Started UTC: `{run.started_utc}`",
        f"- Finished UTC: `{run.finished_utc}`",
        f"- Status: `{summary.status}`",
        f"- Replay mode: `{summary.mode}`",
        f"- Leakage audit: `{summary.leakage_audit_status}`",
        "",
        "## Summary",
        "",
        f"- Rows: {summary.total_rows}",
        f"- Complete rows: {summary.complete_rows}",
        f"- Directional rows: {summary.directional_rows}",
        f"- Evaluation horizon: {summary.evaluation_horizon_label} ({summary.evaluation_horizon_candles} candles)",
        f"- Horizon win rate: {summary.win_rate_24h_pct:.2f}%",
        f"- Avg gross: {summary.avg_gross_24h_pct:.4f}%",
        f"- Avg net: {summary.avg_net_24h_pct:.4f}%",
        f"- Profit factor: {summary.profit_factor_24h}",
        "",
        "## Chronological splits",
        "",
    ]
    for item in summary.by_split:
        lines.append(
            f"- **{item.get('replay_split')}**: rows={item.get('rows')}, directional={item.get('directional_rows')}, "
            f"win24={item.get('win_rate_24h_pct')}%, avg_net24={item.get('avg_net_24h_pct')}%, "
            f"profit_factor={item.get('profit_factor_24h')}"
        )
    if summary.blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in summary.blockers)
    lines.extend(["", "## Safety", ""])
    lines.extend(f"- {item}" for item in summary.warnings)
    return "\n".join(lines) + "\n"
