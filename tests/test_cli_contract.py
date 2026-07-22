from __future__ import annotations

import pytest

from freakto import cli


@pytest.mark.parametrize(
    ("argv", "script", "arguments"),
    [
        (["data", "status"], "market_replay_dashboard.py", ["--status"]),
        (
            ["data", "build", "--symbols", "BTC/USDT", "--years", "1"],
            "market_replay_dashboard.py",
            ["--build-data", "--symbols", "BTC/USDT", "--years", "1"],
        ),
        (["replay", "run", "--compact"], "market_replay_dashboard.py", ["--replay", "--compact"]),
        (["replay", "full", "--step", "6"], "market_replay_dashboard.py", ["--full", "--step", "6"]),
        (
            ["replay", "resume", "run-123", "--compact"],
            "market_replay_dashboard.py",
            ["--resume", "run-123", "--compact"],
        ),
        (["report", "paper", "--no-plot"], "paper_performance_dashboard.py", ["--no-plot"]),
        (["report", "research"], "freakto_research_suite_dashboard.py", []),
        (["report", "forward", "--send"], "forward_test_dashboard.py", ["--status", "--send"]),
    ],
)
def test_canonical_delegation(monkeypatch, argv, script, arguments):
    called = {}

    def fake_run(target, forwarded=()):
        called.update(target=target, forwarded=list(forwarded))
        return 17

    monkeypatch.setattr(cli, "_run_script", fake_run)
    assert cli.main(argv) == 17
    assert called == {"target": script, "forwarded": arguments}


def test_child_process_is_fail_closed_and_exit_code_is_propagated(monkeypatch, tmp_path):
    target = tmp_path / "target.py"
    target.write_text("", encoding="utf-8")
    called = {}

    def fake_call(command, *, cwd, env):
        called.update(command=command, cwd=cwd, env=env)
        return 23

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli.subprocess, "call", fake_call)
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
    monkeypatch.setenv("REAL_CAPITAL_ENABLED", "true")

    assert cli._run_script("target.py", ["--probe"]) == 23
    assert called["command"][-2:] == [str(target), "--probe"]
    assert called["cwd"] == tmp_path
    assert called["env"]["LIVE_TRADING_ENABLED"] == "false"
    assert called["env"]["REAL_CAPITAL_ENABLED"] == "false"
    assert called["env"]["PYTHONUTF8"] == "1"


def test_migrated_target_executes_packaged_module(monkeypatch, tmp_path):
    (tmp_path / "market_replay_dashboard.py").write_text("", encoding="utf-8")
    called = {}

    def fake_call(command, *, cwd, env):
        called["command"] = command
        return 0

    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli.subprocess, "call", fake_call)
    assert cli._run_script("market_replay_dashboard.py", ["--status"]) == 0
    assert called["command"][-3:] == [
        "-m",
        "freakto.research.adapters.market_replay",
        "--status",
    ]


def test_missing_target_is_runtime_error_and_reports_safety(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    assert cli._run_script("missing.py") == cli.EXIT_RUNTIME_ERROR
    output = capsys.readouterr().out
    assert "CLI_TARGET_MISSING" in output
    assert '"live_orders_enabled": false' in output


def test_parser_exposes_four_canonical_areas(capsys):
    with pytest.raises(SystemExit) as raised:
        cli.main(["--help"])
    assert raised.value.code == 0
    help_text = capsys.readouterr().out
    for area in ("data", "replay", "paper", "report"):
        assert area in help_text


def test_forward_report_rejects_cycle_escalation(capsys):
    with pytest.raises(SystemExit) as raised:
        cli.main(["report", "forward", "--cycle"])
    assert raised.value.code == 2
    assert "read-only" in capsys.readouterr().err
