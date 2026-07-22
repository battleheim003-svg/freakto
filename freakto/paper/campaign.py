"""Persistent manager for the frozen 60-day zero-capital Paper campaign."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import ctypes
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

from freakto.core import PAPER_SAFETY


ROOT = Path(__file__).resolve().parents[2]
ACTIVE = {"STARTING", "RUNNING", "STOP_REQUESTED"}
ORCHESTRATOR_DIR = Path("logs") / "paper_cycle"


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def read_state(path: Path) -> dict[str, Any]:
    return _json(path)


def _pid_alive(pid: Any) -> bool:
    try:
        process_id = int(pid)
    except (TypeError, ValueError):
        return False
    if process_id <= 0:
        return False
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
            return ctypes.get_last_error() == 5
        try:
            return kernel32.WaitForSingleObject(handle, 0) == 0x00000102
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(process_id, 0)
    except OSError:
        return False
    return True


def run_cli(arguments: Sequence[str], *, root: Path = ROOT, timeout: int = 900) -> CommandResult:
    command = (sys.executable, "-X", "utf8", "-m", "freakto.cli", *arguments)
    environment = os.environ.copy()
    environment.update({"LIVE_TRADING_ENABLED": "false", "REAL_CAPITAL_ENABLED": "false", "PYTHONUTF8": "1"})
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
        return CommandResult(command, 124, exc.stdout or "", (exc.stderr or "") + f"\nTimed out after {timeout} seconds.", True)
    return CommandResult(command, completed.returncode, completed.stdout, completed.stderr)


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
    frozen = {"policy_version": policy.get("policy_version"), "frozen_contract": policy.get("frozen_contract"), "thresholds": policy.get("thresholds")}
    encoded = json.dumps(frozen, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return frozen, hashlib.sha256(encoded).hexdigest()


def _history(root: Path, started: datetime) -> list[dict[str, Any]]:
    path = root / "logs" / "paper_launch_v2" / "cycle_history.jsonl"
    rows = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        try:
            row = json.loads(line)
            stamp = datetime.fromisoformat(str(row.get("started_utc", "")).replace("Z", "+00:00"))
        except (json.JSONDecodeError, TypeError, ValueError):
            continue
        if stamp.astimezone(timezone.utc) >= started:
            rows.append(row)
    return rows


def campaign_status(root: Path = ROOT, *, now: datetime | None = None) -> dict[str, Any]:
    state = read_state(state_path(root))
    if not state:
        return {"status": "NOT_STARTED", "elapsed_days": 0.0, "closed_trades": 0, "minimum_days": 60, "minimum_closed_trades": 200, **PAPER_SAFETY.payload()}
    heartbeat = _json(root / ORCHESTRATOR_DIR / "heartbeat.json")
    heartbeat_pid = heartbeat.get("pid")
    if (
        state.get("status") in ACTIVE | {"INTERRUPTED"}
        and heartbeat_pid is not None
        and heartbeat.get("status") != "STOPPED"
        and _pid_alive(heartbeat_pid)
    ):
        state.update(status="RUNNING", pid=int(heartbeat_pid), error=None, recovered_from_heartbeat=True)
        write_state(state_path(root), state)
    if state.get("status") in ACTIVE and not _pid_alive(state.get("pid")):
        terminal = "STOPPED" if state.get("status") == "STOP_REQUESTED" else "INTERRUPTED"
        state.update(status=terminal, stopped_utc=utc_now())
        write_state(state_path(root), state)
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    started = datetime.fromisoformat(state["started_utc"].replace("Z", "+00:00")).astimezone(timezone.utc)
    elapsed = max(0.0, (current - started).total_seconds() / 86400.0)
    policy = _json(root / "config" / "paper_go_live_policy.json")
    thresholds = policy.get("thresholds") or {}
    minimum_days = int(thresholds.get("minimum_observation_days", 60))
    minimum_trades = int(thresholds.get("minimum_closed_trades", 200))
    summary = _json(root / "logs" / "paper_performance" / "paper_performance_summary.json")
    closed = int(summary.get("closed_trades", 0) or 0)
    history = _history(root, started)
    successful = sum(row.get("status") == "COMPLETE" for row in history)
    state.update(
        elapsed_days=round(elapsed, 4),
        target_end_utc=(started + timedelta(days=minimum_days)).isoformat(),
        minimum_days=minimum_days,
        closed_trades=closed,
        minimum_closed_trades=minimum_trades,
        cycles=len(history),
        successful_cycles=successful,
        failed_cycles=len(history) - successful,
        cycle_success_rate=round(successful / len(history), 6) if history else 0.0,
        evidence_window_complete=elapsed >= minimum_days and closed >= minimum_trades,
        **PAPER_SAFETY.payload(),
    )
    write_state(state_path(root), state)
    return state


def start_campaign(root: Path = ROOT) -> dict[str, Any]:
    existing = campaign_status(root)
    if existing.get("status") in ACTIVE:
        raise RuntimeError(f"Paper campaign already active: pid={existing.get('pid')}")
    preflight = run_cli(("paper", "preflight"), root=root)
    if preflight.exit_code != 0:
        raise RuntimeError(f"Paper preflight blocked campaign start: exit={preflight.exit_code}")
    arm = run_cli(("paper", "arm-research"), root=root)
    if arm.exit_code != 0:
        raise RuntimeError(f"Research arming blocked campaign start: exit={arm.exit_code}")
    directory = campaign_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    stop_flag = root / ORCHESTRATOR_DIR / "campaign_stop.flag"
    stop_flag.unlink(missing_ok=True)
    frozen, contract_hash = _contract(root)
    previous = read_state(state_path(root))
    started = previous.get("started_utc") if previous.get("status") in {"STOPPED", "INTERRUPTED"} else utc_now()
    state = {
        "schema_version": 1,
        "campaign_id": previous.get("campaign_id") or f"paper-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        "status": "STARTING",
        "started_utc": started,
        "resumed_utc": utc_now() if previous else None,
        "stopped_utc": None,
        "pid": None,
        "contract_sha256": contract_hash,
        "frozen_policy": frozen,
        **PAPER_SAFETY.payload(),
    }
    write_state(state_path(root), state)
    environment = os.environ.copy()
    environment.update({"LIVE_TRADING_ENABLED": "false", "REAL_CAPITAL_ENABLED": "false", "PYTHONUTF8": "1"})
    try:
        with (directory / "campaign.stdout.log").open("a", encoding="utf-8") as stdout, (directory / "campaign.stderr.log").open("a", encoding="utf-8") as stderr:
            process = subprocess.Popen(
                [sys.executable, "-X", "utf8", "-m", "freakto.paper.orchestrator", "--loop", "--no-immediate"],
                cwd=root,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                creationflags=0,
            )
    except OSError as exc:
        state.update(status="FAILED", stopped_utc=utc_now(), error=f"Campaign launch failed: {exc}")
        write_state(state_path(root), state)
        raise
    state.update(status="RUNNING", pid=process.pid)
    write_state(state_path(root), state)
    return campaign_status(root)


def stop_campaign(root: Path = ROOT) -> dict[str, Any]:
    state = campaign_status(root)
    if state.get("status") not in {"STARTING", "RUNNING"}:
        raise ValueError("Paper campaign is not running")
    output = root / ORCHESTRATOR_DIR
    output.mkdir(parents=True, exist_ok=True)
    (output / "campaign_stop.flag").write_text(utc_now(), encoding="utf-8")
    state.update(status="STOP_REQUESTED")
    write_state(state_path(root), state)
    return state
