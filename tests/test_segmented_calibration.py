from dataclasses import replace
from pathlib import Path

import pandas as pd

from engine.segmented_calibration import (
    SegmentedCalibrationConfig,
    build_segment_definitions,
    normalize_regime_label,
    run_segmented_calibration_validation,
)
from engine.segmented_threshold_optimizer import SegmentedThresholdSearchConfig


def _dataset(path: Path, rows: int = 960, include_unknown: bool = False) -> Path:
    data = []
    for index in range(rows):
        side = "LONG" if index % 2 == 0 else "SHORT"
        regime = "TRENDING_BULL" if index % 4 in (0, 1) else "TRENDING_BEAR"
        if include_unknown and index % 31 == 0:
            regime = "UNKNOWN"

        strong = side == "LONG" and regime == "TRENDING_BULL"
        score = 82 if strong else (68 if side == "LONG" else 58)
        if strong:
            evaluated_return = 1.20 + ((index % 5) - 2) * 0.03
        else:
            evaluated_return = -0.45 + ((index % 7) - 3) * 0.02

        data.append(
            {
                "decision_id": f"seg-{index}",
                "candle_timestamp": pd.Timestamp("2025-01-01", tz="UTC")
                + pd.Timedelta(hours=4 * index),
                "symbol": "BTC/USDT",
                "timeframe": "4h",
                "side": side,
                "score": score,
                "regime_label": regime,
                "evaluated_return": evaluated_return,
                "evaluation_status": "COMPLETE",
            }
        )
    pd.DataFrame(data).to_csv(path, index=False)
    return path


def _config() -> SegmentedCalibrationConfig:
    search = SegmentedThresholdSearchConfig(
        raw_score_thresholds=(55, 70, 80),
        probability_thresholds=(0.50, 0.60, 0.70),
        minimum_samples_grid=(10, 20, 40),
        expected_edge_grid=(0.0, 0.03),
        minimum_selected=10,
        target_sample_count=30,
    )
    return SegmentedCalibrationConfig(
        purge_rows=2,
        minimum_total_rows=300,
        minimum_train_rows=50,
        minimum_optimize_rows=20,
        minimum_holdout_rows=20,
        minimum_selected_holdout=10,
        strong_selected_holdout=10,
        walk_forward_folds=2,
        minimum_walk_forward_folds=2,
        minimum_walk_forward_pass_rate=1.0,
        minimum_walk_forward_train_rows=40,
        minimum_walk_forward_optimize_rows=10,
        minimum_walk_forward_test_rows=10,
        max_brier_score=0.35,
        max_ece=0.25,
        search=search,
    )


def _find(result, segment_id: str):
    return next(item for item in result.segment_results if item.segment.segment_id == segment_id)


def test_regime_normalization_is_explicit_and_fail_closed():
    assert normalize_regime_label("TRENDING_BULL") == "BULL"
    assert normalize_regime_label("bearish") == "BEAR"
    assert normalize_regime_label("range") == "SIDEWAYS"
    assert normalize_regime_label("new-unseen-label") == "UNKNOWN"


def test_segment_definitions_do_not_depend_on_outcomes(tmp_path):
    source = _dataset(tmp_path / "segments.csv", include_unknown=True)
    frame = pd.read_csv(source)
    first = build_segment_definitions(frame, _config())
    frame["evaluated_return"] *= -100
    second = build_segment_definitions(frame, _config())

    assert [item.to_dict() for item in first] == [item.to_dict() for item in second]
    unknown = next(item for item in first if item.segment_id == "REGIME:UNKNOWN")
    assert unknown.promotion_eligible is False


def test_holdout_outcomes_do_not_change_selected_segment_policy(tmp_path):
    source = _dataset(tmp_path / "segments.csv")
    first = run_segmented_calibration_validation(
        source,
        output_dir=tmp_path / "first",
        config=_config(),
    )
    first_segment = _find(first, "SIDE_REGIME:LONG|BULL")
    assert first_segment.selected_policy is not None

    changed = pd.read_csv(source)
    holdout_start = int(len(changed) * 0.80)
    mask = (
        changed.index >= holdout_start
    ) & changed["side"].eq("LONG") & changed["regime_label"].eq("TRENDING_BULL")
    changed.loc[mask, "evaluated_return"] *= -5
    changed_path = tmp_path / "changed.csv"
    changed.to_csv(changed_path, index=False)

    second = run_segmented_calibration_validation(
        changed_path,
        output_dir=tmp_path / "second",
        config=_config(),
    )
    second_segment = _find(second, "SIDE_REGIME:LONG|BULL")

    assert first_segment.selected_policy == second_segment.selected_policy
    assert first_segment.optimized_holdout != second_segment.optimized_holdout
    assert second_segment.status == "FAIL"


def test_strong_segment_passes_and_writes_all_reports(tmp_path):
    source = _dataset(tmp_path / "segments.csv")
    result = run_segmented_calibration_validation(
        source,
        output_dir=tmp_path / "out",
        config=_config(),
    )
    segment = _find(result, "SIDE_REGIME:LONG|BULL")

    assert result.status == "PASS"
    assert segment.status == "PASS"
    assert segment.optimized_holdout["expectancy"] > 0
    assert segment.walk_forward["stable"] is True
    assert any(
        item["segment"]["segment_id"] == "SIDE_REGIME:LONG|BULL"
        for item in result.recommended_policies
    )
    for output in result.output_files.values():
        assert Path(output).exists()

    walk = pd.read_csv(result.output_files["walk_forward_folds"])
    completed = walk[
        (walk["segment_id"] == "SIDE_REGIME:LONG|BULL")
        & walk["status"].isin(["PASS", "FAIL", "NO_POLICY"])
    ]
    assert not completed.empty
    train_end = pd.to_datetime(completed["train_end"], utc=True)
    optimize_start = pd.to_datetime(completed["optimize_start"], utc=True)
    optimize_end = pd.to_datetime(completed["optimize_end"], utc=True)
    test_start = pd.to_datetime(completed["test_start"], utc=True)
    assert (train_end < optimize_start).all()
    assert (optimize_end < test_start).all()


def test_promotion_is_blocked_when_no_segment_has_strict_pass(tmp_path):
    source = _dataset(tmp_path / "segments.csv")
    frame = pd.read_csv(source)
    holdout_start = int(len(frame) * 0.80)
    frame.loc[holdout_start:, "evaluated_return"] = -2.0
    frame.to_csv(source, index=False)

    active_mapping = tmp_path / "runtime" / "segmented_mapping.csv"
    active_policy = tmp_path / "runtime" / "segmented_policy.json"
    result = run_segmented_calibration_validation(
        source,
        output_dir=tmp_path / "out",
        config=_config(),
        promote=True,
        runtime_mapping_path=active_mapping,
        runtime_policy_path=active_policy,
    )

    assert result.status == "FAIL"
    assert result.promoted is False
    assert not active_mapping.exists()
    assert not active_policy.exists()


def test_sparse_segments_are_not_rescued_by_lowering_thresholds(tmp_path):
    source = _dataset(tmp_path / "segments.csv", rows=480, include_unknown=True)
    config = replace(
        _config(),
        minimum_train_rows=100,
        minimum_optimize_rows=40,
        minimum_holdout_rows=40,
    )
    result = run_segmented_calibration_validation(
        source,
        output_dir=tmp_path / "out",
        config=config,
    )
    unknown = _find(result, "REGIME:UNKNOWN")
    assert unknown.status == "INELIGIBLE"
    assert unknown.selected_policy is None
