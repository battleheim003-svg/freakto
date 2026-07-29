from __future__ import annotations

import ast
from pathlib import Path

import pytest

from freakto.core import PAPER_SAFETY, SafetyPolicy
from freakto.providers import MarketDataProvider
from freakto.research import resolve_data_replay, resolve_report

ROOT = Path(__file__).parents[1]
PACKAGE = ROOT / "freakto"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


@pytest.mark.parametrize(
    ("layer", "forbidden"),
    [
        ("core", ("engine", "freakto.paper", "freakto.providers", "freakto.research", "freakto.ui", "streamlit")),
        ("providers", ("engine", "freakto.paper", "freakto.research", "freakto.ui", "streamlit")),
        ("research", ("engine", "freakto.paper", "freakto.ui", "streamlit")),
        ("paper", ("freakto.research", "freakto.ui", "streamlit")),
    ],
)
def test_dependency_direction_is_enforced(layer, forbidden):
    violations = []
    for path in (PACKAGE / layer).glob("*.py"):
        for imported in _imports(path):
            if any(imported == prefix or imported.startswith(prefix + ".") for prefix in forbidden):
                violations.append(f"{path.relative_to(ROOT)} -> {imported}")
    assert not violations, "Invalid architecture dependencies:\n" + "\n".join(violations)


def test_cli_is_a_composition_root_without_direct_engine_imports():
    assert all(not name.startswith("engine") for name in _imports(PACKAGE / "cli.py"))


def test_legacy_engine_imports_are_confined_to_explicit_adapters():
    allowed_roots = {
        PACKAGE / "paper",
        PACKAGE / "research" / "adapters",
    }
    violations = []
    for path in PACKAGE.rglob("*.py"):
        if any(path.is_relative_to(root) for root in allowed_roots):
            continue
        for imported in _imports(path):
            if imported == "engine" or imported.startswith("engine."):
                violations.append(f"{path.relative_to(ROOT)} -> {imported}")
    assert not violations, "Engine imports escaped adapter boundaries:\n" + "\n".join(violations)


def test_root_compatibility_wrappers_remain_thin():
    wrappers = [
        "market_replay_dashboard.py",
        "forward_test_dashboard.py",
        "freakto_research_suite_dashboard.py",
        "paper_performance_dashboard.py",
        "paper_research_orchestrator.py",
        "paper_trading_dashboard.py",
        "paper_trade_launch_dashboard.py",
        "github_cloud_runner.py",
    ]
    for name in wrappers:
        lines = (ROOT / name).read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 15, f"Compatibility wrapper grew implementation logic: {name}"


def test_fail_closed_policy_cannot_be_constructed_unsafe():
    assert PAPER_SAFETY.payload() == {
        "live_orders_enabled": False,
        "real_capital_enabled": False,
        "allocation_pct": 0.0,
    }
    with pytest.raises(ValueError):
        SafetyPolicy(live_orders_enabled=True)
    with pytest.raises(ValueError):
        SafetyPolicy(real_capital_enabled=True)
    with pytest.raises(ValueError):
        SafetyPolicy(allocation_pct=0.01)


def test_safe_environment_overrides_an_unsafe_parent():
    environment = PAPER_SAFETY.child_environment(
        {"LIVE_TRADING_ENABLED": "true", "REAL_CAPITAL_ENABLED": "true", "KEEP": "yes"}
    )
    assert environment == {
        "LIVE_TRADING_ENABLED": "false",
        "REAL_CAPITAL_ENABLED": "false",
        "PYTHONUTF8": "1",
        "KEEP": "yes",
    }


def test_research_boundary_resolves_commands_without_executing_them():
    replay = resolve_data_replay("replay", "resume", ["--compact"], run_id="run-7")
    assert replay.script == "market_replay_dashboard.py"
    assert replay.arguments == ("--resume", "run-7", "--compact")
    report = resolve_report("forward", ["--send"])
    assert report.arguments == ("--status", "--send")


def test_provider_contract_is_runtime_checkable():
    class Provider:
        name = "fixture"

        def fetch_ohlcv(self, symbol, timeframe, *, since_ms=None, limit=None):
            return []

    assert isinstance(Provider(), MarketDataProvider)
