from pathlib import Path

import pandas as pd

from engine.calibration_mapper import ScoreCalibrator, evaluate_edge_gate


def _write_table(path: Path):
    pd.DataFrame(
        [
            {"raw_score": 50, "observed_success_rate": 0.45, "sample_count": 500},
            {"raw_score": 70, "observed_success_rate": 0.58, "sample_count": 400},
            {"raw_score": 90, "observed_success_rate": 0.72, "sample_count": 250},
        ]
    ).to_csv(path, index=False)


def test_interpolates_probability_and_uses_conservative_sample_count(tmp_path):
    table = tmp_path / "calibration.csv"
    _write_table(table)
    result = ScoreCalibrator(table).map_score(80)

    assert result.status == "READY"
    assert result.calibrated_probability == 0.65
    assert result.calibrated_score == 65
    assert result.sample_count == 250


def test_missing_calibration_fails_closed(tmp_path):
    result = ScoreCalibrator(tmp_path / "missing.csv").map_score(92)
    gate = evaluate_edge_gate(result)

    assert result.status == "UNAVAILABLE"
    assert result.calibrated_probability is None
    assert gate.passed is False


def test_low_sample_never_passes_edge_gate(tmp_path):
    table = tmp_path / "calibration.csv"
    pd.DataFrame(
        [
            {"raw_score": 70, "win_rate": 70, "samples": 20},
            {"raw_score": 90, "win_rate": 80, "samples": 25},
        ]
    ).to_csv(table, index=False)

    result = ScoreCalibrator(table, min_samples=100).map_score(85)
    gate = evaluate_edge_gate(result, min_samples=100)

    assert result.status == "LOW_SAMPLE"
    assert result.calibrated_probability == 0.775
    assert gate.passed is False
    assert any("حجم نمونه" in failure for failure in gate.failures)


def test_edge_gate_requires_probability_and_edge(tmp_path):
    table = tmp_path / "calibration.csv"
    _write_table(table)
    calibrator = ScoreCalibrator(table)

    weak = evaluate_edge_gate(calibrator.map_score(60))
    strong = evaluate_edge_gate(calibrator.map_score(80))

    assert weak.passed is False
    assert strong.passed is True
    assert strong.expected_edge == 0.15
