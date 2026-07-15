from pathlib import Path

import github_cloud_runner as runner


def test_validate_environment_requires_telegram(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    result = runner.validate_environment()
    assert result["valid"] is False
    assert set(result["missing_required"]) == {"TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"}


def test_discover_cycle_command_is_fail_closed(tmp_path: Path):
    try:
        runner.discover_cycle_command(tmp_path)
    except FileNotFoundError as exc:
        assert "paper_research_orchestrator.py" in str(exc)
    else:
        raise AssertionError("Expected fail-closed FileNotFoundError")


def test_discover_cycle_command_uses_python(tmp_path: Path):
    (tmp_path / "paper_research_orchestrator.py").write_text("print('ok')", encoding="utf-8")
    command = runner.discover_cycle_command(tmp_path)
    assert command[-1] == "--once"
    assert "paper_research_orchestrator.py" in command


def test_live_flags_are_not_enabled_in_source():
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert '"live_orders_enabled": False' in source
    assert '"real_capital_enabled": False' in source
