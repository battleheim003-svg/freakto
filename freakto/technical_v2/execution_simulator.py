"""Deterministic volatility/liquidity-aware paper execution estimator."""

from __future__ import annotations

from freakto.technical_v2.contracts import ExecutionAssessment


def estimate_execution(
    entry_price: float,
    side: str,
    *,
    spread_bps: float = 2.0,
    base_slippage_bps: float = 5.0,
    volatility_percentile: float = 0.5,
    relative_volume: float = 1.0,
    latency_ms: int = 500,
    order_notional_usdt: float = 250.0,
    estimated_depth_usdt: float = 50_000.0,
) -> ExecutionAssessment:
    volatility_penalty = max(0.0, volatility_percentile - 0.5) * 12
    liquidity_penalty = max(0.0, 1.0 - relative_volume) * 8
    impact_bps = min(25.0, order_notional_usdt / max(estimated_depth_usdt, 1.0) * 10_000 * 0.08)
    slippage = base_slippage_bps + volatility_penalty + liquidity_penalty + impact_bps
    latency_bps = min(12.0, max(0, latency_ms) / 1000 * (1 + volatility_percentile * 2))
    one_way = spread_bps / 2 + slippage + latency_bps
    direction = 1 if side.upper() == "LONG" else -1
    effective_entry = entry_price * (1 + direction * one_way / 10_000)
    fill_ratio = max(0.5, min(1.0, estimated_depth_usdt / max(order_notional_usdt * 20, 1.0)))
    warnings = []
    if slippage >= 15:
        warnings.append("HIGH_ESTIMATED_SLIPPAGE")
    if fill_ratio < 1:
        warnings.append("PARTIAL_FILL_EXPECTED")
    return ExecutionAssessment(
        entry_price=round(entry_price, 10),
        effective_entry_price=round(effective_entry, 10),
        spread_bps=round(spread_bps, 3),
        slippage_bps=round(slippage, 3),
        latency_bps=round(latency_bps, 3),
        fill_ratio=round(fill_ratio, 4),
        estimated_round_trip_cost_pct=round((spread_bps + 2 * slippage + 2 * latency_bps) / 100, 4),
        warnings=tuple(warnings),
    )
