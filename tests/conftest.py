"""Shared test isolation and marker classification.

Matplotlib must use a non-interactive backend in tests. This keeps PDF/report
tests deterministic on Windows desktops and on headless CI runners without
changing the backend selected by production entry points.
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")


REPLAY_TESTS = {
    "test_decision_replay_safety.py",
    "test_fresh_oos_replay.py",
    "test_market_replay.py",
    "test_replay_evaluation_recorder.py",
    "test_replay_performance_evaluator.py",
    "test_replay_score_calibration.py",
}

SLOW_TESTS = {
    "test_baseline_benchmarks.py",
    "test_calibration_validation.py",
}


def pytest_collection_modifyitems(items) -> None:
    """Apply broad domain markers without coupling every test module to pytest."""
    import pytest

    for item in items:
        path = Path(str(item.path))
        name = path.name
        if name in REPLAY_TESTS or "replay" in name:
            item.add_marker(pytest.mark.replay)
        if "paper" in name or "shadow" in name or "live_demo" in name:
            item.add_marker(pytest.mark.paper)
        if name in SLOW_TESTS:
            item.add_marker(pytest.mark.slow)
