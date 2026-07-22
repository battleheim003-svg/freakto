"""Persistent background-job manager for the local Control Center."""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from freakto.ui.control_center_state import ROOT


ACTIVE = {"QUEUED", "RUNNING", "CANCEL_REQUESTED"}
TERMINAL = {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def jobs_dir(root: Path = ROOT) -> Path:
    return root / ".freakto-runtime" / "control-center" / "jobs"


def write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def read_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _windows_pid_alive(pid: int) -> bool:
    """Query a Windows process without relying on unsupported signal 0."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel32.OpenProcess.restype = ctypes.c_void_p
    kernel32.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel32.WaitForSingleObject.restype = ctypes.c_uint32
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    synchronize = 0x00100000
    wait_timeout = 0x00000102
    handle = kernel32.OpenProcess(synchronize, False, pid)
    if not handle:
        # Access denied means a process exists but cannot be queried. Treating it
        # as alive is the safe choice because it prevents a concurrent job.
        return ctypes.get_last_error() == 5
    try:
        return kernel32.WaitForSingleObject(handle, 0) == wait_timeout
    finally:
        kernel32.CloseHandle(handle)


def _pid_alive(pid: Any) -> bool:
    try:
        process_id = int(pid)
    except (TypeError, ValueError):
        return False
    if process_id <= 0:
        return False
    if os.name == "nt":
        return _windows_pid_alive(process_id)
    try:
        os.kill(process_id, 0)
    except OSError:
        return False
    return True


def reconcile(path: Path) -> dict[str, Any]:
    state = read_state(path)
    if state.get("status") in {"RUNNING", "CANCEL_REQUESTED"} and not _pid_alive(state.get("pid")):
        state.update(status="INTERRUPTED", ended_utc=utc_now(), error="Background worker is no longer running.")
        write_state(path, state)
    return state


def list_jobs(root: Path = ROOT) -> list[dict[str, Any]]:
    directory = jobs_dir(root)
    if not directory.exists():
        return []
    jobs = [reconcile(path) for path in directory.glob("*/state.json")]
    return sorted((job for job in jobs if job), key=lambda row: row.get("created_utc", ""), reverse=True)


def start_quick_job(*, full: bool, root: Path = ROOT) -> dict[str, Any]:
    active = [job for job in list_jobs(root) if job.get("status") in ACTIVE]
    if active:
        raise RuntimeError(f"Active job already exists: {active[0].get('job_id')}")
    job_id = f"quick-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    directory = jobs_dir(root) / job_id
    state_path = directory / "state.json"
    state = {
        "schema_version": 1,
        "job_id": job_id,
        "kind": "QUICK_START",
        "status": "QUEUED",
        "full": bool(full),
        "created_utc": utc_now(),
        "started_utc": None,
        "ended_utc": None,
        "heartbeat_utc": None,
        "pid": None,
        "current_step": None,
        "completed_steps": 0,
        "total_steps": 0,
        "steps": [],
        "error": None,
    }
    write_state(state_path, state)
    environment = os.environ.copy()
    environment.update({"LIVE_TRADING_ENABLED": "false", "REAL_CAPITAL_ENABLED": "false", "PYTHONUTF8": "1"})
    directory.mkdir(parents=True, exist_ok=True)
    try:
        with (directory / "worker.stdout.log").open("a", encoding="utf-8") as stdout, (directory / "worker.stderr.log").open("a", encoding="utf-8") as stderr:
            process = subprocess.Popen(
                [sys.executable, "-X", "utf8", "-m", "freakto.ui.control_center_worker", "--state", str(state_path), "--root", str(root)],
                cwd=root,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
    except OSError as exc:
        state.update(status="FAILED", ended_utc=utc_now(), error=f"Worker launch failed: {exc}")
        write_state(state_path, state)
        raise
    latest = read_state(state_path) or state
    latest["pid"] = process.pid
    write_state(state_path, latest)
    return latest


def request_cancel(job_id: str, *, root: Path = ROOT) -> dict[str, Any]:
    directory = jobs_dir(root) / job_id
    state_path = directory / "state.json"
    state = reconcile(state_path)
    if not state or state.get("status") not in ACTIVE:
        raise ValueError("Only an active job can be cancelled")
    (directory / "cancel.requested").write_text(utc_now(), encoding="utf-8")
    state.update(status="CANCEL_REQUESTED", heartbeat_utc=utc_now())
    write_state(state_path, state)
    return state


def retry_job(job_id: str, *, root: Path = ROOT) -> dict[str, Any]:
    state = reconcile(jobs_dir(root) / job_id / "state.json")
    if not state or state.get("status") not in TERMINAL:
        raise ValueError("Only a terminal job can be retried")
    return start_quick_job(full=bool(state.get("full")), root=root)


def job_log(job_id: str, *, root: Path = ROOT, limit: int = 12000) -> str:
    path = jobs_dir(root) / job_id / "pipeline.log"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    return text[-limit:]
