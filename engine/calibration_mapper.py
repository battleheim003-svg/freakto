"""Empirical score calibration and edge gating for Freakto.

The mapper converts the engine's raw 0..100 score into an empirical probability
using a calibration table produced from replay/evaluation data.  It deliberately
fails closed: missing, stale, malformed, or under-sampled calibration data can
never promote a decision to ACTIONABLE.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


DEFAULT_CALIBRATION_PATH = Path("logs/calibration/score_calibration.csv")


@dataclass(frozen=True)
class CalibrationPoint:
    raw_score: float
    probability: float
    sample_count: int


@dataclass(frozen=True)
class CalibrationResult:
    raw_score: int
    calibrated_probability: Optional[float]
    calibrated_score: Optional[int]
    sample_count: int
    source: str
    status: str
    reason: str

    @property
    def available(self) -> bool:
        return self.calibrated_probability is not None


@dataclass(frozen=True)
class EdgeGateResult:
    passed: bool
    expected_edge: Optional[float]
    failures: tuple[str, ...]


class ScoreCalibrator:
    """Piecewise-linear mapper backed by an empirical calibration CSV."""

    SCORE_COLUMNS = ("raw_score", "score", "score_midpoint", "bucket_midpoint")
    PROBABILITY_COLUMNS = (
        "calibrated_probability",
        "observed_success_rate",
        "success_rate",
        "win_rate",
        "probability",
    )
    COUNT_COLUMNS = ("sample_count", "samples", "count", "n")

    def __init__(
        self,
        calibration_path: Path | str = DEFAULT_CALIBRATION_PATH,
        *,
        min_samples: int = 100,
    ) -> None:
        self.calibration_path = Path(calibration_path)
        self.min_samples = max(1, int(min_samples))
        self._points: Optional[list[CalibrationPoint]] = None
        self._load_error: Optional[str] = None

    def _pick_column(self, columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
        normalized = {str(column).strip().lower(): column for column in columns}
        for candidate in candidates:
            if candidate in normalized:
                return normalized[candidate]
        return None

    def _load_points(self) -> list[CalibrationPoint]:
        if self._points is not None:
            return self._points

        self._points = []
        if not self.calibration_path.exists():
            self._load_error = f"فایل کالیبراسیون پیدا نشد: {self.calibration_path}"
            return self._points

        try:
            frame = pd.read_csv(self.calibration_path)
        except Exception as exc:  # pragma: no cover - defensive I/O path
            self._load_error = f"خواندن فایل کالیبراسیون ناموفق بود: {exc}"
            return self._points

        score_col = self._pick_column(frame.columns, self.SCORE_COLUMNS)
        probability_col = self._pick_column(frame.columns, self.PROBABILITY_COLUMNS)
        count_col = self._pick_column(frame.columns, self.COUNT_COLUMNS)

        if not score_col or not probability_col or not count_col:
            self._load_error = (
                "schema فایل کالیبراسیون معتبر نیست؛ ستون‌های score، probability و sample_count لازم‌اند."
            )
            return self._points

        clean = frame[[score_col, probability_col, count_col]].copy()
        clean.columns = ["raw_score", "probability", "sample_count"]
        clean["raw_score"] = pd.to_numeric(clean["raw_score"], errors="coerce")
        clean["probability"] = pd.to_numeric(clean["probability"], errors="coerce")
        clean["sample_count"] = pd.to_numeric(clean["sample_count"], errors="coerce")
        clean = clean.dropna()

        if not clean.empty and clean["probability"].max() > 1.0:
            clean["probability"] = clean["probability"] / 100.0

        clean = clean[
            clean["raw_score"].between(0, 100)
            & clean["probability"].between(0, 1)
            & (clean["sample_count"] >= 0)
        ]
        clean = clean.sort_values("raw_score").drop_duplicates("raw_score", keep="last")

        self._points = [
            CalibrationPoint(float(row.raw_score), float(row.probability), int(row.sample_count))
            for row in clean.itertuples(index=False)
        ]

        if len(self._points) < 2:
            self._load_error = "حداقل دو نقطه معتبر برای نگاشت کالیبراسیون لازم است."
            self._points = []

        return self._points

    def map_score(self, raw_score: int | float) -> CalibrationResult:
        score = int(max(0, min(100, round(float(raw_score)))))
        points = self._load_points()

        if not points:
            return CalibrationResult(
                raw_score=score,
                calibrated_probability=None,
                calibrated_score=None,
                sample_count=0,
                source=str(self.calibration_path),
                status="UNAVAILABLE",
                reason=self._load_error or "داده کالیبراسیون در دسترس نیست.",
            )

        if score <= points[0].raw_score:
            left = right = points[0]
        elif score >= points[-1].raw_score:
            left = right = points[-1]
        else:
            left = points[0]
            right = points[-1]
            for index in range(1, len(points)):
                if score <= points[index].raw_score:
                    left = points[index - 1]
                    right = points[index]
                    break

        if left.raw_score == right.raw_score:
            probability = left.probability
            sample_count = left.sample_count
        else:
            weight = (score - left.raw_score) / (right.raw_score - left.raw_score)
            probability = left.probability + weight * (right.probability - left.probability)
            # Conservative support: interpolation is only as strong as its weaker endpoint.
            sample_count = min(left.sample_count, right.sample_count)

        probability = max(0.0, min(1.0, float(probability)))
        status = "READY" if sample_count >= self.min_samples else "LOW_SAMPLE"
        reason = (
            "کالیبراسیون تجربی معتبر است."
            if status == "READY"
            else f"حجم نمونه کالیبراسیون کم است: {sample_count} < {self.min_samples}."
        )

        return CalibrationResult(
            raw_score=score,
            calibrated_probability=round(probability, 6),
            calibrated_score=int(round(probability * 100)),
            sample_count=sample_count,
            source=str(self.calibration_path),
            status=status,
            reason=reason,
        )


def evaluate_edge_gate(
    calibration: CalibrationResult,
    *,
    min_probability: float = 0.55,
    min_samples: int = 100,
    break_even_probability: float = 0.50,
    min_expected_edge: float = 0.03,
) -> EdgeGateResult:
    """Require empirical support and a probability margin above break-even."""

    failures: list[str] = []
    probability = calibration.calibrated_probability

    if probability is None:
        failures.append("کالیبراسیون تجربی در دسترس نیست.")
        return EdgeGateResult(False, None, tuple(failures))

    if calibration.sample_count < min_samples:
        failures.append(
            f"حجم نمونه کالیبراسیون کافی نیست ({calibration.sample_count} < {min_samples})."
        )

    if probability < min_probability:
        failures.append(
            f"احتمال کالیبره‌شده کمتر از حد لازم است ({probability:.1%} < {min_probability:.1%})."
        )

    expected_edge = probability - break_even_probability
    if expected_edge < min_expected_edge:
        failures.append(
            f"Edge تجربی کافی نیست ({expected_edge:.1%} < {min_expected_edge:.1%})."
        )

    return EdgeGateResult(not failures, round(expected_edge, 6), tuple(failures))
