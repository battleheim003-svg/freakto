"""Persistent, zero-capital automation schedules for the Control Center."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from freakto.ui.control_center_state import ROOT
from freakto.ui.job_manager import ACTIVE, list_jobs, pid_alive, start_quick_job, start_workflow_job


AUTOMATION_DEFINITIONS = {
    "daily_data_replay": {
        "title": "Data & Replay",
        "kind": "DATA_REPLAY",
        "default_interval_hours": 24,
        "description": "Build data, validate the cache, and run compact Replay.",
    },
    "forward_shadow": {
        "title": "Forward & Shadow",
        "kind": "FORWARD_SHADOW_CYCLE",
        "default_interval_hours": 4,
        "description": "Run Preflight, Research arm, one Paper cycle, and Forward reports.",
    },
    "report_refresh": {
        "title": "Reports",
        "kind": "REPORT_REFRESH",
        "default_interval_hours": 12,
        "description": "Refresh Paper, Research, Forward, and readiness reports.",
    },
    "airdrop_outcomes": {
        "title": "Airdrop outcomes",
        "kind": "AIRDROP_OUTCOMES",
        "default_interval_hours": 24,
        "description": "Synchronize resolved outcomes and rebuild the research report.",
    },
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def runtime_dir(root: Path = ROOT) -> Path:
    return root / ".freakto-runtime" / "control-center" / "automation"


def config_path(root: Path = ROOT) -> Path:
    return runtime_dir(root) / "schedules.json"


def scheduler_path(root: Path = ROOT) -> Path:
    return runtime_dir(root) / "scheduler.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _default_config() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "items": {
            key: {
                "enabled": False,
                "interval_hours": definition["default_interval_hours"],
                "last_started_utc": None,
                "next_run_utc": None,
                "last_job_id": None,
            }
            for key, definition in AUTOMATION_DEFINITIONS.items()
        },
    }


def load_config(root: Path = ROOT) -> dict[str, Any]:
    stored = _read_json(config_path(root))
    config = _default_config()
    for key, value in dict(stored.get("items") or {}).items():
        if key in config["items"] and isinstance(value, dict):
            config["items"][key].update(value)
    return config


def list_automations(root: Path = ROOT) -> list[dict[str, Any]]:
    config = load_config(root)
    return [
        {"id": key, **definition, **config["items"][key]}
        for key, definition in AUTOMATION_DEFINITIONS.items()
    ]


def set_automation(
    automation_id: str,
    *,
    enabled: bool,
    interval_hours: int,
    root: Path = ROOT,
) -> dict[str, Any]:
    if automation_id not in AUTOMATION_DEFINITIONS:
        raise ValueError("Unknown automation")
    interval = int(interval_hours)
    if not 1 <= interval <= 720:
        raise ValueError("Automation interval must be between 1 and 720 hours")
    config = load_config(root)
    item = config["items"][automation_id]
    was_enabled = bool(item.get("enabled"))
    item.update(enabled=bool(enabled), interval_hours=interval)
    if enabled and (not was_enabled or not item.get("next_run_utc")):
        item["next_run_utc"] = (utc_now() + timedelta(hours=interval)).isoformat()
    if not enabled:
        item["next_run_utc"] = None
    _write_json(config_path(root), config)
    return {"id": automation_id, **AUTOMATION_DEFINITIONS[automation_id], **item}


def _launch(automation_id: str, *, root: Path) -> dict[str, Any]:
    definition = AUTOMATION_DEFINITIONS[automation_id]
    if definition["kind"] == "QUICK_START":
        return start_quick_job(full=True, root=root)
    return start_workflow_job(str(definition["kind"]), root=root)


def run_automation_now(automation_id: str, *, root: Path = ROOT) -> dict[str, Any]:
    if automation_id not in AUTOMATION_DEFINITIONS:
        raise ValueError("Unknown automation")
    job = _launch(automation_id, root=root)
    config = load_config(root)
    item = config["items"][automation_id]
    started = utc_now()
    item.update(
        last_started_utc=started.isoformat(),
        last_job_id=job.get("job_id"),
        next_run_utc=(started + timedelta(hours=int(item["interval_hours"]))).isoformat()
        if item.get("enabled")
        else None,
    )
    _write_json(config_path(root), config)
    return job


def run_due_automations(*, root: Path = ROOT) -> dict[str, Any] | None:
    if any(job.get("status") in ACTIVE for job in list_jobs(root)):
        return None
    now = utc_now()
    for item in list_automations(root):
        if not item.get("enabled") or not item.get("next_run_utc"):
            continue
        try:
            due = datetime.fromisoformat(str(item["next_run_utc"]))
        except ValueError:
            due = now
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if due <= now:
            return run_automation_now(str(item["id"]), root=root)
    return None


def scheduler_status(root: Path = ROOT) -> dict[str, Any]:
    state = _read_json(scheduler_path(root))
    if state.get("status") == "RUNNING" and not pid_alive(state.get("pid")):
        state.update(status="STOPPED", ended_utc=utc_now().isoformat(), error="Scheduler process is no longer running.")
        _write_json(scheduler_path(root), state)
    return state


def ensure_scheduler_running(root: Path = ROOT) -> dict[str, Any]:
    enabled = any(item.get("enabled") for item in list_automations(root))
    current = scheduler_status(root)
    if not enabled or current.get("status") == "RUNNING":
        return current
    directory = runtime_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update({"LIVE_TRADING_ENABLED": "false", "REAL_CAPITAL_ENABLED": "false", "PYTHONUTF8": "1"})
    with (directory / "scheduler.stdout.log").open("a", encoding="utf-8") as stdout, (directory / "scheduler.stderr.log").open("a", encoding="utf-8") as stderr:
        process = subprocess.Popen(
            [sys.executable, "-X", "utf8", "-m", "freakto.ui.automation_runner", "--root", str(root)],
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    state = {
        "schema_version": 1,
        "status": "RUNNING",
        "pid": process.pid,
        "started_utc": utc_now().isoformat(),
        "heartbeat_utc": utc_now().isoformat(),
        "ended_utc": None,
        "error": None,
    }
    _write_json(scheduler_path(root), state)
    return state


def write_scheduler_state(payload: dict[str, Any], *, root: Path = ROOT) -> None:
    _write_json(scheduler_path(root), payload)
