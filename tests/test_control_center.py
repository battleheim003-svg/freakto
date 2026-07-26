from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from freakto.ui import control_center_state as state
from freakto.ui import job_manager


ROOT = Path(__file__).parents[1]


def test_snapshot_is_read_only_and_fail_closed_without_evidence(tmp_path):
    (tmp_path / "config").mkdir()
    policy = json.loads(
        (ROOT / "config" / "paper_go_live_policy.json").read_text(encoding="utf-8")
    )
    (tmp_path / "config" / "paper_go_live_policy.json").write_text(
        json.dumps(policy), encoding="utf-8"
    )
    snapshot = state.collect_snapshot(tmp_path)
    assert snapshot["paper"] == {"armed": False, "mode": "DISARMED", "updated_utc": None}
    assert snapshot["go_live"]["status"] == "BLOCKED_GO_LIVE_REVIEW"
    assert snapshot["safety"] == {
        "live_orders_enabled": False,
        "real_capital_enabled": False,
        "allocation_pct": 0.0,
    }


def test_command_runner_forces_safe_environment(monkeypatch, tmp_path):
    called = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, **kwargs):
        called.update(command=command, kwargs=kwargs)
        return Completed()

    monkeypatch.setattr(state.subprocess, "run", fake_run)
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
    monkeypatch.setenv("REAL_CAPITAL_ENABLED", "true")
    result = state.run_cli(["paper", "status"], root=tmp_path)
    assert result.ok
    assert called["command"][-2:] == ("paper", "status")
    assert called["kwargs"]["cwd"] == tmp_path
    assert called["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"
    assert called["kwargs"]["env"]["REAL_CAPITAL_ENABLED"] == "false"


def test_script_runner_is_allowlisted_and_forces_safe_environment(monkeypatch, tmp_path):
    called = {}
    (tmp_path / "airdrop_backtest_dashboard.py").write_text("# test", encoding="utf-8")

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, **kwargs):
        called.update(command=command, kwargs=kwargs)
        return Completed()

    monkeypatch.setattr(state.subprocess, "run", fake_run)
    result = state.run_script(
        ["airdrop_backtest_dashboard.py", "report"],
        root=tmp_path,
    )
    assert result.ok
    assert called["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"
    assert called["kwargs"]["env"]["REAL_CAPITAL_ENABLED"] == "false"
    with pytest.raises(ValueError, match="allowlisted"):
        state.run_script(["not_allowed.py"], root=tmp_path)


def test_control_center_exposes_every_management_area():
    source = (ROOT / "freakto" / "ui" / "control_center.py").read_text(encoding="utf-8")
    for label in ("مرکز عملیات", "فرآیندها", "گزارش‌ها", "تنظیمات و اتوماسیون"):
        assert label in source
    for label in ("ممیزی فارکس و طلا", "چرخه Forward و Shadow", "Airdrop Outcomes", "رتبه‌بندی بین‌بازاری"):
        assert label in source
    assert "Showcase Paper" in source
    assert "official_evidence_eligible" in (
        ROOT / "freakto" / "showcase_paper" / "engine.py"
    ).read_text(encoding="utf-8")
    assert '"en": {' in source
    assert '"fa": {' in source


def test_showcase_exposes_an_explicit_loss_guard_summary():
    source = (ROOT / "freakto" / "ui" / "control_center.py").read_text(encoding="utf-8")
    assert '"loss_stop": "توقف قطعی زیان"' in source
    assert '"remaining_loss_buffer": "فاصله تا توقف زیان"' in source
    assert 'loss_used_pct = max(0.0, -guard_return)' in source
    assert 'guard_metrics[2].metric(t("loss_stop")' in source


def test_showcase_exposes_quality_profile_and_fail_closed_performance_report():
    source = (ROOT / "freakto" / "ui" / "control_center.py").read_text(encoding="utf-8")
    assert '"quality_test": "تست کیفیت و Win rate"' in source
    assert '"quality_not_promoted"' in source
    assert 'float(candidate.get("profit_factor", 0) or 0) <= 1' in source
    assert '"runbook_aligned"' in source
    assert '"evidence_collecting"' in source
    assert '"mfe_calibration"' in source


def test_quick_start_plan_is_ordered_and_ends_with_review_only_gate():
    plan = state.quick_start_plan(include_data_build=True, include_replay=True)
    assert [step.key for step in plan] == [
        "data_status",
        "data_build",
        "replay_status",
        "replay_run",
        "paper_preflight",
        "arm_research",
        "paper_cycle",
        "paper_status",
        "paper_report",
        "forward_report",
        "go_live_check",
    ]
    assert plan[-1].accepted_exit_codes == (0, 2)
    assert all("live" not in step.arguments for step in plan)


def test_quick_start_can_skip_long_running_bootstrap_steps():
    plan = state.quick_start_plan(include_data_build=False, include_replay=False)
    keys = [step.key for step in plan]
    assert "data_build" not in keys
    assert "replay_run" not in keys
    assert keys[0] == "data_status"
    assert keys[-1] == "go_live_check"


def test_section_workflows_are_fixed_research_only_plans(tmp_path):
    market = state.workflow_plan(
        "MARKET_DATA_AUDIT",
        {"start": "2023-01-01", "end": "2026-01-01"},
        root=tmp_path,
    )
    replay = state.workflow_plan("MARKET_REPLAY", root=tmp_path)
    forward = state.workflow_plan("FORWARD_SHADOW_CYCLE", root=tmp_path)
    airdrop = state.workflow_plan("AIRDROP_OUTCOMES", root=tmp_path)
    assert [step.key for step in market] == ["audit_eur_usd", "audit_xau_usd"]
    assert market[0].runner == "script"
    assert "--fixed-execution-costs" in replay[0].arguments
    assert forward[0].accepted_exit_codes == (0,)
    assert airdrop[0].accepted_exit_codes == (0, 2)
    all_arguments = [
        argument.lower()
        for plan in (market, replay, forward, airdrop)
        for step in plan
        for argument in step.arguments
    ]
    assert "live" not in all_arguments


def test_windows_launcher_is_safe_and_repository_relative():
    source = (ROOT / "run_control_center.bat").read_text(encoding="utf-8").lower()
    assert 'cd /d "%~dp0"' in source
    assert "set live_trading_enabled=false" in source
    assert "set real_capital_enabled=false" in source
    assert "-m streamlit run freakto_control_center.py" in source


def test_dashboard_renders_navigation_without_exception():
    app = AppTest.from_file(str(ROOT / "freakto_control_center.py"), default_timeout=20).run()
    assert not app.exception
    assert app.radio[0].options == ["مرکز عملیات", "فرآیندها", "گزارش‌ها", "تنظیمات و اتوماسیون"]
    app.selectbox[0].set_value("English").run()
    assert not app.exception
    assert app.radio[0].options == ["Operations", "Workflows", "Reports", "Settings & Automation"]
    assert "▶ Start complete workflow" in [button.label for button in app.button]
    quick_button = next(button for button in app.button if button.label.startswith("▶"))
    assert quick_button.disabled is True
    app.checkbox[0].check().run()
    quick_button = next(button for button in app.button if button.label.startswith("▶"))
    assert quick_button.disabled is False


def test_workflow_workspace_renders_independent_controls():
    app = AppTest.from_file(str(ROOT / "freakto_control_center.py"), default_timeout=20).run()
    app.selectbox[0].set_value("English").run()
    app.radio[0].set_value("Workflows").run()
    assert not app.exception
    rendered = {button.label for button in app.button}
    assert "Start" in rendered
    assert "Run ranking" in rendered
    assert "Preflight" in rendered
    assert "Paper status" in rendered


def test_navigation_is_reduced_to_four_clear_workspaces():
    app = AppTest.from_file(str(ROOT / "freakto_control_center.py"), default_timeout=20).run()
    app.selectbox[0].set_value("English").run()
    assert app.radio[0].options == ["Operations", "Workflows", "Reports", "Settings & Automation"]
    for page in app.radio[0].options:
        app.radio[0].set_value(page).run()
        assert not app.exception


def test_quick_start_click_launches_background_job_without_ui_exception(monkeypatch):
    launched = {}

    def fake_start(*, full):
        launched["full"] = full
        return {"job_id": "quick-ui-test", "status": "QUEUED"}

    monkeypatch.setattr(job_manager, "start_quick_job", fake_start)
    monkeypatch.setattr(job_manager, "list_jobs", lambda: [])
    app = AppTest.from_file(str(ROOT / "freakto_control_center.py"), default_timeout=20).run()
    app.checkbox[0].check().run()
    next(button for button in app.button if button.label.startswith("▶")).click().run()
    assert not app.exception
    assert launched == {"full": True}
    assert any("quick-ui-test" in message.value for message in app.success)
