"""External compatibility audit for unchanged legacy replay consumers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from freakto.market_data import inspect_ohlcv
from freakto.market_data.contract import TIMEFRAME_MILLISECONDS
from freakto.markets.config import MarketConfig


@dataclass(frozen=True)
class CompatibilityReport:
    status: str
    schema_ready: bool
    evidence_replay_ready: bool
    rows: int
    unexpected_gap_count: int
    zero_volume_rows: int
    session_audit_status: str
    cost_audit_status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def audit_replay_compatibility(
    frame: pd.DataFrame,
    *,
    timeframe: str,
    config: MarketConfig,
    min_rows: int = 120,
) -> CompatibilityReport:
    """Audit known cross-asset assumptions without calling or changing replay."""
    contract = inspect_ohlcv(frame, timeframe, require_closed=False)
    blockers = [
        f"DATA_CONTRACT:{issue.code}"
        for issue in contract.issues
        if issue.severity == "ERROR"
    ]
    warnings = [
        f"DATA_CONTRACT:{issue.code}"
        for issue in contract.issues
        if issue.severity == "WARNING"
    ]
    if len(frame) < max(1, int(min_rows)):
        blockers.append(f"INSUFFICIENT_SAMPLE:{len(frame)}<{max(1, int(min_rows))}")
    cost_audit_status = str(
        frame.attrs.get("cost_audit_status", config.cost_model_status)
    ).upper()
    session_audit_status = str(
        frame.attrs.get("session_audit_status", "UNVERIFIED")
    ).upper()
    if cost_audit_status not in {"AUDITED", "AUDITED_EXCLUDING_ROLLOVER"}:
        blockers.append("EXECUTION_COST_MODEL_UNVERIFIED")
    if cost_audit_status == "AUDITED_EXCLUDING_ROLLOVER":
        blockers.append("ROLLOVER_NOT_MODELED")
    if session_audit_status != "PASSED":
        blockers.append("SESSION_CALENDAR_UNVERIFIED")

    zero_volume = 0
    if "volume" in frame:
        volume = pd.to_numeric(frame["volume"], errors="coerce")
        zero_volume = int(volume.eq(0).sum())
        if len(volume) and (volume.fillna(0) == 0).all():
            blockers.append("VOLUME_SIGNAL_UNAVAILABLE")
        elif zero_volume:
            warnings.append(f"ZERO_VOLUME_ROWS:{zero_volume}")

    gap_count = 0
    timeframe_ms = TIMEFRAME_MILLISECONDS.get(str(timeframe).strip().lower())
    if timeframe_ms and "timestamp" in frame:
        timestamps = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        diffs = timestamps.sort_values().diff().dropna().dt.total_seconds().mul(1000)
        raw_gap_count = int((diffs > timeframe_ms).sum())
        gap_count = (
            int(frame.attrs.get("session_unexplained_gap_count", raw_gap_count))
            if session_audit_status == "PASSED"
            else raw_gap_count
        )
        if gap_count:
            warnings.append(
                f"RAW_TIME_GAPS:{gap_count}:classify_with_audited_session_calendar"
            )
        elif raw_gap_count:
            warnings.append(f"SESSION_GAPS_EXPLAINED:{raw_gap_count}")

    schema_ready = contract.ok
    evidence_ready = schema_ready and not blockers
    status = "REPLAY_EVIDENCE_CANDIDATE" if evidence_ready else "RESEARCH_DATA_ONLY"
    return CompatibilityReport(
        status=status,
        schema_ready=schema_ready,
        evidence_replay_ready=evidence_ready,
        rows=len(frame),
        unexpected_gap_count=gap_count,
        zero_volume_rows=zero_volume,
        session_audit_status=session_audit_status,
        cost_audit_status=cost_audit_status,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
    )
