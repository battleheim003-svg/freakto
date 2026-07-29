from __future__ import annotations

import pandas as pd

from freakto.cross_asset import (
    CrossAssetForwardTracker,
    evaluate_rankings,
    rank_opportunities,
)


def _opportunities(gross_a=40.0, gross_b=25.0):
    return pd.DataFrame(
        [
            {
                "period_utc": "2024-01-01T00:00:00Z",
                "symbol": "BTC/USDT",
                "asset_class": "crypto",
                "side": "LONG",
                "raw_score": 80,
                "calibrated_probability": 0.7,
                "confidence": 0.8,
                "expected_gross_return_bps": gross_a,
                "expected_cost_bps": 10,
                "calibration_status": "VALIDATED",
                "calibration_version": "crypto-v1",
                "calibration_samples": 200,
                "data_quality_status": "PASSED",
            },
            {
                "period_utc": "2024-01-01T00:00:00Z",
                "symbol": "EUR/USD",
                "asset_class": "forex",
                "side": "SHORT",
                "raw_score": 75,
                "calibrated_probability": 0.65,
                "confidence": 0.9,
                "expected_gross_return_bps": gross_b,
                "expected_cost_bps": 5,
                "calibration_status": "VALIDATED",
                "calibration_version": "forex-v1",
                "calibration_samples": 180,
                "data_quality_status": "PASSED",
            },
        ]
    )


def test_ranker_requires_two_validated_asset_classes():
    frame = _opportunities()
    frame.loc[1, "calibration_status"] = "RESEARCH"
    report = rank_opportunities(frame)
    assert report.status == "BLOCKED"
    assert any("INSUFFICIENT_ASSET_CLASSES" in blocker for blocker in report.blockers)


def test_ranker_selects_research_opportunity_without_emitting_decision():
    report = rank_opportunities(_opportunities())
    assert report.status == "RESEARCH_REPORT"
    selected = [row for row in report.rankings if row["research_selection"]]
    assert len(selected) == 1
    assert selected[0]["symbol"] == "BTC/USDT"
    assert all("decision" not in row for row in report.rankings)


def test_ranker_can_choose_nothing():
    report = rank_opportunities(_opportunities(gross_a=5, gross_b=3))
    assert report.selected_periods == 0
    assert report.no_selection_periods == 1
    assert not any(row["research_selection"] for row in report.rankings)


def test_historical_evaluation_is_causal_and_compares_equal_weight_benchmark():
    report = rank_opportunities(_opportunities())
    rankings = pd.DataFrame(report.rankings)
    outcomes = pd.DataFrame(
        [
            {
                "period_utc": "2024-01-01T00:00:00Z",
                "symbol": "BTC/USDT",
                "outcome_observed_utc": "2024-01-02T00:00:00Z",
                "realized_gross_return_bps": 50,
                "realized_cost_bps": 10,
            },
            {
                "period_utc": "2024-01-01T00:00:00Z",
                "symbol": "EUR/USD",
                "outcome_observed_utc": "2024-01-02T00:00:00Z",
                "realized_gross_return_bps": -10,
                "realized_cost_bps": 5,
            },
        ]
    )
    evaluation = evaluate_rankings(rankings, outcomes, min_completed_periods=1)
    assert evaluation.status == "PASSED"
    assert evaluation.completed_periods == 1
    assert evaluation.selected_average_net_return_bps == 40.0


def test_historical_evaluation_blocks_duplicate_outcomes():
    report = rank_opportunities(_opportunities())
    rankings = pd.DataFrame(report.rankings)
    outcome = {
        "period_utc": "2024-01-01T00:00:00Z",
        "symbol": "BTC/USDT",
        "outcome_observed_utc": "2024-01-02T00:00:00Z",
        "realized_gross_return_bps": 50,
        "realized_cost_bps": 10,
    }
    evaluation = evaluate_rankings(rankings, pd.DataFrame([outcome, outcome]))
    assert evaluation.status == "BLOCKED"
    assert evaluation.blockers == ("DUPLICATE_OUTCOME_KEYS",)


def test_forward_tracker_is_append_only_and_requires_prior_ranking(tmp_path):
    report = rank_opportunities(_opportunities())
    tracker = CrossAssetForwardTracker(tmp_path / "forward.db")
    assert tracker.record_rankings(report.rankings) == 2
    assert tracker.record_rankings(report.rankings) == 0
    assert tracker.record_outcome(
        period_utc="2024-01-01T00:00:00Z",
        symbol="BTC/USDT",
        outcome_observed_utc="2024-01-02T00:00:00Z",
        realized_gross_return_bps=50,
        realized_cost_bps=10,
        source_ref="replay:fixture",
    )
