"""Causal OHLCV quality, freshness, cadence, and source-divergence gates."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from freakto.technical_v2.contracts import DataQualityAssessment


TIMEFRAME_SECONDS = {"1m": 60, "3m": 180, "5m": 300, "15m": 900, "1h": 3600, "4h": 14400, "1d": 86400}


def assess_data_quality(
    frame: pd.DataFrame,
    *,
    timeframe: str,
    now: datetime | None = None,
    require_fresh: bool = False,
    reference_close: float | None = None,
    maximum_source_divergence_bps: float = 35,
) -> DataQualityAssessment:
    reasons: list[str] = []
    rows = len(frame)
    timestamps = pd.to_datetime(frame.get("timestamp"), utc=True, errors="coerce") if "timestamp" in frame else pd.Series(dtype="datetime64[ns, UTC]")
    duplicate_count = int(timestamps.duplicated().sum()) if len(timestamps) else 0
    if duplicate_count:
        reasons.append("DUPLICATE_TIMESTAMPS")
    invalid_timestamps = int(timestamps.isna().sum()) if len(timestamps) else rows
    if invalid_timestamps:
        reasons.append("INVALID_TIMESTAMPS")
    cadence = TIMEFRAME_SECONDS.get(timeframe)
    missing = 0
    if cadence and len(timestamps.dropna()) > 1:
        deltas = timestamps.sort_values().diff().dt.total_seconds().dropna()
        missing = int(sum(max(0, round(delta / cadence) - 1) for delta in deltas if delta > cadence * 1.5))
        if missing:
            reasons.append("MISSING_CANDLES")
    numeric = frame[[name for name in ("open", "high", "low", "close") if name in frame]].apply(pd.to_numeric, errors="coerce")
    if numeric.empty or numeric.isna().any().any():
        reasons.append("INVALID_OHLC")
    elif ((numeric["high"] < numeric["low"]) | (numeric["close"] <= 0)).any():
        reasons.append("INVALID_PRICE_GEOMETRY")
    returns = pd.to_numeric(frame.get("close"), errors="coerce").pct_change()
    median = returns.rolling(30).median()
    mad = (returns - median).abs().rolling(30).median().replace(0, 1e-12)
    robust_z = (returns - median).abs() / (1.4826 * mad)
    outliers = int((robust_z > 12).sum())
    if outliers:
        reasons.append("PRICE_OUTLIERS")
    latest = timestamps.dropna().max() if len(timestamps) else None
    freshness = None
    if latest is not None and pd.notna(latest):
        current = now or datetime.now(timezone.utc)
        freshness = max(0.0, (current - latest.to_pydatetime()).total_seconds())
        if require_fresh and cadence and freshness > cadence * 3:
            reasons.append("STALE_DATA")
    divergence = None
    if reference_close is not None and rows and float(reference_close) > 0:
        latest_close = float(pd.to_numeric(frame["close"], errors="coerce").iloc[-1])
        divergence = abs(latest_close - float(reference_close)) / float(reference_close) * 10_000
        if divergence > maximum_source_divergence_bps:
            reasons.append("SOURCE_DIVERGENCE")
    fatal = {"INVALID_TIMESTAMPS", "INVALID_OHLC", "INVALID_PRICE_GEOMETRY", "STALE_DATA", "SOURCE_DIVERGENCE"}
    status = "FAIL" if fatal.intersection(reasons) else "WARN" if reasons else "PASS"
    penalty = duplicate_count * 2 + missing * 0.5 + outliers * 2 + invalid_timestamps * 5
    score = max(0.0, min(1.0, 1.0 - penalty / max(rows, 1)))
    return DataQualityAssessment(
        status=status,
        score=round(score, 4),
        rows=rows,
        latest_timestamp=None if latest is None or pd.isna(latest) else latest.isoformat(),
        freshness_seconds=None if freshness is None else round(freshness, 2),
        missing_candles=missing,
        duplicate_timestamps=duplicate_count,
        outlier_candles=outliers,
        source_divergence_bps=None if divergence is None else round(divergence, 3),
        reasons=tuple(dict.fromkeys(reasons)),
    )


def aggregate_quality(reports: dict[str, DataQualityAssessment]) -> DataQualityAssessment:
    if not reports:
        raise ValueError("At least one quality report is required")
    worst = "FAIL" if any(item.status == "FAIL" for item in reports.values()) else "WARN" if any(item.status == "WARN" for item in reports.values()) else "PASS"
    reasons = tuple(f"{timeframe}:{reason}" for timeframe, report in reports.items() for reason in report.reasons)
    latest_report = next(iter(reports.values()))
    divergences = [item.source_divergence_bps for item in reports.values() if item.source_divergence_bps is not None]
    return DataQualityAssessment(
        status=worst,
        score=round(min(item.score for item in reports.values()), 4),
        rows=sum(item.rows for item in reports.values()),
        latest_timestamp=latest_report.latest_timestamp,
        freshness_seconds=latest_report.freshness_seconds,
        missing_candles=sum(item.missing_candles for item in reports.values()),
        duplicate_timestamps=sum(item.duplicate_timestamps for item in reports.values()),
        outlier_candles=sum(item.outlier_candles for item in reports.values()),
        source_divergence_bps=max(divergences) if divergences else None,
        reasons=reasons,
    )
