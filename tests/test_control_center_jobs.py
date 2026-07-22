from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from freakto.ui import control_center_worker as worker
from freakto.ui import job_manager
from freakto.ui.control_center_state import CommandResult

ROOT = Path(__file__).parents[1]

def initial_state(job_id="job-1", full=False):
    return {
        "schema_version": 1,
        "job_id": job_id,
        "kind": "QUICK_START",
        "status": "QUEUED",
        "full": full,
        "created_utc": job_manager.utc_now(),
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


def prepare_job(tmp_path: Path, state=None):
    directory = job_manager.jobs_dir(tmp_path) / (state or {}).get("job_id", "job-1")
    path = directory / "state.json"
    job_manager.write_state(path, state or initial_state())
    return path


def test_worker_completes_pipeline_and_accepts_review_block(monkeypatch, tmp_path):
    path = prepare_job(tmp_path)

    def fake_run(arguments, **kwargs):
        code = 2 if arguments == ("paper", "go-live-check") else 0
        return CommandResult(("python", *arguments), code, "ok", "")

    monkeypatch.setattr(worker, "run_cli", fake_run)
    assert worker.run_job(path, tmp_path) == 0
    state = job_manager.read_state(path)
    assert state["status"] == "SUCCEEDED"
    assert state["completed_steps"] == state["total_steps"] == 9
    assert state["steps"][-1]["exit_code"] == 2
    assert state["steps"][-1]["accepted"] is True
    assert (path.parent / "pipeline.log").is_file()


def test_worker_stops_on_first_unexpected_failure(monkeypatch, tmp_path):
    path = prepare_job(tmp_path)

    def fake_run(arguments, **kwargs):
        code = 7 if arguments == ("paper", "preflight") else 0
        return CommandResult(("python", *arguments), code, "", "failed")

    monkeypatch.setattr(worker, "run_cli", fake_run)
    assert worker.run_job(path, tmp_path) == 7
    state = job_manager.read_state(path)
    assert state["status"] == "FAILED"
    assert state["steps"][-1]["key"] == "paper_preflight"
    assert "exited with 7" in state["error"]


def test_worker_honors_cancel_before_next_step(monkeypatch, tmp_path):
    path = prepare_job(tmp_path)
    (path.parent / "cancel.requested").write_text("now", encoding="utf-8")
    monkeypatch.setattr(worker, "run_cli", lambda *args, **kwargs: pytest.fail("must not run"))
    assert worker.run_job(path, tmp_path) == 3
    assert job_manager.read_state(path)["status"] == "CANCELLED"


def test_cancel_request_is_persistent(monkeypatch, tmp_path):
    state = initial_state()
    state.update(status="RUNNING", pid=123)
    path = prepare_job(tmp_path, state)
    monkeypatch.setattr(job_manager, "_pid_alive", lambda pid: True)
    requested = job_manager.request_cancel("job-1", root=tmp_path)
    assert requested["status"] == "CANCEL_REQUESTED"
    assert (path.parent / "cancel.requested").is_file()


def test_start_job_is_detached_and_forces_safe_environment(monkeypatch, tmp_path):
    called = {}

    class Process:
        pid = 4321

    def fake_popen(command, **kwargs):
        called.update(command=command, kwargs=kwargs)
        return Process()

    monkeypatch.setattr(job_manager.subprocess, "Popen", fake_popen)
    state = job_manager.start_quick_job(full=False, root=tmp_path)
    assert state["pid"] == 4321
    assert called["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"
    assert called["kwargs"]["env"]["REAL_CAPITAL_ENABLED"] == "false"
    assert "freakto.ui.control_center_worker" in called["command"]


def test_second_active_job_is_rejected(monkeypatch, tmp_path):
    state = initial_state()
    state.update(status="QUEUED")
    prepare_job(tmp_path, state)
    with pytest.raises(RuntimeError, match="Active job"):
        job_manager.start_quick_job(full=True, root=tmp_path)


def test_pid_probe_handles_invalid_values_without_oserror():
    assert job_manager._pid_alive(None) is False
    assert job_manager._pid_alive(-1) is False
    assert job_manager._pid_alive(os.getpid()) is True


@pytest.mark.skipif(os.name != "nt", reason="Windows regression")
def test_windows_pid_probe_does_not_use_signal_zero(monkeypatch):
    monkeypatch.setattr(job_manager.os, "kill", lambda *args: pytest.fail("os.kill must not be used on Windows"))
    assert job_manager._pid_alive(os.getpid()) is True


def test_worker_module_runs_in_a_real_child_process_and_honors_cancel(tmp_path):
    path = prepare_job(tmp_path)
    (path.parent / "cancel.requested").write_text("now", encoding="utf-8")
    completed = subprocess.run(
        [sys.executable, "-m", "freakto.ui.control_center_worker", "--state", str(path), "--root", str(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 3
    assert job_manager.read_state(path)["status"] == "CANCELLED"
