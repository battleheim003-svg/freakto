from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

import pytest

from paper_research_orchestrator import (
    OrchestratorConfig,
    ProcessLock,
    cycle_commands,
    maintenance_commands,
    next_candle_run,
    run_step,
    should_run_maintenance,
)


class _Logger:
    def info(self, *_args, **_kwargs):
        pass

    def warning(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
        pass

    def exception(self, *_args, **_kwargs):
        pass


def test_next_candle_run_uses_utc_boundary_and_delay():
    now = datetime(2026, 7, 15, 9, 30, tzinfo=timezone.utc)
    scheduled = next_candle_run(now, timeframe_minutes=240, settle_delay_seconds=120)
    assert scheduled == datetime(2026, 7, 15, 12, 2, tzinfo=timezone.utc)


def test_next_candle_run_can_use_current_boundary_before_delay():
    now = datetime(2026, 7, 15, 12, 1, tzinfo=timezone.utc)
    scheduled = next_candle_run(now, timeframe_minutes=240, settle_delay_seconds=120)
    assert scheduled == datetime(2026, 7, 15, 12, 2, tzinfo=timezone.utc)


def test_next_candle_run_moves_forward_after_delay():
    now = datetime(2026, 7, 15, 12, 3, tzinfo=timezone.utc)
    scheduled = next_candle_run(now, timeframe_minutes=240, settle_delay_seconds=120)
    assert scheduled == datetime(2026, 7, 15, 16, 2, tzinfo=timezone.utc)


def test_maintenance_cadence_runs_first_and_every_n_cycles():
    assert should_run_maintenance(1, 6)
    assert should_run_maintenance(6, 6)
    assert should_run_maintenance(12, 6)
    assert not should_run_maintenance(5, 6)
    assert not should_run_maintenance(6, 6, enabled=False)


def test_cycle_commands_are_ordered_and_never_contain_live_order_command():
    commands = cycle_commands(OrchestratorConfig(project_root="."), "python")
    names = [item[0] for item in commands]
    assert names == ["market_monitor", "decision_evaluator", "paper_scan", "paper_evaluator", "paper_status"]
    text = " ".join(part for _, cmd, _ in commands for part in cmd).lower()
    assert "live" not in text
    assert "order" not in text


def test_maintenance_commands_refresh_history_before_fresh_oos():
    commands = maintenance_commands(OrchestratorConfig(project_root="."), "python")
    assert [item[0] for item in commands] == ["historical_incremental_update", "fresh_oos_replay"]
    assert "--update-history-only" in commands[0][1]
    assert "--run-replay" in commands[1][1]


def test_process_lock_blocks_second_process_and_recovers_after_release(tmp_path: Path):
    lock_path = tmp_path / "cycle.lock"
    with ProcessLock(lock_path):
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
        assert payload["pid"] > 0
        with pytest.raises(RuntimeError):
            ProcessLock(lock_path).acquire()
    assert not lock_path.exists()


def test_run_step_retries_then_passes(tmp_path: Path):
    calls = {"count": 0}

    def runner(command, *, cwd, timeout_seconds):
        calls["count"] += 1
        if calls["count"] == 1:
            return subprocess.CompletedProcess(command, 2, "", "temporary failure")
        return subprocess.CompletedProcess(command, 0, "ok", "")

    result = run_step(
        "example",
        ["python", "tool.py"],
        cwd=tmp_path,
        timeout_seconds=5,
        retries=1,
        retry_delay_seconds=0,
        logger=_Logger(),
        runner=runner,
    )
    assert result.status == "PASSED"
    assert result.attempts == 2
    assert result.exit_code == 0


def test_run_step_returns_failure_without_hiding_it(tmp_path: Path):
    def runner(command, *, cwd, timeout_seconds):
        return subprocess.CompletedProcess(command, 7, "partial", "failed")

    result = run_step(
        "example",
        ["python", "tool.py"],
        cwd=tmp_path,
        timeout_seconds=5,
        retries=0,
        retry_delay_seconds=0,
        logger=_Logger(),
        runner=runner,
    )
    assert result.status == "FAILED"
    assert result.exit_code == 7
    assert result.stderr_tail == ["failed"]
