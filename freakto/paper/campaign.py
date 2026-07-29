"""Persistent manager for the frozen 60-day zero-capital Paper campaign."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
import errno
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
from typing import Any, Sequence

from freakto.core import PAPER_SAFETY
from freakto.paper.cycle_contract import CYCLE_NETWORK_SKIPPED
from freakto.paper.state_paths import (
    CANONICAL_RELATIVE_DIR,
    atomic_write_json,
    paper_state_paths,
)
from engine.artifact_protocols import DEFAULT_ARTIFACT_SELECTOR, GLOBAL_UTC_SELECTOR
from engine.experiment_registry import ResearchGovernanceRegistry


ROOT = Path(__file__).resolve().parents[2]
ACTIVE = {"STARTING", "RUNNING", "STOP_REQUESTED"}
ORCHESTRATOR_DIR = CANONICAL_RELATIVE_DIR


class ProcessLiveness(str, Enum):
    ALIVE = "ALIVE"
    DEAD = "DEAD"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_aware_timestamp(value: Any) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Paper timestamp is naive and cannot be treated as UTC.")
    return parsed.astimezone(timezone.utc)


def write_state(path: Path, payload: dict[str, Any]) -> None:
    atomic_write_json(path, payload)


def read_state(path: Path) -> dict[str, Any]:
    return _json(path)


def _pid_liveness(pid: Any) -> ProcessLiveness:
    try:
        process_id = int(pid)
    except (TypeError, ValueError):
        return ProcessLiveness.DEAD
    if process_id <= 0:
        return ProcessLiveness.DEAD

    if os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel32.OpenProcess.restype = ctypes.c_void_p
        kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        kernel32.WaitForSingleObject.restype = ctypes.c_uint32
        kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel32.CloseHandle.restype = ctypes.c_int
        handle = kernel32.OpenProcess(0x00100000, False, process_id)
        if not handle:
            return (
                ProcessLiveness.UNKNOWN
                if ctypes.get_last_error() == 5
                else ProcessLiveness.DEAD
            )
        try:
            result = kernel32.WaitForSingleObject(handle, 0)
            if result == 0x00000102:
                return ProcessLiveness.ALIVE
            if result == 0:
                return ProcessLiveness.DEAD
            return ProcessLiveness.UNKNOWN
        finally:
            kernel32.CloseHandle(handle)

    try:
        os.kill(process_id, 0)
    except ProcessLookupError:
        return ProcessLiveness.DEAD
    except PermissionError:
        return ProcessLiveness.UNKNOWN
    except OSError as exc:
        if exc.errno == errno.ESRCH:
            return ProcessLiveness.DEAD
        if exc.errno == errno.EPERM:
            return ProcessLiveness.UNKNOWN
        return ProcessLiveness.UNKNOWN
    return ProcessLiveness.ALIVE


def _pid_alive(pid: Any) -> bool:
    """Compatibility wrapper for older callers and tests."""
    return _pid_liveness(pid) is ProcessLiveness.ALIVE


def run_cli(
    arguments: Sequence[str],
    *,
    root: Path = ROOT,
    timeout: int = 900,
) -> CommandResult:
    command = (sys.executable, "-X", "utf8", "-m", "freakto.cli", *arguments)
    environment = os.environ.copy()
    environment.update(
        {
            "LIVE_TRADING_ENABLED": "false",
            "REAL_CAPITAL_ENABLED": "false",
            "PYTHONUTF8": "1",
        }
    )
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command,
            124,
            exc.stdout or "",
            (exc.stderr or "") + f"\nTimed out after {timeout} seconds.",
            True,
        )
    return CommandResult(
        command,
        completed.returncode,
        completed.stdout,
        completed.stderr,
    )


def campaign_dir(root: Path = ROOT) -> Path:
    return root / ".freakto-runtime" / "paper-campaign"


def state_path(root: Path = ROOT) -> Path:
    return campaign_dir(root) / "state.json"


def _json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _contract(root: Path) -> tuple[dict[str, Any], str]:
    policy = _json(root / "config" / "paper_go_live_policy.json")
    frozen = {
        "policy_version": policy.get("policy_version"),
        "frozen_contract": policy.get("frozen_contract"),
        "thresholds": policy.get("thresholds"),
    }
    encoded = json.dumps(
        frozen,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return frozen, hashlib.sha256(encoded).hexdigest()


def _history(
    root: Path,
    started: datetime,
) -> tuple[list[dict[str, Any]], str, str | None]:
    resolution = paper_state_paths(root).resolve_for_read("cycle_history.jsonl")
    rows = []
    try:
        lines = resolution.path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows, resolution.source, resolution.warning
    for line in lines:
        try:
            row = json.loads(line)
            stamp = _parse_aware_timestamp(row.get("started_utc"))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if stamp >= started:
            rows.append(row)
    return rows, resolution.source, resolution.warning


def _heartbeat(root: Path) -> tuple[dict[str, Any], str, str | None]:
    resolution = paper_state_paths(root).resolve_for_read("heartbeat.json")
    return _json(resolution.path), resolution.source, resolution.warning


def _verified_worker_identity(
    state: dict[str, Any],
    heartbeat: dict[str, Any],
) -> bool:
    expected_identity = state.get("worker_identity_sha256")
    if not expected_identity:
        return False
    return bool(
        heartbeat.get("worker_identity_sha256") == expected_identity
        and int(heartbeat.get("pid") or 0) == int(state.get("pid") or 0)
        and heartbeat.get("worker_host") == state.get("worker_host")
    )


def _recover_process_state(
    state: dict[str, Any],
    heartbeat: dict[str, Any],
) -> None:
    status = str(state.get("status") or "")
    if status not in {"RUNNING", "INTERRUPTED", "STOP_REQUESTED"}:
        return

    local_host = socket.gethostname()
    state_host = state.get("worker_host")
    if state_host and state_host != local_host:
        state.update(
            process_liveness=ProcessLiveness.UNKNOWN.value,
            process_identity="REMOTE_HOST_UNVERIFIED",
        )
        return

    liveness = _pid_liveness(state.get("pid"))
    if status == "RUNNING" and liveness is ProcessLiveness.DEAD:
        recovered_at = utc_now()
        state.update(
            previous_status="RUNNING",
            status="STALE_RECOVERED",
            recovery_reason="STALE_PROCESS_NOT_FOUND",
            recovered_at_utc=recovered_at,
            stopped_utc=recovered_at,
            stale_pid=state.get("pid"),
            last_heartbeat_utc=heartbeat.get("now_utc")
            or heartbeat.get("stopped_utc"),
            process_liveness=ProcessLiveness.DEAD.value,
            process_identity="NOT_FOUND",
        )
        return

    if status == "STOP_REQUESTED" and liveness is ProcessLiveness.DEAD:
        state.update(
            previous_status="STOP_REQUESTED",
            status="STOPPED",
            stopped_utc=utc_now(),
            process_liveness=ProcessLiveness.DEAD.value,
        )
        return

    verified = (
        liveness is ProcessLiveness.ALIVE
        and _verified_worker_identity(state, heartbeat)
    )
    if status == "INTERRUPTED" and verified:
        state.update(
            previous_status="INTERRUPTED",
            status="RUNNING",
            error=None,
            recovered_from_heartbeat=True,
            recovered_at_utc=utc_now(),
            process_liveness=ProcessLiveness.ALIVE.value,
            process_identity="VERIFIED",
        )
        return

    if liveness is ProcessLiveness.UNKNOWN or (
        liveness is ProcessLiveness.ALIVE and not verified
    ):
        state.update(
            process_liveness=ProcessLiveness.UNKNOWN.value,
            process_identity="UNVERIFIED",
        )
    else:
        state.update(
            process_liveness=liveness.value,
            process_identity="VERIFIED" if verified else "NOT_APPLICABLE",
        )


def campaign_status(
    root: Path = ROOT,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    state = read_state(state_path(root))
    if not state:
        return {
            "status": "NOT_STARTED",
            "elapsed_days": 0.0,
            "closed_trades": 0,
            "minimum_days": 60,
            "minimum_closed_trades": 200,
            **PAPER_SAFETY.payload(),
        }

    heartbeat, heartbeat_source, heartbeat_warning = _heartbeat(root)
    _recover_process_state(state, heartbeat)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    try:
        started = _parse_aware_timestamp(state["started_utc"])
    except (KeyError, TypeError, ValueError):
        state.update(
            previous_status=state.get("status"),
            status="ABORTED",
            recovery_reason="INVALID_STARTED_TIMESTAMP",
            recovered_at_utc=utc_now(),
        )
        write_state(state_path(root), state)
        return state

    elapsed = max(0.0, (current - started).total_seconds() / 86400.0)
    policy = _json(root / "config" / "paper_go_live_policy.json")
    thresholds = policy.get("thresholds") or {}
    minimum_days = int(thresholds.get("minimum_observation_days", 60))
    minimum_trades = int(thresholds.get("minimum_closed_trades", 200))
    summary = _json(
        root / "logs" / "paper_performance" / "paper_performance_summary.json"
    )
    closed = int(summary.get("closed_trades", 0) or 0)
    history, history_source, history_warning = _history(root, started)
    successful = sum(
        row.get("status")
        in {"COMPLETE", "COMPLETE_WITH_MAINTENANCE_WARNINGS"}
        for row in history
    )
    network_skipped = sum(
        row.get("status") == CYCLE_NETWORK_SKIPPED for row in history
    )
    failed = len(history) - successful - network_skipped
    evaluated_cycles = successful + failed
    warnings = [
        warning
        for warning in (heartbeat_warning, history_warning)
        if warning
    ]
    state.update(
        elapsed_days=round(elapsed, 4),
        target_end_utc=(started + timedelta(days=minimum_days)).isoformat(),
        minimum_days=minimum_days,
        closed_trades=closed,
        minimum_closed_trades=minimum_trades,
        cycles=len(history),
        successful_cycles=successful,
        network_skipped_cycles=network_skipped,
        failed_cycles=failed,
        cycle_success_rate=(
            round(successful / evaluated_cycles, 6) if evaluated_cycles else 0.0
        ),
        evidence_window_complete=elapsed >= minimum_days
        and closed >= minimum_trades,
        persistence_source=history_source,
        heartbeat_source=heartbeat_source,
        persistence_warnings=warnings,
        **PAPER_SAFETY.payload(),
    )
    write_state(state_path(root), state)
    return state


def start_campaign(
    root: Path = ROOT,
    *,
    artifact_selector: str = DEFAULT_ARTIFACT_SELECTOR,
    experiment_id: str = "",
    governance_path: str | Path | None = None,
) -> dict[str, Any]:
    if artifact_selector == GLOBAL_UTC_SELECTOR or experiment_id:
        registry = (
            ResearchGovernanceRegistry(governance_path)
            if governance_path
            else ResearchGovernanceRegistry()
        )
        try:
            registry.require_promotion_eligible(
                experiment_id=experiment_id,
                artifact_selector=artifact_selector,
            )
        except ValueError as exc:
            raise RuntimeError(str(exc)) from exc
    existing = campaign_status(root)
    if existing.get("status") in ACTIVE:
        raise RuntimeError(
            f"Paper campaign already active: pid={existing.get('pid')}"
        )
    preflight = run_cli(("paper", "preflight"), root=root)
    if preflight.exit_code != 0:
        details = []
        try:
            payload = json.loads(preflight.stdout)
        except (TypeError, json.JSONDecodeError):
            payload = {}
        if isinstance(payload, dict):
            details = [str(item) for item in payload.get("blockers") or []]
        suffix = f": {'; '.join(details)}" if details else ""
        raise RuntimeError(
            f"Paper preflight blocked campaign start: exit={preflight.exit_code}{suffix}"
        )
    arm = run_cli(("paper", "arm-research"), root=root)
    if arm.exit_code != 0:
        raise RuntimeError(
            f"Research arming blocked campaign start: exit={arm.exit_code}"
        )

    directory = campaign_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    paths = paper_state_paths(root)
    stop_flag = paths.canonical("campaign_stop.flag")
    stop_flag.unlink(missing_ok=True)
    frozen, contract_hash = _contract(root)
    previous = read_state(state_path(root))
    resumable = {"STOPPED", "INTERRUPTED", "STALE_RECOVERED", "ABORTED"}
    started = (
        previous.get("started_utc")
        if previous.get("status") in resumable
        else utc_now()
    )
    worker_token = secrets.token_urlsafe(32)
    worker_identity = hashlib.sha256(worker_token.encode("utf-8")).hexdigest()
    worker_host = socket.gethostname()
    state = {
        "schema_version": 2,
        "campaign_id": previous.get("campaign_id")
        or f"paper-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "status": "STARTING",
        "started_utc": started,
        "resumed_utc": utc_now() if previous else None,
        "stopped_utc": None,
        "pid": None,
        "worker_host": worker_host,
        "worker_identity_sha256": worker_identity,
        "contract_sha256": contract_hash,
        "frozen_policy": frozen,
        **PAPER_SAFETY.payload(),
    }
    write_state(state_path(root), state)
    environment = os.environ.copy()
    environment.update(
        {
            "LIVE_TRADING_ENABLED": "false",
            "REAL_CAPITAL_ENABLED": "false",
            "PYTHONUTF8": "1",
            "FREAKTO_CAMPAIGN_WORKER_TOKEN": worker_token,
        }
    )
    try:
        with (
            (directory / "campaign.stdout.log").open(
                "a",
                encoding="utf-8",
            ) as stdout,
            (directory / "campaign.stderr.log").open(
                "a",
                encoding="utf-8",
            ) as stderr,
        ):
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "-m",
                    "freakto.paper.orchestrator",
                    "--loop",
                    "--no-immediate",
                ],
                cwd=root,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                creationflags=0,
            )
    except OSError as exc:
        state.update(
            status="FAILED",
            stopped_utc=utc_now(),
            error=f"Campaign launch failed: {exc}",
        )
        write_state(state_path(root), state)
        raise
    state.update(
        status="RUNNING",
        pid=process.pid,
        launched_at_utc=utc_now(),
    )
    write_state(state_path(root), state)
    return campaign_status(root)


def stop_campaign(root: Path = ROOT) -> dict[str, Any]:
    state = campaign_status(root)
    if state.get("status") not in {"STARTING", "RUNNING"}:
        raise ValueError("Paper campaign is not running")
    output = paper_state_paths(root).canonical_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "campaign_stop.flag").write_text(utc_now(), encoding="utf-8")
    state.update(status="STOP_REQUESTED")
    write_state(state_path(root), state)
    return state


__all__ = [
    "ACTIVE",
    "CommandResult",
    "ORCHESTRATOR_DIR",
    "ProcessLiveness",
    "campaign_dir",
    "campaign_status",
    "read_state",
    "run_cli",
    "start_campaign",
    "state_path",
    "stop_campaign",
    "utc_now",
    "write_state",
]
