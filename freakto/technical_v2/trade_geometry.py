"""Volatility-aware entry, invalidation, stop and target geometry."""

from __future__ import annotations

import pandas as pd

from freakto.technical_v2.contracts import TradeGeometry
from freakto.technical_v2.features import atr_series, validate_frame


def build_trade_geometry(
    frame: pd.DataFrame,
    side: str,
    *,
    stop_atr: float = 1.3,
    target_atr: float = 2.2,
    fee_bps_per_side: float = 10,
    slippage_bps: float = 5,
    expiry_bars: int = 12,
) -> TradeGeometry:
    data = validate_frame(frame)
    entry = float(data["close"].iloc[-1])
    atr = max(float(atr_series(data).iloc[-1]), entry * 0.0005)
    direction = 1 if side.upper() == "LONG" else -1
    stop = entry - direction * atr * stop_atr
    target = entry + direction * atr * target_atr
    risk = abs(entry - stop)
    reward = abs(target - entry)
    round_trip_cost = entry * (2 * fee_bps_per_side + 2 * slippage_bps) / 10_000
    raw_rr = reward / max(risk, 1e-12)
    adjusted_rr = max(0.0, reward - round_trip_cost) / max(risk + round_trip_cost, 1e-12)
    return TradeGeometry(
        entry=round(entry, 10),
        stop=round(stop, 10),
        target=round(target, 10),
        invalidation=round(stop, 10),
        stop_distance_pct=round(risk / entry * 100, 4),
        reward_risk=round(raw_rr, 4),
        cost_adjusted_reward_risk=round(adjusted_rr, 4),
        expiry_bars=max(1, int(expiry_bars)),
    )
