"""Market-data boundary rules used before feature computation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

import pandas as pd

from engine.historical_data_store import timeframe_to_milliseconds


def keep_closed_candles_only(
    frame: pd.DataFrame,
    timeframe: str,
    *,
    now: Optional[datetime] = None,
) -> Tuple[pd.DataFrame, int]:
    """Remove candles whose close time has not occurred yet.

    CCXT candle timestamps represent bar-open time. Using their evolving
    close/volume in a decision is lookahead relative to bar-close execution.
    """
    if frame is None or frame.empty or "timestamp" not in frame.columns:
        return frame.copy() if frame is not None else pd.DataFrame(), 0
    work = frame.copy()
    attrs = dict(getattr(frame, "attrs", {}))
    timestamps = pd.to_datetime(work["timestamp"], utc=True, errors="coerce")
    cutoff = pd.Timestamp(now or datetime.now(timezone.utc))
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    else:
        cutoff = cutoff.tz_convert("UTC")
    duration = pd.to_timedelta(timeframe_to_milliseconds(timeframe), unit="ms")
    closed = timestamps.notna() & ((timestamps + duration) <= cutoff)
    removed = int((~closed).sum())
    result = work.loc[closed].reset_index(drop=True)
    result.attrs.update(attrs)
    result.attrs["closed_candles_only"] = True
    result.attrs["incomplete_candles_removed"] = removed
    return result, removed
