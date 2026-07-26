"""Causal triple-barrier labels with conservative intrabar ambiguity handling."""

from __future__ import annotations

import pandas as pd


def evaluate_triple_barrier(
    future: pd.DataFrame,
    *,
    side: str,
    stop: float,
    target: float,
    maximum_bars: int,
    ambiguous_policy: str = "STOP_FIRST",
) -> dict[str, object]:
    if ambiguous_policy not in {"STOP_FIRST", "TARGET_FIRST", "AMBIGUOUS"}:
        raise ValueError("Unknown ambiguous barrier policy")
    direction = side.upper()
    rows = future.head(max(1, int(maximum_bars)))
    for offset, (_, row) in enumerate(rows.iterrows(), start=1):
        opened = float(row.get("open", row["close"]))
        high, low = float(row["high"]), float(row["low"])
        if direction == "LONG" and opened <= stop:
            return {"label": "STOP", "bars": offset, "exit_price": opened, "intrabar_ambiguous": False, "gap": True}
        if direction == "SHORT" and opened >= stop:
            return {"label": "STOP", "bars": offset, "exit_price": opened, "intrabar_ambiguous": False, "gap": True}
        if direction == "LONG" and opened >= target:
            return {"label": "TARGET", "bars": offset, "exit_price": target, "intrabar_ambiguous": False, "gap": True}
        if direction == "SHORT" and opened <= target:
            return {"label": "TARGET", "bars": offset, "exit_price": target, "intrabar_ambiguous": False, "gap": True}
        stop_hit = low <= stop if direction == "LONG" else high >= stop
        target_hit = high >= target if direction == "LONG" else low <= target
        if stop_hit and target_hit:
            if ambiguous_policy == "AMBIGUOUS":
                return {"label": "AMBIGUOUS", "bars": offset, "exit_price": None}
            label = "STOP" if ambiguous_policy == "STOP_FIRST" else "TARGET"
            return {"label": label, "bars": offset, "exit_price": stop if label == "STOP" else target, "intrabar_ambiguous": True}
        if stop_hit:
            return {"label": "STOP", "bars": offset, "exit_price": stop, "intrabar_ambiguous": False}
        if target_hit:
            return {"label": "TARGET", "bars": offset, "exit_price": target, "intrabar_ambiguous": False}
    exit_price = float(rows.iloc[-1]["close"]) if len(rows) else None
    return {"label": "TIME", "bars": len(rows), "exit_price": exit_price, "intrabar_ambiguous": False, "gap": False}
