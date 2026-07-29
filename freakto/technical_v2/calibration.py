"""Reliability calibration for technical confidence estimates."""

from __future__ import annotations

from collections.abc import Iterable

from freakto.technical_v2.contracts import CalibrationSummary


def calibration_summary(
    observations: Iterable[tuple[float, bool]], *, minimum_samples: int = 50, bins: int = 5
) -> CalibrationSummary:
    rows = [(max(0.0, min(1.0, float(probability))), bool(outcome)) for probability, outcome in observations]
    if not rows:
        return CalibrationSummary()
    samples = len(rows)
    empirical = sum(outcome for _, outcome in rows) / samples
    brier = sum((probability - float(outcome)) ** 2 for probability, outcome in rows) / samples
    ece = 0.0
    for index in range(bins):
        lower, upper = index / bins, (index + 1) / bins
        bucket = [row for row in rows if lower <= row[0] < upper or (index == bins - 1 and row[0] == 1)]
        if bucket:
            forecast = sum(row[0] for row in bucket) / len(bucket)
            realised = sum(row[1] for row in bucket) / len(bucket)
            ece += len(bucket) / samples * abs(forecast - realised)
    status = "CALIBRATED" if samples >= minimum_samples and ece <= 0.10 else "NEEDS_REVIEW" if samples >= minimum_samples else "UNCALIBRATED"
    return CalibrationSummary(status, samples, round(empirical, 4), round(brier, 4), round(ece, 4))
