import pandas as pd

from engine.threshold_optimizer import (
    EdgeGatePolicyCandidate,
    apply_policy,
    optimize_edge_thresholds,
    selection_metrics,
)


def test_apply_policy_requires_all_edge_conditions():
    frame = pd.DataFrame(
        {
            "score": [80, 80, 65, 85],
            "calibrated_probability": [0.64, 0.54, 0.70, 0.70],
            "calibration_sample_count": [150, 150, 150, 20],
            "evaluated_return": [1.0, 2.0, 3.0, 4.0],
        }
    )
    policy = EdgeGatePolicyCandidate(70, 0.60, 100, 0.50, 0.05)
    assert apply_policy(frame, policy).tolist() == [True, False, False, False]


def test_selection_metrics_include_profit_factor_and_drawdown():
    metrics = selection_metrics(pd.Series([2.0, -1.0, 1.0, -0.5]))
    assert metrics.sample_count == 4
    assert metrics.win_rate == 0.5
    assert metrics.profit_factor == 2.0
    assert metrics.max_drawdown == -1.0


def test_optimizer_rejects_tiny_high_return_candidate():
    rows = []
    for index in range(120):
        strong = index < 40
        rows.append(
            {
                "score": 85 if strong else 65,
                "calibrated_probability": 0.68 if strong else 0.52,
                "calibration_sample_count": 120,
                "evaluated_return": 1.0 if strong else -0.2,
            }
        )
    frame = pd.DataFrame(rows)
    policy, candidates = optimize_edge_thresholds(
        frame,
        raw_score_thresholds=(60, 80),
        probability_thresholds=(0.50, 0.65),
        minimum_samples_grid=(100,),
        expected_edge_grid=(0.0, 0.03),
        minimum_selected=30,
    )
    assert policy is not None
    selected = apply_policy(frame, policy)
    assert selected.sum() == 40
    assert candidates.iloc[0]["viable"]
    assert int(candidates.iloc[0]["sample_count"]) == 40
