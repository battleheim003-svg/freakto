"""Event-based opportunity universe for Freakto research.

The runtime DecisionEngine is intentionally untouched.  This module converts
per-candle replay decisions into a sparse, pre-declared event universe using
entry-time information only.  Outcome, future return, MFE/MAE and exit fields
are never used to detect an event or to pass the pre-trade cost gate.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from engine.multi_cycle_validation import normalize_replay_rows
from engine.geometry_parser import parse_trade_geometry
from engine.cost_gate_diagnostics import rejection_reason

VERSION = "2.0.1"
MODE = "EVENT_OPPORTUNITY_UNIVERSE_DEVELOPMENT_ONLY"

LEAKAGE_TOKENS = (
    "return",
    "outcome",
    "future",
    "win",
    "loss",
    "target_hit",
    "stop_hit",
    "first_exit",
    "mfe",
    "mae",
    "exit_price",
    "direction_correct",
    "label",
)

TIMESTAMP_CANDIDATES = (
    "candle_timestamp",
    "timestamp_utc",
    "timestamp",
    "feature_cutoff_timestamp",
)

ALIASES: Mapping[str, Tuple[str, ...]] = {
    "trend": ("trend_score",),
    "momentum": ("momentum_score",),
    "volume": ("volume_score",),
    "structure": ("structure_score",),
    "regime_score": ("regime_score",),
    "risk": ("risk_penalty",),
    "atr": ("atr_pct", "atr_percent", "atr_14_pct", "atr_ratio_pct", "execution_volatility_multiplier"),
    "rsi": ("rsi_14", "rsi"),
    "macd": ("macd_histogram", "macd_hist", "macd_diff"),
    "cost": (
        "round_trip_cost_pct",
        "execution_cost_pct",
        "total_cost_pct",
        "estimated_round_trip_cost_pct",
        "fee_slippage_pct",
    ),
    "entry": ("entry_price", "entry_mid", "planned_entry_price"),
    "target": ("target_1", "target1", "target_1_price", "target_price", "targets"),
    "stop": ("stop_price", "stop", "planned_stop_price", "stop_zone"),
}

EXPLICIT_BREAKOUT_COLUMNS = (
    "breakout_confirmed",
    "structure_break_confirmed",
    "breakout_up",
    "breakout_down",
)
EXPLICIT_VOL_EXPANSION_COLUMNS = (
    "volatility_expansion",
    "atr_expansion_confirmed",
    "compression_breakout",
)
EXPLICIT_SWEEP_COLUMNS = (
    "liquidity_sweep",
    "liquidity_sweep_confirmed",
    "sweep_high",
    "sweep_low",
)

EVENT_PRIORITY = (
    "LIQUIDITY_SWEEP",
    "BREAKOUT_CONFIRMATION",
    "VOLATILITY_EXPANSION",
    "REGIME_TRANSITION",
    "EXTREME_MEAN_REVERSION",
)


@dataclass(frozen=True)
class EventUniverseConfig:
    development_cutoff_utc: str = "2026-07-09T12:00:00Z"
    breakout_structure_min: float = 8.0
    breakout_volume_min: float = 10.0
    breakout_trend_min: float = 18.0
    mean_reversion_rsi_low: float = 30.0
    mean_reversion_rsi_high: float = 70.0
    mean_reversion_regimes: Tuple[str, ...] = ("SIDEWAYS", "QUIET", "RANGE", "RANGING", "NEUTRAL")
    proxy_lookback: int = 126
    proxy_min_periods: int = 24
    breakout_structure_quantile: float = 0.70
    breakout_volume_quantile: float = 0.70
    breakout_trend_quantile: float = 0.65
    mean_reversion_momentum_quantile: float = 0.20
    volatility_quantile: float = 0.80
    transition_structure_quantile: float = 0.60
    volatility_lookback: int = 42
    volatility_expansion_ratio: float = 1.30
    volatility_prior_max_ratio: float = 1.05
    volatility_volume_min: float = 5.0
    structure_sweep_min: float = 8.0
    regime_transition_structure_min: float = 6.0
    regime_transition_volume_min: float = 5.0
    regime_transition_trend_min: float = 14.0
    maximum_risk_penalty: float = 25.0
    maximum_cost_pct: float = 1.25
    minimum_target_to_cost: float = 2.0
    minimum_net_reward_risk: float = 0.50
    minimum_target_distance_pct: float = 0.10
    require_directional_side: bool = True

    def validate(self) -> None:
        cutoff = pd.Timestamp(self.development_cutoff_utc)
        if cutoff.tzinfo is None:
            raise ValueError("development_cutoff_utc must include a timezone")
        if self.volatility_lookback < 5:
            raise ValueError("volatility_lookback must be at least 5")
        if self.proxy_lookback < 10 or self.proxy_min_periods < 5:
            raise ValueError("proxy lookback/min periods are too small")
        for value in (self.breakout_structure_quantile, self.breakout_volume_quantile, self.breakout_trend_quantile, self.mean_reversion_momentum_quantile, self.volatility_quantile, self.transition_structure_quantile):
            if not 0 < value < 1:
                raise ValueError("proxy quantiles must be between 0 and 1")
        if self.volatility_expansion_ratio <= 1.0:
            raise ValueError("volatility_expansion_ratio must exceed 1")
        if self.minimum_target_to_cost < 0 or self.minimum_net_reward_risk < 0:
            raise ValueError("cost geometry thresholds cannot be negative")


@dataclass(frozen=True)
class EventUniverseDiagnostics:
    rows_loaded: int
    rows_usable: int
    event_rows: int
    unique_event_decisions: int
    multi_event_decisions: int
    explicit_breakout_rows: int
    explicit_sweep_rows: int
    explicit_volatility_rows: int
    aggregate_score_used: bool = False
    outcome_fields_used: bool = False
    breakout_rows: int = 0
    mean_reversion_rows: int = 0
    volatility_expansion_rows: int = 0
    regime_transition_rows: int = 0
    liquidity_sweep_rows: int = 0
    schema_mode: str = "UNKNOWN"
    unavailable_event_families: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _first_existing(frame: pd.DataFrame, aliases: Sequence[str]) -> Optional[str]:
    return next((column for column in aliases if column in frame.columns), None)


def _numeric(frame: pd.DataFrame, key: str, default: float = np.nan) -> pd.Series:
    column = _first_existing(frame, ALIASES[key])
    if column is None:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _truthy_series(frame: pd.DataFrame, columns: Sequence[str]) -> pd.Series:
    result = pd.Series(False, index=frame.index, dtype=bool)
    truthy = {"1", "true", "yes", "y", "on", "hit", "confirmed", "long", "short"}
    for column in columns:
        if column not in frame.columns:
            continue
        values = frame[column]
        numeric = pd.to_numeric(values, errors="coerce")
        textual = values.fillna("").astype(str).str.strip().str.lower()
        result |= numeric.fillna(0).ne(0) | textual.isin(truthy)
    return result


def _recover_mixed_timestamps(frame: pd.DataFrame) -> pd.DataFrame:
    standard = normalize_replay_rows(frame)
    if len(standard) >= max(1, int(len(frame) * 0.95)):
        return standard
    work = frame.copy()
    ts_col = _first_existing(work, TIMESTAMP_CANDIDATES)
    if ts_col is None:
        return standard
    try:
        work["__timestamp"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce", format="mixed")
    except TypeError:
        work["__timestamp"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce")
    return_col = next(
        (
            c
            for c in (
                "net_signed_return_after_6c_pct",
                "net_return_pct",
                "net_signed_return_after_12c_pct",
            )
            if c in work.columns
        ),
        None,
    )
    if return_col is None:
        return standard
    work["__return"] = pd.to_numeric(work[return_col], errors="coerce")
    if "side" not in work.columns:
        work["side"] = "NEUTRAL"
    if "regime" not in work.columns:
        work["regime"] = work.get("regime_label", "UNKNOWN")
    work["side"] = work["side"].fillna("NEUTRAL").astype(str).str.upper()
    work["regime"] = work["regime"].fillna("UNKNOWN").astype(str).str.upper()
    if "score" not in work.columns:
        work["score"] = np.nan
    work["score"] = pd.to_numeric(work["score"], errors="coerce")
    recovered = work.dropna(subset=["__timestamp", "__return"]).sort_values("__timestamp").reset_index(drop=True)
    return recovered if len(recovered) > len(standard) else standard




def _normalize_paper_entry_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize entry-time decision rows without requiring future outcomes."""
    work = frame.copy()
    ts_col = _first_existing(work, TIMESTAMP_CANDIDATES)
    if ts_col is None:
        return pd.DataFrame()
    try:
        work["__timestamp"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce", format="mixed")
    except TypeError:
        work["__timestamp"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce")
    work["__return"] = np.nan
    if "side" not in work.columns:
        work["side"] = "NEUTRAL"
    work["side"] = work["side"].fillna("NEUTRAL").astype(str).str.upper()
    if "regime" not in work.columns:
        work["regime"] = work.get("regime_label", "UNKNOWN")
    work["regime"] = work["regime"].fillna("UNKNOWN").astype(str).str.upper()
    if "score" not in work.columns:
        work["score"] = np.nan
    work["score"] = pd.to_numeric(work["score"], errors="coerce")
    if "symbol" not in work.columns:
        work["symbol"] = "UNKNOWN"
    if "timeframe" not in work.columns:
        work["timeframe"] = "4h"
    return work.dropna(subset=["__timestamp"]).sort_values("__timestamp", kind="stable").reset_index(drop=True)


def validate_event_feature_names(features: Sequence[str]) -> None:
    for name in features:
        lowered = str(name).strip().lower()
        if not lowered:
            raise ValueError("event feature names cannot be empty")
        if any(token in lowered for token in LEAKAGE_TOKENS):
            raise ValueError(f"Outcome/leakage field cannot detect an event: {name}")


def prepare_event_rows(
    frame: pd.DataFrame,
    config: EventUniverseConfig,
    *,
    time_scope: str = "development",
) -> pd.DataFrame:
    """Normalize and enforce a strict development/fresh boundary."""
    config.validate()
    if frame is None or frame.empty:
        return pd.DataFrame()
    work = _normalize_paper_entry_rows(frame) if time_scope == "paper" else _recover_mixed_timestamps(frame)
    cutoff = pd.Timestamp(config.development_cutoff_utc)
    if time_scope == "development":
        work = work[work["__timestamp"] <= cutoff].copy()
    elif time_scope == "fresh":
        work = work[work["__timestamp"] > cutoff].copy()
    elif time_scope == "paper":
        pass
    else:
        raise ValueError("time_scope must be 'development', 'fresh' or 'paper'")
    if "regime_label" in work.columns and ("regime" not in work.columns or work["regime"].eq("UNKNOWN").all()):
        work["regime"] = work["regime_label"].fillna("UNKNOWN").astype(str).str.upper()
    if config.require_directional_side:
        work = work[work["side"].isin(["LONG", "SHORT"])].copy()
    if "decision_id" not in work.columns:
        stable = (
            work["__timestamp"].astype(str)
            + "|"
            + work.get("symbol", pd.Series("UNKNOWN", index=work.index)).astype(str)
            + "|"
            + work["side"].astype(str)
        )
        work["decision_id"] = stable.map(lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest()[:20])
    work = work.drop_duplicates("decision_id", keep="last")
    sort_columns = [c for c in ("symbol", "timeframe", "__timestamp", "decision_id") if c in work.columns]
    return work.sort_values(sort_columns, kind="stable").reset_index(drop=True)


def _geometry(frame: pd.DataFrame) -> pd.DataFrame:
    entry_col = _first_existing(frame, ALIASES["entry"])
    target_col = _first_existing(frame, ALIASES["target"])
    stop_col = _first_existing(frame, ALIASES["stop"])
    entries = frame[entry_col] if entry_col else pd.Series(np.nan, index=frame.index)
    targets = frame[target_col] if target_col else pd.Series(np.nan, index=frame.index)
    stops = frame[stop_col] if stop_col else pd.Series(np.nan, index=frame.index)
    records = []
    for idx in frame.index:
        parsed = parse_trade_geometry(entries.loc[idx], stops.loc[idx], targets.loc[idx], frame.loc[idx, "side"])
        if parsed.geometry_valid:
            if str(frame.loc[idx, "side"]).upper() == "LONG":
                target_distance = (parsed.target / parsed.entry - 1.0) * 100.0
                stop_distance = (1.0 - parsed.stop / parsed.entry) * 100.0
            else:
                target_distance = (1.0 - parsed.target / parsed.entry) * 100.0
                stop_distance = (parsed.stop / parsed.entry - 1.0) * 100.0
        else:
            target_distance = np.nan
            stop_distance = np.nan
        records.append({
            "entry_price_normalized": parsed.entry,
            "target_price_normalized": parsed.target,
            "stop_price_normalized": parsed.stop,
            "entry_valid": parsed.entry_valid,
            "stop_valid": parsed.stop_valid,
            "target_valid": parsed.target_valid,
            "geometry_valid": parsed.geometry_valid,
            "geometry_parse_reason": parsed.parse_reason,
            "target_distance_pct": max(0.0, target_distance) if np.isfinite(target_distance) else np.nan,
            "stop_distance_pct": max(0.0, stop_distance) if np.isfinite(stop_distance) else np.nan,
        })
    return pd.DataFrame(records, index=frame.index)

def _group_keys(frame: pd.DataFrame) -> List[str]:
    keys = [column for column in ("symbol", "timeframe") if column in frame.columns]
    return keys or ["side"]


def _causal_quantile(frame: pd.DataFrame, values: pd.Series, keys: Sequence[str], q: float, config: EventUniverseConfig) -> pd.Series:
    tmp = frame.copy()
    tmp["__proxy_value"] = pd.to_numeric(values, errors="coerce")
    return tmp.groupby(list(keys), sort=False, dropna=False)["__proxy_value"].transform(
        lambda series: series.shift(1).rolling(config.proxy_lookback, min_periods=config.proxy_min_periods).quantile(q)
    )


def _event_masks(frame: pd.DataFrame, config: EventUniverseConfig) -> Tuple[Dict[str, pd.Series], Dict[str, Any]]:
    trend = _numeric(frame, "trend", 0.0).fillna(0.0)
    momentum = _numeric(frame, "momentum", 0.0).fillna(0.0)
    volume = _numeric(frame, "volume", 0.0).fillna(0.0)
    structure = _numeric(frame, "structure", 0.0).fillna(0.0)
    volatility = _numeric(frame, "atr", np.nan)
    rsi = _numeric(frame, "rsi", np.nan)
    side = frame["side"].astype(str).str.upper()
    regime = frame.get("regime", pd.Series("UNKNOWN", index=frame.index)).fillna("UNKNOWN").astype(str).str.upper()
    long_score = pd.to_numeric(frame["long_score"], errors="coerce") if "long_score" in frame.columns else pd.Series(np.nan, index=frame.index, dtype=float)
    short_score = pd.to_numeric(frame["short_score"], errors="coerce") if "short_score" in frame.columns else pd.Series(np.nan, index=frame.index, dtype=float)

    explicit_breakout = _truthy_series(frame, EXPLICIT_BREAKOUT_COLUMNS)
    explicit_volatility = _truthy_series(frame, EXPLICIT_VOL_EXPANSION_COLUMNS)
    explicit_sweep = _truthy_series(frame, EXPLICIT_SWEEP_COLUMNS)

    bull_labels = {"BULL", "BULLISH", "UPTREND", "TREND_UP", "RISK_ON"}
    bear_labels = {"BEAR", "BEARISH", "DOWNTREND", "TREND_DOWN", "RISK_OFF"}
    aligned_by_regime = (side.eq("LONG") & regime.isin(bull_labels)) | (side.eq("SHORT") & regime.isin(bear_labels))
    aligned_by_scores = (side.eq("LONG") & long_score.ge(short_score)) | (side.eq("SHORT") & short_score.ge(long_score))
    direction_aligned = aligned_by_regime | aligned_by_scores.fillna(False)

    keys = _group_keys(frame)
    structure_q = _causal_quantile(frame, structure, keys, config.breakout_structure_quantile, config)
    volume_q = _causal_quantile(frame, volume, keys, config.breakout_volume_quantile, config)
    trend_q = _causal_quantile(frame, trend, keys, config.breakout_trend_quantile, config)
    momentum_low_q = _causal_quantile(frame, momentum, keys, config.mean_reversion_momentum_quantile, config)
    volatility_q = _causal_quantile(frame, volatility, keys, config.volatility_quantile, config)
    transition_structure_q = _causal_quantile(frame, structure, keys, config.transition_structure_quantile, config)

    breakout_absolute = (
        structure.ge(config.breakout_structure_min)
        & volume.ge(config.breakout_volume_min)
        & trend.ge(config.breakout_trend_min)
    )
    breakout_relative = structure.ge(structure_q) & volume.ge(volume_q) & trend.ge(trend_q)
    breakout_proxy = direction_aligned & (breakout_absolute | breakout_relative)

    range_regime = regime.isin([item.upper() for item in config.mean_reversion_regimes])
    rsi_signal = (side.eq("LONG") & rsi.le(config.mean_reversion_rsi_low)) | (
        side.eq("SHORT") & rsi.ge(config.mean_reversion_rsi_high)
    )
    # The production replay currently does not persist RSI. In that schema, a
    # weak momentum tail inside a range regime is a causal, entry-time proxy.
    momentum_signal = momentum.le(momentum_low_q)
    mean_reversion = range_regime & (rsi_signal.fillna(False) | momentum_signal.fillna(False))

    tmp = frame.copy()
    tmp["__event_volatility"] = volatility
    groups_tmp = tmp.groupby(keys, sort=False, dropna=False)
    past_median = groups_tmp["__event_volatility"].transform(
        lambda series: series.shift(1).rolling(config.volatility_lookback, min_periods=5).median()
    )
    volatility_ratio = volatility / past_median.replace(0, np.nan)
    tmp["__event_volatility_ratio"] = volatility_ratio
    prior_ratio = tmp.groupby(keys, sort=False, dropna=False)["__event_volatility_ratio"].shift(1)
    ratio_proxy = volatility_ratio.ge(config.volatility_expansion_ratio) & prior_ratio.le(config.volatility_prior_max_ratio)
    quantile_proxy = volatility.ge(volatility_q) & volatility_q.notna()
    volatility_proxy = (ratio_proxy | quantile_proxy) & volume.ge(volume_q.fillna(config.volatility_volume_min))

    previous_regime = frame.groupby(keys, sort=False, dropna=False)["regime"].shift(1) if "regime" in frame.columns else pd.Series(np.nan, index=frame.index)
    regime_transition = (
        previous_regime.notna()
        & regime.ne(previous_regime.astype(str).str.upper())
        & direction_aligned
        & structure.ge(transition_structure_q.fillna(config.regime_transition_structure_min))
        & volume.ge(volume_q.fillna(config.regime_transition_volume_min))
    )

    # A liquidity sweep cannot be reconstructed honestly from component scores;
    # it remains available only when an explicit entry-time sweep flag exists.
    sweep_direction = explicit_sweep & structure.ge(config.structure_sweep_min)
    masks = {
        "LIQUIDITY_SWEEP": sweep_direction,
        "BREAKOUT_CONFIRMATION": explicit_breakout | breakout_proxy,
        "VOLATILITY_EXPANSION": explicit_volatility | volatility_proxy.fillna(False),
        "REGIME_TRANSITION": regime_transition.fillna(False),
        "EXTREME_MEAN_REVERSION": mean_reversion.fillna(False),
    }
    unavailable: List[str] = []
    if not any(column in frame.columns for column in EXPLICIT_SWEEP_COLUMNS):
        unavailable.append("LIQUIDITY_SWEEP")
    schema_mode = "RAW_INDICATOR_SCHEMA" if (rsi.notna().any() or any(alias in frame.columns for alias in ALIASES["atr"][:-1])) else "REPLAY_COMPONENT_SCHEMA"
    diagnostics: Dict[str, Any] = {
        "explicit_breakout_rows": int(explicit_breakout.sum()),
        "explicit_sweep_rows": int(explicit_sweep.sum()),
        "explicit_volatility_rows": int(explicit_volatility.sum()),
        "breakout_rows": int(masks["BREAKOUT_CONFIRMATION"].sum()),
        "mean_reversion_rows": int(masks["EXTREME_MEAN_REVERSION"].sum()),
        "volatility_expansion_rows": int(masks["VOLATILITY_EXPANSION"].sum()),
        "regime_transition_rows": int(masks["REGIME_TRANSITION"].sum()),
        "liquidity_sweep_rows": int(masks["LIQUIDITY_SWEEP"].sum()),
        "schema_mode": schema_mode,
        "unavailable_event_families": tuple(unavailable),
    }
    frame["event_volatility_past_median"] = past_median
    frame["event_volatility_expansion_ratio"] = volatility_ratio
    frame["event_previous_regime"] = previous_regime
    frame["event_structure_threshold"] = structure_q
    frame["event_volume_threshold"] = volume_q
    frame["event_trend_threshold"] = trend_q
    return masks, diagnostics


def build_event_opportunity_universe(
    frame: pd.DataFrame,
    config: Optional[EventUniverseConfig] = None,
    *,
    time_scope: str = "development",
) -> Tuple[pd.DataFrame, EventUniverseDiagnostics]:
    """Return one sparse primary-event row per decision.

    Multiple simultaneous events are preserved in ``event_types`` while the
    pre-declared priority chooses one ``primary_event`` for portfolio research.
    """
    config = config or EventUniverseConfig()
    rows_loaded = 0 if frame is None else int(len(frame))
    work = prepare_event_rows(frame, config, time_scope=time_scope)
    if work.empty:
        return work, EventUniverseDiagnostics(rows_loaded, 0, 0, 0, 0, 0, 0, 0)

    # Only explicitly approved entry-time fields participate in event creation.
    validate_event_feature_names(
        [
            "trend_score",
            "momentum_score",
            "volume_score",
            "structure_score",
            "regime_score",
            "risk_penalty",
            "atr_pct",
            "rsi_14",
            "macd_histogram",
            "round_trip_cost_pct",
            "entry_price",
            "target_1",
            "stop_price",
            "side",
            "regime",
            "symbol",
            "timeframe",
        ]
    )

    masks, explicit = _event_masks(work, config)
    event_lists: List[List[str]] = []
    for idx in work.index:
        event_lists.append([name for name in EVENT_PRIORITY if bool(masks[name].loc[idx])])
    work["event_types"] = [json.dumps(items, ensure_ascii=False) for items in event_lists]
    work["event_count"] = [len(items) for items in event_lists]
    work["primary_event"] = [items[0] if items else "NO_EVENT" for items in event_lists]
    work["has_event"] = work["event_count"].gt(0)
    work["event_source"] = np.where(
        work["primary_event"].eq("LIQUIDITY_SWEEP"),
        "EXPLICIT_ENTRY_FLAG",
        np.where(
            work["primary_event"].eq("BREAKOUT_CONFIRMATION") & _truthy_series(work, EXPLICIT_BREAKOUT_COLUMNS),
            "EXPLICIT_ENTRY_FLAG",
            np.where(
                work["primary_event"].eq("VOLATILITY_EXPANSION") & _truthy_series(work, EXPLICIT_VOL_EXPANSION_COLUMNS),
                "EXPLICIT_ENTRY_FLAG",
                "CAUSAL_ENTRY_PROXY",
            ),
        ),
    )

    geometry = _geometry(work)
    for column in geometry.columns:
        work[column] = geometry[column]
    cost = _numeric(work, "cost", np.nan).clip(lower=0)
    if time_scope == "paper":
        fee_bps = pd.to_numeric(work.get("fee_bps_per_side", pd.Series(np.nan, index=work.index)), errors="coerce")
        slippage_bps = pd.to_numeric(work.get("slippage_bps_per_side", work.get("base_slippage_bps_per_side", pd.Series(np.nan, index=work.index))), errors="coerce")
        derived_cost = 2.0 * (fee_bps.fillna(10.0) + slippage_bps.fillna(5.0)) / 100.0
        cost = cost.where(cost.notna(), derived_cost)
    risk = _numeric(work, "risk", 0.0).fillna(0.0)
    work["event_execution_cost_pct"] = cost
    work["gross_target_to_cost"] = work["target_distance_pct"] / cost.replace(0, np.nan)
    net_reward = work["target_distance_pct"] - cost
    net_loss = work["stop_distance_pct"] + cost
    work["net_reward_pct"] = net_reward
    work["net_loss_pct"] = net_loss
    work["net_reward_risk"] = net_reward / net_loss.replace(0, np.nan)
    geometry_valid = (
        work["target_distance_pct"].ge(config.minimum_target_distance_pct)
        & work["stop_distance_pct"].gt(0)
        & cost.notna()
    )
    work["cost_gate_pass"] = (
        work["has_event"]
        & geometry_valid
        & cost.le(config.maximum_cost_pct)
        & work["gross_target_to_cost"].ge(config.minimum_target_to_cost)
        & work["net_reward_risk"].ge(config.minimum_net_reward_risk)
        & risk.le(config.maximum_risk_penalty)
    )
    work["cost_gate_rejection_reason"] = rejection_reason(
        work,
        maximum_cost_pct=config.maximum_cost_pct,
        minimum_target_to_cost=config.minimum_target_to_cost,
        minimum_net_reward_risk=config.minimum_net_reward_risk,
        maximum_risk_penalty=config.maximum_risk_penalty,
    )
    work["opportunity_id"] = (
        work["decision_id"].astype(str) + "|" + work["primary_event"].astype(str)
    ).map(lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()[:24])

    event_only = work[work["has_event"]].copy().reset_index(drop=True)
    diagnostics = EventUniverseDiagnostics(
        rows_loaded=rows_loaded,
        rows_usable=int(len(work)),
        event_rows=int(len(event_only)),
        unique_event_decisions=int(event_only["decision_id"].nunique()) if not event_only.empty else 0,
        multi_event_decisions=int(work["event_count"].gt(1).sum()),
        explicit_breakout_rows=explicit["explicit_breakout_rows"],
        explicit_sweep_rows=explicit["explicit_sweep_rows"],
        explicit_volatility_rows=explicit["explicit_volatility_rows"],
        breakout_rows=explicit["breakout_rows"],
        mean_reversion_rows=explicit["mean_reversion_rows"],
        volatility_expansion_rows=explicit["volatility_expansion_rows"],
        regime_transition_rows=explicit["regime_transition_rows"],
        liquidity_sweep_rows=explicit["liquidity_sweep_rows"],
        schema_mode=explicit["schema_mode"],
        unavailable_event_families=explicit["unavailable_event_families"],
    )
    return event_only, diagnostics


def event_overlap_table(event_rows: pd.DataFrame) -> pd.DataFrame:
    if event_rows is None or event_rows.empty:
        return pd.DataFrame(columns=["event_a", "event_b", "overlap_count"])
    records: Dict[Tuple[str, str], int] = {}
    for value in event_rows["event_types"]:
        try:
            events = sorted(set(json.loads(value)))
        except Exception:
            events = []
        for i, first in enumerate(events):
            for second in events[i:]:
                key = (first, second)
                records[key] = records.get(key, 0) + 1
    return pd.DataFrame(
        [{"event_a": a, "event_b": b, "overlap_count": count} for (a, b), count in sorted(records.items())]
    )
