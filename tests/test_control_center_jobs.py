from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from freakto.ui import control_center_worker as worker
from freakto.ui import job_manager
from freakto.ui import automation
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


def test_market_workflow_job_is_validated_and_persisted(monkeypatch, tmp_path):
    called = {}

    class Process:
        pid = 8765

    monkeypatch.setattr(
        job_manager.subprocess,
        "Popen",
        lambda command, **kwargs: called.update(command=command, kwargs=kwargs) or Process(),
    )
    state = job_manager.start_workflow_job(
        "MARKET_DATA_AUDIT",
        options={"start": "2023-01-01", "end": "2026-01-01"},
        root=tmp_path,
    )
    assert state["kind"] == "MARKET_DATA_AUDIT"
    assert state["options"]["start"] == "2023-01-01"
    assert state["pid"] == 8765
    assert called["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"


def test_data_and_report_workflows_are_fixed_and_zero_capital(tmp_path):
    data_plan = worker.workflow_plan("DATA_REPLAY", root=tmp_path)
    report_plan = worker.workflow_plan("REPORT_REFRESH", root=tmp_path)
    assert [step.key for step in data_plan] == ["data_status", "data_build", "replay_status", "replay_run"]
    assert [step.key for step in report_plan] == ["paper_report", "research_report", "forward_report", "go_live_check"]
    assert all("live" not in step.arguments for step in (*data_plan, *report_plan))


def test_automation_schedule_is_persisted_disabled_by_default(tmp_path):
    items = automation.list_automations(tmp_path)
    assert items
    assert all(item["enabled"] is False for item in items)
    updated = automation.set_automation("forward_shadow", enabled=True, interval_hours=6, root=tmp_path)
    assert updated["enabled"] is True
    assert updated["interval_hours"] == 6
    assert updated["next_run_utc"]


def test_due_automation_respects_single_active_job(monkeypatch, tmp_path):
    automation.set_automation("report_refresh", enabled=True, interval_hours=1, root=tmp_path)
    config = automation.load_config(tmp_path)
    config["items"]["report_refresh"]["next_run_utc"] = "2020-01-01T00:00:00+00:00"
    automation._write_json(automation.config_path(tmp_path), config)
    monkeypatch.setattr(automation, "list_jobs", lambda root: [{"status": "RUNNING"}])
    monkeypatch.setattr(automation, "start_workflow_job", lambda *args, **kwargs: pytest.fail("must not launch"))
    assert automation.run_due_automations(root=tmp_path) is None


def test_due_automation_launches_allowlisted_workflow(monkeypatch, tmp_path):
    automation.set_automation("report_refresh", enabled=True, interval_hours=1, root=tmp_path)
    config = automation.load_config(tmp_path)
    config["items"]["report_refresh"]["next_run_utc"] = "2020-01-01T00:00:00+00:00"
    automation._write_json(automation.config_path(tmp_path), config)
    monkeypatch.setattr(automation, "list_jobs", lambda root: [])
    monkeypatch.setattr(automation, "start_workflow_job", lambda kind, root: {"job_id": "auto-1", "kind": kind})
    job = automation.run_due_automations(root=tmp_path)
    assert job == {"job_id": "auto-1", "kind": "REPORT_REFRESH"}
    stored = automation.load_config(tmp_path)["items"]["report_refresh"]
    assert stored["last_job_id"] == "auto-1"


def test_scheduler_launch_is_detached_and_forces_safe_environment(monkeypatch, tmp_path):
    automation.set_automation("forward_shadow", enabled=True, interval_hours=4, root=tmp_path)
    called = {}

    class Process:
        pid = 9911

    monkeypatch.setattr(
        automation.subprocess,
        "Popen",
        lambda command, **kwargs: called.update(command=command, kwargs=kwargs) or Process(),
    )
    state = automation.ensure_scheduler_running(tmp_path)
    assert state["status"] == "RUNNING"
    assert state["pid"] == 9911
    assert called["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"
    assert called["kwargs"]["env"]["REAL_CAPITAL_ENABLED"] == "false"
    assert "freakto.ui.automation_runner" in called["command"]


def test_cross_asset_inputs_cannot_escape_workspace(tmp_path):
    with pytest.raises(ValueError, match="workspace"):
        job_manager.start_workflow_job(
            "CROSS_ASSET_RANK",
            options={"input": str(tmp_path.parent / "outside.csv")},
            root=tmp_path,
        )


def test_worker_dispatches_allowlisted_script_steps(monkeypatch, tmp_path):
    state = initial_state(job_id="airdrop-1")
    state.update(kind="AIRDROP_OUTCOMES", options={})
    path = prepare_job(tmp_path, state)
    called = []

    def fake_script(arguments, **kwargs):
        called.append(tuple(arguments))
        code = 2 if arguments[-1] == "sync" else 0
        return CommandResult(("python", *arguments), code, "ok", "")

    monkeypatch.setattr(worker, "run_script", fake_script)
    monkeypatch.setattr(worker, "run_cli", lambda *args, **kwargs: pytest.fail("must use script runner"))
    assert worker.run_job(path, tmp_path) == 0
    assert called[0][-1] == "sync"
    assert called[1][-2:] == ("--min-resolved", "30")


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
