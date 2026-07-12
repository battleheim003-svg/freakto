from pathlib import Path

import pandas as pd

from engine.calibration_validation import (
    ValidationConfig,
    chronological_three_way_split,
    load_validation_dataset,
    run_calibration_validation,
)


def _dataset(path: Path, rows: int = 720) -> Path:
    data = []
    for index in range(rows):
        score = 50 + (index % 9) * 5
        side = "LONG" if index % 2 == 0 else "SHORT"
        # Stable relationship: high scores have positive expectancy, low scores negative.
        base_return = 1.20 if score >= 75 else (0.25 if score >= 65 else -0.75)
        noise = ((index % 7) - 3) * 0.08
        data.append(
            {
                "decision_id": f"d-{index}",
                "candle_timestamp": pd.Timestamp("2025-01-01", tz="UTC") + pd.Timedelta(hours=4 * index),
                "symbol": "BTC/USDT",
                "timeframe": "4h",
                "side": side,
                "score": score,
                "evaluated_return": base_return + noise,
                "evaluation_status": "COMPLETE",
            }
        )
    pd.DataFrame(data).to_csv(path, index=False)
    return path


def test_chronological_split_has_purge_gap(tmp_path):
    path = _dataset(tmp_path / "dataset.csv")
    frame, _ = load_validation_dataset(path)
    config = ValidationConfig(purge_rows=6, minimum_total_rows=180)
    train, optimize, holdout, _ = chronological_three_way_split(frame, config)

    assert train["_row_order"].max() + 6 < optimize["_row_order"].min()
    assert optimize["_row_order"].max() + 6 < holdout["_row_order"].min()
    assert train["_event_time"].max() < optimize["_event_time"].min() < holdout["_event_time"].min()


def test_holdout_outcomes_do_not_change_selected_policy(tmp_path):
    source = _dataset(tmp_path / "dataset.csv")
    first = run_calibration_validation(source, output_dir=tmp_path / "out1")

    frame = pd.read_csv(source)
    holdout_start = int(len(frame) * 0.80)
    frame.loc[holdout_start:, "evaluated_return"] *= -10
    changed = tmp_path / "changed.csv"
    frame.to_csv(changed, index=False)
    second = run_calibration_validation(changed, output_dir=tmp_path / "out2")

    assert first.recommended_policy == second.recommended_policy
    assert first.optimized_holdout != second.optimized_holdout


def test_validation_writes_reports_and_candidate_mapping(tmp_path):
    source = _dataset(tmp_path / "dataset.csv")
    result = run_calibration_validation(source, output_dir=tmp_path / "out")

    assert result.status in {"PASS", "PASS_WITH_WARNINGS"}
    assert result.optimized_holdout["sample_count"] >= 30
    assert result.optimized_holdout["expectancy"] > 0
    for path in result.output_files.values():
        assert Path(path).exists()

    mapping = pd.read_csv(result.output_files["candidate_mapping"])
    assert {"raw_score", "calibrated_probability", "sample_count"}.issubset(mapping.columns)


def test_promotion_is_blocked_when_holdout_fails(tmp_path):
    source = _dataset(tmp_path / "dataset.csv")
    frame = pd.read_csv(source)
    holdout_start = int(len(frame) * 0.80)
    frame.loc[holdout_start:, "evaluated_return"] = -2.0
    frame.to_csv(source, index=False)

    active_mapping = tmp_path / "runtime" / "score_calibration.csv"
    active_policy = tmp_path / "runtime" / "edge_gate_policy.json"
    result = run_calibration_validation(
        source,
        output_dir=tmp_path / "out",
        promote=True,
        runtime_calibration_path=active_mapping,
        runtime_policy_path=active_policy,
    )

    assert result.status == "FAIL"
    assert result.promoted is False
    assert not active_mapping.exists()
    assert not active_policy.exists()
