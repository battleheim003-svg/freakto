"""Hierarchical calibration by symbol, setup, regime, side, and timeframe."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from freakto.technical_v2.calibration import calibration_summary
from freakto.technical_v2.contracts import CalibrationSummary


SEGMENT_FIELDS = ("symbol", "setup", "regime", "side", "timeframe")


def segmented_calibration(
    observations: Iterable[dict[str, object]],
    context: dict[str, str],
    *,
    minimum_samples: int = 50,
) -> tuple[CalibrationSummary, str]:
    rows = list(observations)
    hierarchy = [
        SEGMENT_FIELDS,
        ("setup", "regime", "side"),
        ("regime", "side"),
        ("side",),
        (),
    ]
    for fields in hierarchy:
        selected = [row for row in rows if all(str(row.get(field)) == str(context.get(field)) for field in fields)]
        if len(selected) >= minimum_samples or not fields:
            pairs = [(float(row.get("probability", 0) or 0), bool(row.get("outcome"))) for row in selected]
            summary = calibration_summary(pairs, minimum_samples=minimum_samples)
            segment = "+".join(fields) if fields else "global"
            return summary, segment
    return CalibrationSummary(), "global"


def calibration_matrix(observations: Iterable[dict[str, object]], *, minimum_samples: int = 50) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[tuple[float, bool]]] = defaultdict(list)
    for row in observations:
        key = "|".join(str(row.get(field, "UNKNOWN")) for field in SEGMENT_FIELDS)
        grouped[key].append((float(row.get("probability", 0) or 0), bool(row.get("outcome"))))
    return {key: calibration_summary(values, minimum_samples=minimum_samples).to_dict() for key, values in sorted(grouped.items())}
