"""Single conservative bar-by-bar outcome evaluator used by v2 evidence."""

from __future__ import annotations

from typing import Any, Iterable

EVALUATOR_VERSION = "event-ordered-v2"


def evaluate_path(decision: dict[str, Any], candles: Iterable[dict[str, Any]], *, horizon_candles: int, fee_bps_per_side: float = 10.0, slippage_bps_per_side: float = 5.0) -> dict[str, Any] | None:
    """Evaluate next-bar entry, first terminal hit, stop-first ambiguity, net costs.

    Candles must start with the first candle after the decision bar.
    """
    side = str(decision.get("side", "")).upper()
    if side not in {"LONG", "SHORT"}:
        return None
    future = list(candles)[: max(0, int(horizon_candles))]
    if not future:
        return None
    entry = float(future[0]["open"])
    stop = decision.get("stop_price")
    stop = float(stop) if stop not in (None, "") else None
    targets = [float(value) for value in decision.get("targets", []) if value not in (None, "")]
    target = targets[0] if targets else None
    cost = 2.0 * (max(0.0, float(fee_bps_per_side)) + max(0.0, float(slippage_bps_per_side))) / 100.0
    for offset, candle in enumerate(future, start=1):
        high, low = float(candle["high"]), float(candle["low"])
        if side == "LONG":
            stop_hit = stop is not None and low <= stop
            target_hit = target is not None and high >= target
        else:
            stop_hit = stop is not None and high >= stop
            target_hit = target is not None and low <= target
        if stop_hit or target_hit:
            # OHLC cannot order same-bar touches: always choose STOP.
            status = "STOP" if stop_hit else "TARGET"
            exit_price = stop if stop_hit else target
            gross = ((float(exit_price) - entry) / entry) * 100.0
            if side == "SHORT":
                gross *= -1.0
            return {
                "decision_id": decision["decision_id"], "evaluator_version": EVALUATOR_VERSION,
                "terminal_status": status, "terminal_candle_timestamp_utc": str(candle["timestamp"]),
                "terminal_offset": offset, "entry_price": round(entry, 10), "exit_price": round(float(exit_price), 10),
                "gross_return_pct": round(gross, 8), "cost_pct": round(cost, 8), "net_return_pct": round(gross - cost, 8),
                "intrabar_ambiguity": bool(stop_hit and target_hit),
            }
    close = float(future[-1]["close"])
    gross = ((close - entry) / entry) * 100.0
    if side == "SHORT":
        gross *= -1.0
    return {
        "decision_id": decision["decision_id"], "evaluator_version": EVALUATOR_VERSION,
        "terminal_status": "EXPIRED", "terminal_candle_timestamp_utc": str(future[-1]["timestamp"]),
        "terminal_offset": len(future), "entry_price": round(entry, 10), "exit_price": round(close, 10),
        "gross_return_pct": round(gross, 8), "cost_pct": round(cost, 8), "net_return_pct": round(gross - cost, 8),
        "intrabar_ambiguity": False,
    }
