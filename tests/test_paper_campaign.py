from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from freakto.paper import campaign
from freakto.ui.control_center_state import CommandResult
from freakto.ui.job_manager import write_state


ROOT = Path(__file__).parents[1]


def prepare_policy(tmp_path: Path):
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    source = ROOT / "config" / "paper_go_live_policy.json"
    (tmp_path / "config" / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def test_campaign_is_fail_closed_before_start(tmp_path):
    status = campaign.campaign_status(tmp_path)
    assert status["status"] == "NOT_STARTED"
    assert status["live_orders_enabled"] is False
    assert status["real_capital_enabled"] is False
    assert status["allocation_pct"] == 0.0


def test_campaign_start_preflights_arms_and_spawns_safe_loop(monkeypatch, tmp_path):
    prepare_policy(tmp_path)
    calls = []
    monkeypatch.setattr(campaign, "run_cli", lambda args, **kwargs: calls.append(args) or CommandResult(("python", *args), 0, "ok", ""))
    monkeypatch.setattr(campaign, "_pid_alive", lambda pid: True)

    class Process:
        pid = 9876

    spawned = {}
    monkeypatch.setattr(campaign.subprocess, "Popen", lambda command, **kwargs: spawned.update(command=command, kwargs=kwargs) or Process())
    status = campaign.start_campaign(tmp_path)
    assert calls == [("paper", "preflight"), ("paper", "arm-research")]
    assert status["status"] == "RUNNING"
    assert status["pid"] == 9876
    assert "freakto.paper.orchestrator" in spawned["command"]
    assert "--no-immediate" in spawned["command"]
    assert spawned["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"
    assert spawned["kwargs"]["env"]["REAL_CAPITAL_ENABLED"] == "false"
    assert len(status["contract_sha256"]) == 64


def test_campaign_progress_requires_real_time_and_closed_trades(monkeypatch, tmp_path):
    prepare_policy(tmp_path)
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    state = {"campaign_id": "paper-test", "status": "RUNNING", "started_utc": started.isoformat(), "pid": 55}
    write_state(campaign.state_path(tmp_path), state)
    monkeypatch.setattr(campaign, "_pid_alive", lambda pid: True)
    performance = tmp_path / "logs" / "paper_performance"
    performance.mkdir(parents=True)
    (performance / "paper_performance_summary.json").write_text(json.dumps({"closed_trades": 200}), encoding="utf-8")
    status = campaign.campaign_status(tmp_path, now=started + timedelta(days=60))
    assert status["elapsed_days"] == 60.0
    assert status["closed_trades"] == 200
    assert status["evidence_window_complete"] is True


def test_campaign_does_not_complete_from_samples_without_elapsed_time(monkeypatch, tmp_path):
    prepare_policy(tmp_path)
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    write_state(campaign.state_path(tmp_path), {"campaign_id": "paper-test", "status": "RUNNING", "started_utc": started.isoformat(), "pid": 55})
    monkeypatch.setattr(campaign, "_pid_alive", lambda pid: True)
    performance = tmp_path / "logs" / "paper_performance"
    performance.mkdir(parents=True)
    (performance / "paper_performance_summary.json").write_text(json.dumps({"closed_trades": 500}), encoding="utf-8")
    status = campaign.campaign_status(tmp_path, now=started + timedelta(days=59, hours=23))
    assert status["evidence_window_complete"] is False


def test_stop_is_cooperative_and_persistent(monkeypatch, tmp_path):
    prepare_policy(tmp_path)
    write_state(campaign.state_path(tmp_path), {"campaign_id": "paper-test", "status": "RUNNING", "started_utc": datetime.now(timezone.utc).isoformat(), "pid": 55})
    monkeypatch.setattr(campaign, "_pid_alive", lambda pid: True)
    stopped = campaign.stop_campaign(tmp_path)
    assert stopped["status"] == "STOP_REQUESTED"
    assert (tmp_path / "logs" / "paper_cycle" / "campaign_stop.flag").is_file()


def test_campaign_recovers_real_windows_worker_pid_from_heartbeat(monkeypatch, tmp_path):
    prepare_policy(tmp_path)
    write_state(campaign.state_path(tmp_path), {"campaign_id": "paper-test", "status": "INTERRUPTED", "started_utc": datetime.now(timezone.utc).isoformat(), "pid": 11})
    heartbeat = tmp_path / "logs" / "paper_cycle"
    heartbeat.mkdir(parents=True)
    (heartbeat / "heartbeat.json").write_text(json.dumps({"pid": 99, "status": "WAITING_FOR_NEXT_CANDLE"}), encoding="utf-8")
    monkeypatch.setattr(campaign, "_pid_alive", lambda pid: int(pid) == 99)
    status = campaign.campaign_status(tmp_path)
    assert status["status"] == "RUNNING"
    assert status["pid"] == 99
    assert status["recovered_from_heartbeat"] is True


def test_blocked_preflight_never_spawns_worker(monkeypatch, tmp_path):
    prepare_policy(tmp_path)
    monkeypatch.setattr(campaign, "run_cli", lambda *args, **kwargs: CommandResult(("python",), 2, "", "blocked"))
    monkeypatch.setattr(campaign.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("must not spawn"))
    with pytest.raises(RuntimeError, match="preflight blocked"):
        campaign.start_campaign(tmp_path)
