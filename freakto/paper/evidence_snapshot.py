"""Atomic, secret-free evidence snapshots for the frozen Paper campaign."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class EvidenceSource:
    relative_path: str
    required: bool = False


EVIDENCE_SOURCES: tuple[EvidenceSource, ...] = (
    EvidenceSource(".freakto-runtime/paper-campaign/state.json", required=True),
    EvidenceSource("config/paper_go_live_policy.json", required=True),
    EvidenceSource("logs/paper_launch_v2/cycle_history.jsonl"),
    EvidenceSource("logs/paper_launch_v2/last_cycle.json"),
    EvidenceSource("logs/paper_launch_v2/orchestrator_state.json"),
    EvidenceSource("logs/paper_launch_v2/heartbeat.json"),
    EvidenceSource("logs/paper_cycle/cycle_history.jsonl"),
    EvidenceSource("logs/paper_cycle/last_cycle.json"),
    EvidenceSource("logs/paper_cycle/orchestrator_state.json"),
    EvidenceSource("logs/paper_cycle/heartbeat.json"),
    EvidenceSource("logs/paper_trades.csv"),
    EvidenceSource("logs/paper_trade_evaluations.csv"),
    EvidenceSource("logs/paper_performance/paper_performance_summary.json"),
    EvidenceSource("logs/paper_performance/paper_performance_dashboard.md"),
    EvidenceSource("logs/paper_performance/paper_performance_ledger.csv"),
    EvidenceSource("logs/paper_performance/paper_performance_by_regime.csv"),
    EvidenceSource("logs/paper_performance/paper_equity_curve.csv"),
)


class EvidenceSnapshotError(RuntimeError):
    """Raised when a trustworthy snapshot cannot be created."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _safe_archive_name(relative_path: str) -> str:
    normalized = PurePosixPath(relative_path.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise EvidenceSnapshotError(f"Unsafe evidence path: {relative_path}")
    return normalized.as_posix()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def create_evidence_snapshot(
    root: str | Path,
    *,
    output_dir: str | Path | None = None,
    generated_at: datetime | None = None,
    sources: Iterable[EvidenceSource] = EVIDENCE_SOURCES,
) -> dict:
    """Copy allowlisted evidence into one atomic ZIP with an internal hash manifest."""
    workspace = Path(root).resolve()
    destination = (
        Path(output_dir).resolve()
        if output_dir is not None
        else workspace / ".freakto-runtime" / "campaign-backups"
    )
    now = generated_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)

    included: list[tuple[EvidenceSource, str, bytes]] = []
    missing: list[str] = []
    missing_required: list[str] = []
    for source in tuple(sources):
        archive_name = _safe_archive_name(source.relative_path)
        candidate = (workspace / Path(*PurePosixPath(archive_name).parts)).resolve()
        try:
            candidate.relative_to(workspace)
        except ValueError as exc:
            raise EvidenceSnapshotError(f"Evidence path escapes workspace: {archive_name}") from exc
        if not candidate.is_file():
            missing.append(archive_name)
            if source.required:
                missing_required.append(archive_name)
            continue
        included.append((source, archive_name, candidate.read_bytes()))

    if missing_required:
        raise EvidenceSnapshotError(
            "Required campaign evidence is missing: " + ", ".join(missing_required)
        )

    state_payload = next(
        payload for _, name, payload in included if name.endswith("paper-campaign/state.json")
    )
    try:
        campaign_id = str(json.loads(state_payload).get("campaign_id") or "unknown")
    except (UnicodeDecodeError, json.JSONDecodeError, AttributeError) as exc:
        raise EvidenceSnapshotError("Campaign state is not valid JSON") from exc

    safe_campaign_id = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in campaign_id
    ) or "unknown"
    stamp = now.strftime("%Y%m%dT%H%M%S.%fZ")
    archive_path = destination / f"{safe_campaign_id}-evidence-{stamp}.zip"
    checksum_path = archive_path.with_suffix(".zip.sha256")
    if archive_path.exists() or checksum_path.exists():
        raise EvidenceSnapshotError(f"Snapshot destination already exists: {archive_path.name}")

    manifest = {
        "schema_version": 1,
        "campaign_id": campaign_id,
        "generated_utc": now.isoformat(),
        "evidence_scope": "PAPER_CAMPAIGN_AUDIT_ONLY",
        "contains_secrets": False,
        "files": [
            {
                "path": name,
                "required": source.required,
                "size_bytes": len(payload),
                "sha256": _sha256(payload),
            }
            for source, name, payload in included
        ],
        "missing_optional": missing,
    }

    destination.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{archive_path.name}.", suffix=".tmp", dir=destination
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            for _, name, payload in included:
                archive.writestr(name, payload)
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
            )
        os.replace(temporary, archive_path)
    finally:
        temporary.unlink(missing_ok=True)

    archive_sha256 = _sha256(archive_path.read_bytes())
    _atomic_write(checksum_path, f"{archive_sha256}  {archive_path.name}\n".encode("ascii"))
    return {
        "status": "SNAPSHOT_CREATED",
        "archive": str(archive_path),
        "checksum_file": str(checksum_path),
        "archive_sha256": archive_sha256,
        "campaign_id": campaign_id,
        "included_files": len(included),
        "missing_optional": missing,
        "manifest": manifest,
        "live_orders_enabled": False,
        "real_capital_enabled": False,
        "allocation_pct": 0.0,
    }


__all__ = [
    "EVIDENCE_SOURCES",
    "EvidenceSnapshotError",
    "EvidenceSource",
    "create_evidence_snapshot",
]
