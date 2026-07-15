from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine.paper_readiness_v2 import (
    PaperReadinessConfig,
    assess_deterministic_candidate,
    build_paper_launch_readiness,
    deterministic_walk_forward,
)


def _event_universe(rows: int = 480, positive: bool = True) -> pd.DataFrame:
    returns = np.full(rows, 0.4 if positive else -0.4)
    return pd.DataFrame(
        {
            "__timestamp": pd.date_range("2020-01-01", periods=rows, freq="4h", tz="UTC"),
            "primary_event": ["BREAKOUT_CONFIRMATION"] * rows,
            "cost_gate_pass": [True] * rows,
            "realized_net_return_pct": returns,
        }
    )


def test_deterministic_walk_forward_uses_non_overlapping_fixed_policy():
    config = PaperReadinessConfig(minimum_fold_samples=20, walk_forward_folds=4)
    result = deterministic_walk_forward(_event_universe(), "EVENT_COST_GATED", config)
    assert len(result) == 4
    assert result["positive"].all()
    assert result["no_overlap"].all()


def test_candidate_requires_holdout_and_walk_forward():
    config = PaperReadinessConfig(minimum_fold_samples=20, walk_forward_folds=4)
    holdout = pd.DataFrame(
        [
            {
                "strategy": "EVENT_COST_GATED",
                "sample_count": 166,
                "expectancy": 1.2,
                "profit_factor": 1.8,
                "expectancy_ci_low": 0.2,
                "expectancy_ci_high": 2.0,
            }
        ]
    )
    walk = deterministic_walk_forward(_event_universe(), "EVENT_COST_GATED", config)
    assessment = assess_deterministic_candidate("EVENT_COST_GATED", holdout, walk, config)
    assert assessment.eligible is True
    assert assessment.positive_walk_forward_fraction == 1.0


def test_readiness_allows_research_but_blocks_strategy_without_fresh_oos(tmp_path: Path):
    event_dir = tmp_path / "event"
    cost_dir = tmp_path / "cost"
    event_dir.mkdir()
    cost_dir.mkdir()
    universe = _event_universe()
    universe.to_csv(event_dir / "event_universe.csv", index=False)
    pd.DataFrame(
        [
            {
                "strategy": "EVENT_COST_GATED",
                "sample_count": 166,
                "expectancy": 1.2,
                "profit_factor": 1.8,
                "expectancy_ci_low": 0.2,
                "expectancy_ci_high": 2.0,
            }
        ]
    ).to_csv(event_dir / "holdout_benchmarks.csv", index=False)
    (event_dir / "event_opportunity_v2_report.json").write_text(
        json.dumps({"event_rows": 480, "cost_gated_event_rows": 480}), encoding="utf-8"
    )
    (cost_dir / "cost_gate_diagnostics_report.json").write_text(json.dumps({"status": "COMPLETE_DIAGNOSTIC_ONLY"}), encoding="utf-8")
    fresh = tmp_path / "fresh.json"
    fresh.write_text(json.dumps({"fresh_directional_rows": 0, "fixed_gate_samples": 0}), encoding="utf-8")
    config = PaperReadinessConfig(minimum_fold_samples=20)
    readiness, _ = build_paper_launch_readiness(event_dir, cost_dir, fresh, config)
    assert readiness.research_collection_ready is True
    assert readiness.strategy_paper_ready is False
    assert readiness.status == "READY_FOR_RESEARCH_PAPER_COLLECTION"
    assert readiness.live_orders_enabled is False


def test_readiness_strategy_requires_positive_fresh_oos(tmp_path: Path):
    event_dir = tmp_path / "event"
    cost_dir = tmp_path / "cost"
    event_dir.mkdir()
    cost_dir.mkdir()
    _event_universe().to_csv(event_dir / "event_universe.csv", index=False)
    pd.DataFrame(
        [
            {
                "strategy": "EVENT_COST_GATED",
                "sample_count": 166,
                "expectancy": 1.2,
                "profit_factor": 1.8,
                "expectancy_ci_low": 0.2,
                "expectancy_ci_high": 2.0,
            }
        ]
    ).to_csv(event_dir / "holdout_benchmarks.csv", index=False)
    (event_dir / "event_opportunity_v2_report.json").write_text(json.dumps({"event_rows": 480, "cost_gated_event_rows": 480}), encoding="utf-8")
    (cost_dir / "cost_gate_diagnostics_report.json").write_text(json.dumps({"status": "COMPLETE_DIAGNOSTIC_ONLY"}), encoding="utf-8")
    fresh = tmp_path / "fresh.json"
    fresh.write_text(
        json.dumps(
            {
                "fresh_directional_rows": 350,
                "fixed_gate_samples": 70,
                "fixed_gate_expectancy": 0.25,
                "fixed_gate_profit_factor": 1.2,
            }
        ),
        encoding="utf-8",
    )
    readiness, _ = build_paper_launch_readiness(event_dir, cost_dir, fresh, PaperReadinessConfig(minimum_fold_samples=20))
    assert readiness.strategy_paper_ready is True
    assert readiness.selected_policy == "EVENT_COST_GATED"
