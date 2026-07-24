"""Read-only validation for OHLCV frames entering Freakto research workflows.

This module deliberately does not import the legacy engine.  It documents and
checks the boundary that new providers must satisfy without changing, wrapping,
or silently repairing the existing replay implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

OHLCV_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume")
PRICE_COLUMNS = ("open", "high", "low", "close")
TIMEFRAME_MILLISECONDS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
    "1w": 604_800_000,
}


@dataclass(frozen=True)
class ContractIssue:
    code: str
    severity: str
    message: str
    rows: int = 0


@dataclass(frozen=True)
class ContractReport:
    status: str
    rows: int
    valid_rows: int
    timeframe: str
    first_timestamp_utc: str | None
    last_timestamp_utc: str | None
    issues: tuple[ContractIssue, ...]

    @property
    def ok(self) -> bool:
        return self.status == "PASSED"


def _issue(
    issues: list[ContractIssue],
    code: str,
    severity: str,
    message: str,
    rows: int = 0,
) -> None:
    issues.append(ContractIssue(code, severity, message, int(rows)))


def _timestamps(values: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(values):
        return pd.to_datetime(values, unit="ms", utc=True, errors="coerce")
    return pd.to_datetime(values, utc=True, errors="coerce")


def inspect_ohlcv(
    frame: pd.DataFrame | None,
    timeframe: str,
    *,
    now: datetime | None = None,
    require_closed: bool = True,
) -> ContractReport:
    """Inspect a frame without mutating or repairing it.

    Errors mean the frame must not cross the adapter boundary. Warnings retain
    useful provenance (for example zero volume in decentralized FX candles)
    without pretending that the value has exchange-volume semantics.
    """
    issues: list[ContractIssue] = []
    rows = 0 if frame is None else len(frame)
    timeframe_ms = TIMEFRAME_MILLISECONDS.get(str(timeframe).strip().lower())
    if timeframe_ms is None:
        _issue(
            issues,
            "UNSUPPORTED_TIMEFRAME",
            "ERROR",
            f"Unsupported timeframe: {timeframe}",
        )

    if frame is None:
        _issue(issues, "FRAME_MISSING", "ERROR", "OHLCV frame is None.")
        return ContractReport("FAILED", 0, 0, timeframe, None, None, tuple(issues))
    if frame.empty:
        _issue(issues, "FRAME_EMPTY", "ERROR", "OHLCV frame has no rows.")
        return ContractReport("FAILED", 0, 0, timeframe, None, None, tuple(issues))

    missing = [column for column in OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        _issue(
            issues,
            "MISSING_COLUMNS",
            "ERROR",
            "Missing required columns: " + ", ".join(missing),
        )
        return ContractReport("FAILED", rows, 0, timeframe, None, None, tuple(issues))

    timestamps = _timestamps(frame["timestamp"])
    invalid_timestamps = int(timestamps.isna().sum())
    if invalid_timestamps:
        _issue(
            issues,
            "INVALID_TIMESTAMP",
            "ERROR",
            "Timestamps must be epoch milliseconds or UTC-parseable values.",
            invalid_timestamps,
        )

    numeric = frame.loc[:, [*PRICE_COLUMNS, "volume"]].apply(
        pd.to_numeric, errors="coerce"
    )
    invalid_numeric_mask = numeric.isna().any(axis=1) | ~np.isfinite(numeric).all(axis=1)
    invalid_numeric = int(invalid_numeric_mask.sum())
    if invalid_numeric:
        _issue(
            issues,
            "INVALID_NUMERIC_VALUE",
            "ERROR",
            "OHLCV values must be finite numeric values.",
            invalid_numeric,
        )

    duplicate_count = int(timestamps.duplicated(keep=False).sum())
    if duplicate_count:
        _issue(
            issues,
            "DUPLICATE_TIMESTAMP",
            "ERROR",
            "Each symbol/timeframe dataset must contain one row per bar-open timestamp.",
            duplicate_count,
        )
    if not timestamps.dropna().is_monotonic_increasing:
        _issue(
            issues,
            "NON_MONOTONIC_TIMESTAMP",
            "ERROR",
            "Rows must be ordered by ascending bar-open timestamp.",
        )

    nonpositive_prices = int((numeric.loc[:, PRICE_COLUMNS] <= 0).any(axis=1).sum())
    if nonpositive_prices:
        _issue(
            issues,
            "NONPOSITIVE_PRICE",
            "ERROR",
            "Open, high, low, and close must be greater than zero.",
            nonpositive_prices,
        )
    negative_volume = int((numeric["volume"] < 0).sum())
    if negative_volume:
        _issue(
            issues,
            "NEGATIVE_VOLUME",
            "ERROR",
            "Volume cannot be negative.",
            negative_volume,
        )
    zero_volume = int((numeric["volume"] == 0).sum())
    if zero_volume:
        _issue(
            issues,
            "ZERO_VOLUME",
            "WARNING",
            "Zero volume is allowed but its semantics must be declared by the adapter.",
            zero_volume,
        )

    invalid_ohlc = (
        (numeric["high"] < numeric.loc[:, PRICE_COLUMNS].max(axis=1))
        | (numeric["low"] > numeric.loc[:, PRICE_COLUMNS].min(axis=1))
    )
    invalid_ohlc_count = int(invalid_ohlc.sum())
    if invalid_ohlc_count:
        _issue(
            issues,
            "INVALID_OHLC_GEOMETRY",
            "ERROR",
            "High must be the row maximum and low must be the row minimum.",
            invalid_ohlc_count,
        )

    valid_timestamps = timestamps.dropna()
    if timeframe_ms is not None and not valid_timestamps.empty:
        epoch_ms = valid_timestamps.astype("int64") // 1_000_000
        misaligned = int((epoch_ms % timeframe_ms != 0).sum())
        if misaligned:
            _issue(
                issues,
                "MISALIGNED_BAR_OPEN",
                "ERROR",
                "Timestamps must identify UTC-aligned bar-open times.",
                misaligned,
            )
        if require_closed:
            cutoff = pd.Timestamp(now or datetime.now(timezone.utc))
            if cutoff.tzinfo is None:
                cutoff = cutoff.tz_localize("UTC")
            else:
                cutoff = cutoff.tz_convert("UTC")
            incomplete = int(
                ((valid_timestamps + pd.to_timedelta(timeframe_ms, unit="ms")) > cutoff).sum()
            )
            if incomplete:
                _issue(
                    issues,
                    "INCOMPLETE_CANDLE",
                    "ERROR",
                    "Only candles whose full interval has closed may enter replay.",
                    incomplete,
                )

    error_rows = pd.Series(False, index=frame.index)
    error_rows |= timestamps.isna()
    error_rows |= invalid_numeric_mask
    error_rows |= timestamps.duplicated(keep=False)
    error_rows |= (numeric.loc[:, PRICE_COLUMNS] <= 0).any(axis=1)
    error_rows |= numeric["volume"] < 0
    error_rows |= invalid_ohlc
    status = "FAILED" if any(issue.severity == "ERROR" for issue in issues) else "PASSED"
    return ContractReport(
        status=status,
        rows=rows,
        valid_rows=int((~error_rows).sum()),
        timeframe=timeframe,
        first_timestamp_utc=(
            valid_timestamps.iloc[0].isoformat() if not valid_timestamps.empty else None
        ),
        last_timestamp_utc=(
            valid_timestamps.iloc[-1].isoformat() if not valid_timestamps.empty else None
        ),
        issues=tuple(issues),
    )
