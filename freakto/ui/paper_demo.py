"""Read-only Paper demo state and presentation helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from typing import Any

from freakto.paper.campaign import state_path
from freakto.paper.cycle_contract import CYCLE_NETWORK_SKIPPED
from freakto.paper.state_paths import paper_state_paths


@dataclass(frozen=True)
class StatusPresentation:
    label: str
    severity: str
    icon: str
    description: str


STATUS_PRESENTATIONS = {
    "NOT_STARTED": StatusPresentation("Not started", "neutral", "○", "No Paper campaign state exists."),
    "STARTING": StatusPresentation("Starting", "info", "◌", "The Paper worker is starting."),
    "RUNNING": StatusPresentation("Running", "info", "●", "The Paper campaign is active."),
    "STOP_REQUESTED": StatusPresentation("Stop requested", "warning", "◌", "A graceful stop is pending."),
    "STOPPED": StatusPresentation("Stopped", "neutral", "■", "The Paper campaign is stopped."),
    "STALE_RECOVERED": StatusPresentation("Stale worker recovered", "warning", "⚠", "A dead worker was recovered safely."),
    "INTERRUPTED": StatusPresentation("Interrupted", "warning", "⚠", "The previous worker was interrupted."),
    "ABORTED": StatusPresentation("Aborted", "error", "✕", "The campaign was aborted safely."),
    "FAILED": StatusPresentation("Failed", "error", "✕", "The campaign failed."),
    "COMPLETE": StatusPresentation("Complete", "success", "✓", "The cycle completed."),
    "COMPLETE_WITH_MAINTENANCE_WARNINGS": StatusPresentation(
        "Complete with warnings", "warning", "⚠", "The cycle completed with maintenance warnings."
    ),
    "COMPLETE_WITH_STEP_FAILURES": StatusPresentation(
        "Completed with step failures", "error", "✕", "One or more cycle steps failed."
    ),
    CYCLE_NETWORK_SKIPPED: StatusPresentation(
        "Skipped: network unavailable",
        "warning",
        "⚠",
        "All usable market-data providers failed; this is not a strategy result.",
    ),
}


def status_presentation(value: object) -> StatusPresentation:
    raw = str(value or "UNKNOWN").strip().upper()
    return STATUS_PRESENTATIONS.get(
        raw,
        StatusPresentation(
            f"Unknown status: {raw}",
            "neutral",
            "?",
            "This status is not recognized by the current dashboard.",
        ),
    )


def validate_refresh_seconds(value: object, *, default: int = 10) -> int:
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        seconds = default
    return max(5, min(60, seconds))


def _read_object(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, None
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"Could not read {path.name}: {type(exc).__name__}"
    if not isinstance(payload, dict):
        return {}, f"Invalid object in {path.name}"
    return payload, None


def _parse_utc(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def format_utc(value: object) -> str:
    parsed = _parse_utc(value)
    if parsed is None:
        return "Unavailable"
    return parsed.isoformat().replace("+00:00", "Z")


def _history_summary(path: Path, *, started: datetime | None) -> dict[str, Any]:
    total = successful = failed = network_skipped = 0
    latest: dict[str, Any] = {}
    try:
        handle = path.open("r", encoding="utf-8")
    except OSError:
        return {
            "cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "network_skipped_cycles": 0,
            "latest_cycle": {},
        }
    with handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            row_started = _parse_utc(row.get("started_utc"))
            if started is not None and (row_started is None or row_started < started):
                continue
            total += 1
            latest = row
            status = str(row.get("status") or "")
            if status in {"COMPLETE", "COMPLETE_WITH_MAINTENANCE_WARNINGS"}:
                successful += 1
            elif status == CYCLE_NETWORK_SKIPPED:
                network_skipped += 1
            else:
                failed += 1
    return {
        "cycles": total,
        "successful_cycles": successful,
        "failed_cycles": failed,
        "network_skipped_cycles": network_skipped,
        "latest_cycle": latest,
    }


def _health(
    status: str,
    latest_status: str,
    age_seconds: float | None,
    heartbeat_status: str = "",
) -> str:
    if status in {"FAILED", "ABORTED"} or latest_status == "COMPLETE_WITH_STEP_FAILURES":
        return "FAILED"
    if status == "STALE_RECOVERED":
        return "RECOVERED_STALE_WORKER"
    if latest_status == CYCLE_NETWORK_SKIPPED:
        return "DEGRADED_NETWORK"
    if (
        not latest_status
        and heartbeat_status == "WAITING_FOR_NEXT_CANDLE"
        and status == "NOT_STARTED"
    ):
        return "WAITING_FOR_FIRST_SCHEDULED_CYCLE"
    if age_seconds is not None and age_seconds > 6 * 60 * 60:
        return "STALE"
    if status == "NOT_STARTED":
        return "NO_DATA_YET"
    if status in {"RUNNING", "STARTING", "STOPPED", "STOP_REQUESTED"}:
        return "HEALTHY"
    return "UNKNOWN"


def collect_paper_demo_snapshot(
    root: Path,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Build a bounded, read-only view of campaign and canonical Paper artifacts."""
    root = Path(root).resolve()
    paths = paper_state_paths(root)
    campaign, campaign_warning = _read_object(state_path(root))
    heartbeat_resolution = paths.resolve_for_read("heartbeat.json")
    history_resolution = paths.resolve_for_read("cycle_history.jsonl")
    heartbeat, heartbeat_error = _read_object(heartbeat_resolution.path)
    started = _parse_utc(campaign.get("started_utc"))
    history = _history_summary(history_resolution.path, started=started)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    policy, _ = _read_object(root / "config" / "paper_go_live_policy.json")
    thresholds = policy.get("thresholds") if isinstance(policy.get("thresholds"), dict) else {}
    performance, _ = _read_object(
        root / "logs" / "paper_performance" / "paper_performance_summary.json"
    )
    minimum_days = int(thresholds.get("minimum_observation_days", 60) or 60)
    minimum_closed_trades = int(thresholds.get("minimum_closed_trades", 200) or 200)
    elapsed_days = (
        max(0.0, (current - started).total_seconds() / 86400.0)
        if started is not None
        else 0.0
    )
    heartbeat_at = _parse_utc(
        heartbeat.get("now_utc")
        or heartbeat.get("heartbeat_utc")
        or heartbeat.get("stopped_utc")
    )
    age_seconds = (
        max(0.0, (current - heartbeat_at).total_seconds())
        if heartbeat_at is not None
        else None
    )
    campaign_status = str(campaign.get("status") or "NOT_STARTED").upper()
    heartbeat_status = str(heartbeat.get("status") or "").upper()
    latest = history["latest_cycle"]
    latest_status = str(latest.get("status") or "").upper()
    warnings = [
        item
        for item in (
            campaign_warning,
            heartbeat_error,
            heartbeat_resolution.warning,
            history_resolution.warning,
        )
        if item
    ]
    presentation = status_presentation(campaign_status)
    latest_presentation = status_presentation(latest_status) if latest_status else None
    return {
        **campaign,
        **{key: value for key, value in history.items() if key != "latest_cycle"},
        "status": campaign_status,
        "elapsed_days": round(elapsed_days, 4),
        "target_end_utc": (
            (started + timedelta(days=minimum_days)).isoformat()
            if started is not None
            else None
        ),
        "minimum_days": minimum_days,
        "closed_trades": int(performance.get("closed_trades", 0) or 0),
        "minimum_closed_trades": minimum_closed_trades,
        "status_presentation": asdict(presentation),
        "latest_cycle": latest,
        "latest_cycle_presentation": asdict(latest_presentation) if latest_presentation else None,
        "health": _health(
            campaign_status,
            latest_status,
            age_seconds,
            heartbeat_status,
        ),
        "worker_status": heartbeat_status or "NOT_RUNNING",
        "heartbeat_utc": format_utc(
            heartbeat.get("now_utc")
            or heartbeat.get("heartbeat_utc")
            or heartbeat.get("stopped_utc")
        ),
        "last_cycle_utc": format_utc(
            latest.get("finished_utc") or latest.get("started_utc")
        ),
        "state_age_seconds": round(age_seconds, 3) if age_seconds is not None else None,
        "persistence_source": history_resolution.source,
        "heartbeat_source": heartbeat_resolution.source,
        "canonical_state_dir": str(paths.canonical_dir),
        "warnings": warnings,
    }


__all__ = [
    "STATUS_PRESENTATIONS",
    "StatusPresentation",
    "collect_paper_demo_snapshot",
    "format_utc",
    "status_presentation",
    "validate_refresh_seconds",
]
