import pandas as pd
import pytest

from engine.segmented_threshold_optimizer import (
    SegmentedThresholdSearchConfig,
    evaluate_segment_policy,
    optimize_segment_thresholds,
)


def _frame() -> pd.DataFrame:
    rows = []
    for index in range(80):
        strong = index < 40
        rows.append(
            {
                "score": 80 if strong else 55,
                "calibrated_probability": 0.75 if strong else 0.45,
                "calibration_sample_count": 60,
                "evaluated_return": 1.0 if strong else -0.5,
            }
        )
    return pd.DataFrame(rows)


def test_segment_optimizer_tags_candidates_and_selects_viable_policy():
    config = SegmentedThresholdSearchConfig(
        raw_score_thresholds=(50, 70),
        probability_thresholds=(0.50, 0.70),
        minimum_samples_grid=(20, 50),
        expected_edge_grid=(0.0, 0.05),
        minimum_selected=20,
        target_sample_count=40,
    )
    policy, candidates = optimize_segment_thresholds(
        _frame(),
        segment_id="SIDE_REGIME:LONG|BULL",
        config=config,
    )

    assert policy is not None
    assert set(candidates["segment_id"]) == {"SIDE_REGIME:LONG|BULL"}
    assert bool(candidates.iloc[0]["viable"])
    assert int(candidates.iloc[0]["sample_count"]) == 40


def test_segment_policy_evaluation_is_fail_closed_without_policy():
    evaluation = evaluate_segment_policy(
        _frame(),
        None,
        segment_id="SIDE:LONG",
        minimum_selected=10,
    )
    assert evaluation.viable is False
    assert evaluation.selected_count == 0


def test_segment_optimizer_rejects_missing_calibration_columns():
    with pytest.raises(ValueError, match="Missing segment optimizer columns"):
        optimize_segment_thresholds(
            pd.DataFrame({"score": [80], "evaluated_return": [1.0]}),
            segment_id="SIDE:LONG",
        )
