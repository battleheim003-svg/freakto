from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
import os
from pathlib import Path
import subprocess

import pytest

from freakto.paper.cycle_contract import (
    CYCLE_NETWORK_SKIPPED,
    NETWORK_EXHAUSTED_EXIT_CODE,
    STEP_NETWORK_SKIPPED,
)
from freakto.paper.state_paths import CANONICAL_RELATIVE_DIR
from paper_research_orchestrator import (
    PaperResearchOrchestrator,
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
    assert names == [
        "market_monitor",
        "decision_evaluator",
        "paper_scan",
        "paper_evaluator",
        "paper_performance_dashboard",
        "paper_status",
    ]
    text = " ".join(part for _, cmd, _ in commands for part in cmd).lower()
    assert "live" not in text
    assert "order" not in text


def test_default_cycle_output_is_canonical():
    assert Path(OrchestratorConfig().output_dir) == CANONICAL_RELATIVE_DIR


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


def test_pid_alive_for_current_process_never_calls_os_kill(monkeypatch):
    def unsafe_kill(*_args, **_kwargs):
        raise AssertionError("os.kill must not be used for the current process")

    monkeypatch.setattr(os, "kill", unsafe_kill)
    assert ProcessLock._pid_alive(os.getpid()) is True


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


def test_maintenance_failure_is_warning_not_hard_cycle_failure(tmp_path: Path, monkeypatch):
    config = OrchestratorConfig(project_root=str(tmp_path), step_retries=0)
    orchestrator = PaperResearchOrchestrator(config)
    monkeypatch.setattr(orchestrator, "_refresh_readiness", lambda: type("Ready", (), {"status": "RESEARCH"})())
    monkeypatch.setattr(
        orchestrator,
        "_ensure_arm",
        lambda _readiness: {"mode": "RESEARCH", "live_orders_enabled": False},
    )

    calls = {"count": 0}

    def run_commands(_commands):
        calls["count"] += 1
        if calls["count"] == 1:
            return [_step("paper_scan", "PASSED", 0)]
        return [_step("historical_incremental_update", "FAILED", 2)]

    monkeypatch.setattr(orchestrator, "_run_commands", run_commands)
    result = orchestrator.run_cycle(force_maintenance=True)

    assert result.status == "COMPLETE_WITH_MAINTENANCE_WARNINGS"
    assert result.warnings == ["historical_incremental_update failed with exit code 2."]


def test_operational_failure_remains_hard_cycle_failure(tmp_path: Path, monkeypatch):
    config = OrchestratorConfig(project_root=str(tmp_path), maintenance_enabled=False, step_retries=0)
    orchestrator = PaperResearchOrchestrator(config)
    monkeypatch.setattr(orchestrator, "_refresh_readiness", lambda: type("Ready", (), {"status": "RESEARCH"})())
    monkeypatch.setattr(
        orchestrator,
        "_ensure_arm",
        lambda _readiness: {"mode": "RESEARCH", "live_orders_enabled": False},
    )
    monkeypatch.setattr(orchestrator, "_run_commands", lambda _commands: [_step("paper_scan", "FAILED", 2)])

    result = orchestrator.run_cycle()

    assert result.status == "COMPLETE_WITH_STEP_FAILURES"


def test_network_skip_is_terminal_and_does_not_run_maintenance(
    tmp_path: Path,
    monkeypatch,
):
    config = OrchestratorConfig(
        project_root=str(tmp_path),
        maintenance_enabled=True,
        step_retries=0,
    )
    orchestrator = PaperResearchOrchestrator(config)
    monkeypatch.setattr(
        orchestrator,
        "_refresh_readiness",
        lambda: type("Ready", (), {"status": "RESEARCH"})(),
    )
    monkeypatch.setattr(
        orchestrator,
        "_ensure_arm",
        lambda _readiness: {"mode": "RESEARCH", "live_orders_enabled": False},
    )
    calls = {"count": 0}

    def run_commands(_commands):
        calls["count"] += 1
        return [
            _step(
                "market_monitor",
                STEP_NETWORK_SKIPPED,
                NETWORK_EXHAUSTED_EXIT_CODE,
            )
        ]

    monkeypatch.setattr(orchestrator, "_run_commands", run_commands)

    result = orchestrator.run_cycle(force_maintenance=True)

    assert result.status == CYCLE_NETWORK_SKIPPED
    assert calls["count"] == 1
    assert [step.name for step in result.steps] == ["market_monitor"]
    assert "no observation or trade" in result.warnings[-1]
    history = (
        tmp_path
        / "logs"
        / "paper_launch_v2"
        / "cycle_history.jsonl"
    )
    assert json.loads(history.read_text(encoding="utf-8"))["status"] == (
        CYCLE_NETWORK_SKIPPED
    )


def test_iso_utc_rejects_naive_timestamp():
    from freakto.paper.orchestrator import iso_utc

    with pytest.raises(ValueError, match="timezone-aware"):
        iso_utc(datetime(2026, 7, 1))


def test_cycle_id_normalizes_non_utc_clock(tmp_path: Path, monkeypatch):
    local = timezone(timedelta(hours=3, minutes=30))
    config = OrchestratorConfig(
        project_root=str(tmp_path),
        maintenance_enabled=False,
    )
    orchestrator = PaperResearchOrchestrator(
        config,
        now_fn=lambda: datetime(2026, 7, 1, 3, 30, tzinfo=local),
    )
    monkeypatch.setattr(
        orchestrator,
        "_refresh_readiness",
        lambda: type("Ready", (), {"status": "RESEARCH"})(),
    )
    monkeypatch.setattr(
        orchestrator,
        "_ensure_arm",
        lambda _readiness: {"mode": "RESEARCH", "live_orders_enabled": False},
    )
    monkeypatch.setattr(orchestrator, "_run_commands", lambda _commands: [])

    result = orchestrator.run_cycle()

    assert result.cycle_id == "paper_cycle_20260701_000000"
    assert result.started_utc.endswith("+00:00")


def test_logger_z_suffix_represents_real_utc(tmp_path: Path):
    from freakto.paper.orchestrator import _configure_logging

    logger = _configure_logging(tmp_path, max_bytes=4096, backups=1)
    try:
        record = logging.LogRecord(
            "freakto.paper_cycle",
            logging.INFO,
            __file__,
            1,
            "cycle",
            (),
            None,
        )
        record.created = datetime(
            2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc
        ).timestamp()
        rendered = logger.handlers[0].formatter.format(record)
        assert rendered.startswith("2026-07-01T00:00:00Z")
    finally:
        for handler in tuple(logger.handlers):
            logger.removeHandler(handler)
            handler.close()


def test_next_boundary_is_independent_of_non_utc_offset():
    local = timezone(timedelta(hours=-4))
    scheduled = next_candle_run(
        datetime(2026, 7, 15, 7, 59, tzinfo=local),
        timeframe_minutes=240,
        settle_delay_seconds=120,
    )
    assert scheduled == datetime(2026, 7, 15, 12, 2, tzinfo=timezone.utc)


def _step(name: str, status: str, exit_code: int):
    from paper_research_orchestrator import StepResult

    return StepResult(
        name=name,
        command=[name],
        started_utc="2026-07-26T00:00:00+00:00",
        finished_utc="2026-07-26T00:00:01+00:00",
        exit_code=exit_code,
        attempts=1,
        status=status,
        duration_seconds=1.0,
    )
