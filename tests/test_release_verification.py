from __future__ import annotations

import importlib
from pathlib import Path

import pytest

import freakto


ROOT = Path(__file__).parents[1]


def test_public_version_matches_distribution_metadata():
    assert freakto.__version__ == "10.3.0"


@pytest.mark.parametrize(
    ("legacy", "canonical"),
    [
        ("market_replay_dashboard", "freakto.research.adapters.market_replay"),
        ("forward_test_dashboard", "freakto.research.adapters.forward_status"),
        ("freakto_research_suite_dashboard", "freakto.research.adapters.suite_report"),
        ("paper_performance_dashboard", "freakto.paper.performance_report"),
        ("paper_research_orchestrator", "freakto.paper.orchestrator"),
        ("paper_trading_dashboard", "freakto.paper.dashboard"),
        ("paper_trade_launch_dashboard", "freakto.paper.trade_launch"),
        ("github_cloud_runner", "freakto.paper.cloud_runner"),
    ],
)
def test_compatibility_entry_points_share_canonical_main(legacy, canonical):
    legacy_module = importlib.import_module(legacy)
    canonical_module = importlib.import_module(canonical)
    assert legacy_module.main is canonical_module.main


@pytest.mark.parametrize(
    ("launcher", "canonical_command"),
    [
        ("run_forward_test_status.bat", "-m freakto.cli report forward"),
        ("run_market_replay.bat", "-m freakto.cli replay full"),
        ("run_research_paper_cycle.bat", "-m freakto.cli paper cycle"),
    ],
)
def test_windows_launchers_are_portable_and_canonical(launcher, canonical_command):
    text = (ROOT / launcher).read_text(encoding="utf-8").lower()
    assert "cd /d \"%~dp0\"" in text
    assert ".venv\\scripts\\python.exe" in text
    assert canonical_command in text
    assert "exit /b %exit_code%" in text


@pytest.mark.parametrize(
    "launcher",
    ["run_market_replay.bat", "run_research_paper_cycle.bat"],
)
def test_mutating_windows_launchers_force_paper_only_safety(launcher):
    text = (ROOT / launcher).read_text(encoding="utf-8").lower()
    assert "set live_trading_enabled=false" in text
    assert "set real_capital_enabled=false" in text
