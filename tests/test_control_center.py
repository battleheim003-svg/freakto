from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from freakto.ui import control_center_state as state
from freakto.ui.legacy_launcher import control_center_command
from freakto.ui.navigation import NAVIGATION
from freakto.ui.unified_state import official_paper_view


ROOT = Path(__file__).parents[1]


def test_snapshot_is_read_only_and_fail_closed_without_evidence(tmp_path):
    (tmp_path / "config").mkdir()
    policy = json.loads((ROOT / "config" / "paper_go_live_policy.json").read_text(encoding="utf-8"))
    (tmp_path / "config" / "paper_go_live_policy.json").write_text(json.dumps(policy), encoding="utf-8")
    snapshot = state.collect_snapshot(tmp_path)
    assert snapshot["paper"] == {"armed": False, "mode": "DISARMED", "updated_utc": None}
    assert snapshot["go_live"]["status"] == "BLOCKED_GO_LIVE_REVIEW"
    assert snapshot["safety"]["live_orders_enabled"] is False


def test_command_runner_forces_safe_environment(monkeypatch, tmp_path):
    called = {}

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setattr(state.subprocess, "run", lambda command, **kwargs: (called.update(command=command, kwargs=kwargs) or Completed()))
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
    result = state.run_cli(["paper", "status"], root=tmp_path)
    assert result.ok
    assert called["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"
    assert called["kwargs"]["env"]["REAL_CAPITAL_ENABLED"] == "false"


def test_script_runner_is_allowlisted(monkeypatch, tmp_path):
    (tmp_path / "airdrop_backtest_dashboard.py").write_text("# test", encoding="utf-8")

    class Completed:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setattr(state.subprocess, "run", lambda *args, **kwargs: Completed())
    assert state.run_script(["airdrop_backtest_dashboard.py", "report"], root=tmp_path).ok
    with pytest.raises(ValueError, match="allowlisted"):
        state.run_script(["not_allowed.py"], root=tmp_path)


def test_navigation_is_the_four_target_workspaces():
    assert NAVIGATION == ["Spot Paper Trading", "Research", "Airdrop", "System"]
    app = AppTest.from_file(str(ROOT / "freakto_control_center.py"), default_timeout=20).run()
    assert not app.exception
    assert app.radio[0].options == NAVIGATION
    for page in NAVIGATION:
        app.radio[0].set_value(page).run()
        assert not app.exception


def test_showcase_has_explicit_evidence_warning():
    app = AppTest.from_file(str(ROOT / "freakto_control_center.py"), default_timeout=20).run()
    app.selectbox[0].set_value("Showcase").run()
    assert not app.exception
    assert any("Not official evidence" in item.value for item in app.warning)


def test_windows_source_path_is_rendered_verbatim():
    app = AppTest.from_file(str(ROOT / "freakto_control_center.py"), default_timeout=20).run()
    expected = str(ROOT / "logs" / "paper_performance")
    assert any(item.value == expected for item in app.code)
    assert Path(expected).is_absolute()
    assert Path(expected).parts[-2:] == ("logs", "paper_performance")


def test_blocked_preflight_is_explained_and_campaign_controls_are_safe():
    app = AppTest.from_file(str(ROOT / "freakto_control_center.py"), default_timeout=20).run()
    assert any("Paper preflight" in item.value for item in app.warning)
    start = next(item for item in app.button if item.label == "Start / resume campaign")
    stop = next(item for item in app.button if item.label == "Stop campaign safely")
    assert start.disabled is True
    campaign = official_paper_view(ROOT)["campaign"]
    campaign_active = str(campaign.get("status") or "") in {"STARTING", "RUNNING"}
    assert stop.disabled is not campaign_active
    app.checkbox[0].set_value(True).run()
    start = next(item for item in app.button if item.label == "Start / resume campaign")
    assert start.disabled is True


def test_terminal_research_governance_is_visible_and_controls_are_disabled():
    app = AppTest.from_file(str(ROOT / "freakto_control_center.py"), default_timeout=20).run()
    assert not app.exception
    assert any("HOLDOUT CONSUMED" in item.value for item in app.error)
    assert any("HOLDOUT CRITERIA FAILED" in item.value for item in app.markdown)
    promotion = next(item for item in app.button if item.label == "Strategy Promotion")
    assert promotion.disabled is True
    start = next(item for item in app.button if item.label == "Start / resume campaign")
    assert start.disabled is True
    app.run()
    assert not app.exception


def test_windows_launcher_is_safe_and_repository_relative():
    source = (ROOT / "run_control_center.bat").read_text(encoding="utf-8").lower()
    assert 'cd /d "%~dp0"' in source
    assert "set live_trading_enabled=false" in source
    assert "set real_capital_enabled=false" in source
    assert "-m streamlit run freakto_control_center.py" in source


def test_legacy_command_targets_only_official_entry_point():
    command = control_center_command(ROOT)
    assert any(str(item).endswith("freakto_control_center.py") for item in command)
    assert "live_paper_web_dashboard.py" not in command
    assert command[command.index("--server.address") + 1] == "127.0.0.1"


def test_quick_start_plan_remains_research_only():
    plan = state.quick_start_plan(include_data_build=False, include_replay=False)
    assert plan[-1].key == "go_live_check"
    assert all("live" not in step.arguments for step in plan)
