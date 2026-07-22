"""Empirical score calibration and edge gating for Freakto.

The mapper converts the engine's raw 0..100 score into an empirical probability
using a calibration table produced from replay/evaluation data. It deliberately
fails closed: missing, malformed, or under-sampled calibration data can never
promote a decision to ACTIONABLE.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


DEFAULT_CALIBRATION_PATH = Path("logs/calibration/score_calibration.csv")
DEFAULT_DATASET = Path("logs/calibration_dataset/calibration_training.csv")
DEFAULT_EDGE_GATE_POLICY_PATH = Path("logs/calibration/edge_gate_policy.json")


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
class EdgeGatePolicy:
    min_probability: float = 0.55
    min_samples: int = 100
    break_even_probability: float = 0.50
    min_expected_edge: float = 0.03
    status: str = "DEFAULT"
    source: str = "built-in defaults"


@dataclass(frozen=True)
class EdgeGateResult:
    passed: bool
    expected_edge: Optional[float]
    failures: tuple[str, ...]
    policy_status: str = "DEFAULT"
    policy_source: str = "built-in defaults"


@dataclass(frozen=True)
class CalibrationEstimate:
    """Backward-compatible bucket estimate used by legacy dashboards."""

    score: float
    probability: float
    samples: int
    verdict: str


def _bucket(score: float) -> str:
    low = int(float(score) // 10 * 10)
    return f"score_{low}_{low + 9}"


def build_mapping(dataset_path: Path | str = DEFAULT_DATASET) -> pd.DataFrame:
    """Build the legacy bucket mapping without changing its public schema."""
    path = Path(dataset_path)
    if not path.exists():
        return pd.DataFrame()
    try:
        frame = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except Exception:
        return pd.DataFrame()
    if "evaluated_return" not in frame.columns or "score" not in frame.columns:
        return pd.DataFrame()

    frame = frame.copy()
    frame["evaluated_return"] = pd.to_numeric(frame["evaluated_return"], errors="coerce")
    frame["score"] = pd.to_numeric(frame["score"], errors="coerce")
    frame = frame.dropna(subset=["evaluated_return", "score"])
    frame["win"] = frame["evaluated_return"] > 0
    frame["score_bucket"] = frame["score"].map(_bucket)
    mapping = (
        frame.groupby("score_bucket")
        .agg(
            samples=("win", "size"),
            historical_probability=("win", "mean"),
            avg_return=("evaluated_return", "mean"),
        )
        .reset_index()
    )
    mapping["historical_probability"] = (mapping["historical_probability"] * 100).round(2)
    return mapping


def estimate_probability(score: float, mapping: pd.DataFrame) -> CalibrationEstimate:
    bucket = _bucket(score)
    if mapping.empty or "score_bucket" not in mapping.columns or bucket not in set(mapping["score_bucket"]):
        return CalibrationEstimate(float(score), 50.0, 0, "NO_DATA")
    row = mapping[mapping["score_bucket"] == bucket].iloc[0]
    probability = float(row["historical_probability"])
    samples = int(row["samples"])
    verdict = "VALID" if samples >= 100 else "LOW_SAMPLE"
    return CalibrationEstimate(float(score), probability, samples, verdict)


class ScoreCalibrator:
    """Piecewise-linear mapper backed by an empirical calibration CSV."""

    SCORE_COLUMNS = ("raw_score", "score", "score_midpoint", "bucket_midpoint")
    PROBABILITY_COLUMNS = (
        "calibrated_probability",
        "observed_success_rate",
        "historical_probability",
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


def _normalize_probability(value: object, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number > 1.0:
        number /= 100.0
    return max(0.0, min(1.0, number))


def load_edge_gate_policy(
    policy_path: Path | str = DEFAULT_EDGE_GATE_POLICY_PATH,
) -> EdgeGatePolicy:
    """Load only explicitly promoted policies; otherwise return safe defaults."""
    path = Path(policy_path)
    default = EdgeGatePolicy(source=str(path) if path.exists() else "built-in defaults")
    if not path.exists():
        return default

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return EdgeGatePolicy(status="INVALID", source=str(path))

    status = str(payload.get("status", "")).upper()
    approved = bool(payload.get("approved", False))
    if status not in {"PROMOTED", "ACTIVE", "APPROVED"} and not approved:
        return EdgeGatePolicy(status="IGNORED_NOT_PROMOTED", source=str(path))

    min_probability = _normalize_probability(payload.get("min_probability"), default.min_probability)
    break_even = _normalize_probability(payload.get("break_even_probability"), default.break_even_probability)
    min_edge = _normalize_probability(payload.get("min_expected_edge"), default.min_expected_edge)
    try:
        min_samples = max(1, int(payload.get("min_samples", default.min_samples)))
    except (TypeError, ValueError):
        min_samples = default.min_samples

    if min_probability < break_even or min_edge < 0:
        return EdgeGatePolicy(status="INVALID", source=str(path))

    return EdgeGatePolicy(
        min_probability=min_probability,
        min_samples=min_samples,
        break_even_probability=break_even,
        min_expected_edge=min_edge,
        status="PROMOTED",
        source=str(path),
    )


def evaluate_edge_gate(
    calibration: CalibrationResult,
    *,
    min_probability: Optional[float] = None,
    min_samples: Optional[int] = None,
    break_even_probability: Optional[float] = None,
    min_expected_edge: Optional[float] = None,
    policy: Optional[EdgeGatePolicy] = None,
    policy_path: Path | str = DEFAULT_EDGE_GATE_POLICY_PATH,
) -> EdgeGateResult:
    """Require empirical support and a probability margin above break-even."""
    resolved = policy or load_edge_gate_policy(policy_path)
    required_probability = resolved.min_probability if min_probability is None else float(min_probability)
    required_samples = resolved.min_samples if min_samples is None else int(min_samples)
    break_even = resolved.break_even_probability if break_even_probability is None else float(break_even_probability)
    required_edge = resolved.min_expected_edge if min_expected_edge is None else float(min_expected_edge)

    failures: list[str] = []
    probability = calibration.calibrated_probability

    if probability is None:
        failures.append("کالیبراسیون تجربی در دسترس نیست.")
        return EdgeGateResult(False, None, tuple(failures), resolved.status, resolved.source)

    if calibration.sample_count < required_samples:
        failures.append(
            f"حجم نمونه کالیبراسیون کافی نیست ({calibration.sample_count} < {required_samples})."
        )

    if probability < required_probability:
        failures.append(
            f"احتمال کالیبره‌شده کمتر از حد لازم است ({probability:.1%} < {required_probability:.1%})."
        )

    expected_edge = probability - break_even
    if expected_edge < required_edge:
        failures.append(
            f"Edge تجربی کافی نیست ({expected_edge:.1%} < {required_edge:.1%})."
        )

    return EdgeGateResult(
        not failures,
        round(expected_edge, 6),
        tuple(failures),
        resolved.status,
        resolved.source,
    )
