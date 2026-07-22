"""Causal execution assumptions shared by replay and paper evaluation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

from engine.model_contract import EXECUTION_MODEL_VERSION


@dataclass(frozen=True)
class ExecutionCost:
    fee_bps_per_side: float
    slippage_bps_per_side: float
    round_trip_cost_pct: float
    volatility_multiplier: float
    liquidity_multiplier: float
    model_version: str = EXECUTION_MODEL_VERSION


def _number(value: Any, default: float) -> float:
    try:
        parsed = float(value)
        return default if not math.isfinite(parsed) else parsed
    except (TypeError, ValueError):
        return default


def estimate_execution_cost(
    row: Mapping[str, Any],
    *,
    fee_bps_per_side: float,
    base_slippage_bps_per_side: float,
    dynamic: bool = True,
    max_slippage_bps_per_side: float = 100.0,
) -> ExecutionCost:
    """Estimate cost using information available at decision time only.

    ATR and trailing/cross-exchange volume ratio are causal inputs.  The model
    is deliberately conservative and bounded; missing liquidity never improves
    the base assumption.
    """
    fee = max(0.0, _number(fee_bps_per_side, 0.0))
    base = max(0.0, _number(base_slippage_bps_per_side, 0.0))
    if dynamic:
        atr_pct = max(0.0, _number(row.get("atr_pct"), 0.0))
        # 1% ATR keeps the base; 4% ATR approximately doubles it.
        volatility_multiplier = min(4.0, max(1.0, 1.0 + max(0.0, atr_pct - 0.01) * 33.3333))
        volume_ratio = _number(row.get("cross_exchange_volume_ratio"), 1.0)
        # A ratio below one indicates thinner-than-reference liquidity.
        liquidity_multiplier = min(3.0, max(1.0, 1.0 / max(0.33, volume_ratio)))
    else:
        volatility_multiplier = 1.0
        liquidity_multiplier = 1.0
    slippage = min(
        max(0.0, _number(max_slippage_bps_per_side, 100.0)),
        base * volatility_multiplier * liquidity_multiplier,
    )
    round_trip_pct = 2.0 * (fee + slippage) / 100.0
    return ExecutionCost(
        fee_bps_per_side=round(fee, 6),
        slippage_bps_per_side=round(slippage, 6),
        round_trip_cost_pct=round(round_trip_pct, 8),
        volatility_multiplier=round(volatility_multiplier, 6),
        liquidity_multiplier=round(liquidity_multiplier, 6),
    )


def adaptive_horizon(base_horizon: int, regime_label: str) -> int:
    base = max(1, int(base_horizon))
    regime = str(regime_label or "").upper()
    if regime.startswith("TRENDING"):
        return base * 2
    if regime in {"SIDEWAYS", "VOLATILE"}:
        return max(1, int(round(base * 0.5)))
    return base

