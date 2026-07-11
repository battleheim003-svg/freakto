"""
Freakto Probability Engine v1

Purpose:
- Convert calibrated historical evidence into probability estimates.
- This is NOT a prediction oracle.
- It only estimates observed historical likelihood from validated samples.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class ProbabilityEstimate:
    score: float
    historical_win_probability: float
    confidence: str
    sample_size: int
    notes: list[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProbabilityEngine:
    """Maps calibrated score ranges to historical outcome probabilities."""

    def __init__(self, calibration_table: Dict[str, Dict[str, float]] | None = None):
        self.calibration_table = calibration_table or {}

    def estimate(self, score: float) -> ProbabilityEstimate:
        bucket = f"{int(float(score)//10)*10}_{int(float(score)//10)*10+9}"
        data = self.calibration_table.get(bucket)

        if not data:
            return ProbabilityEstimate(
                score=float(score),
                historical_win_probability=50.0,
                confidence="UNVALIDATED",
                sample_size=0,
                notes=[
                    "No calibrated historical bucket available.",
                    "Score must not be interpreted as probability."
                ],
            )

        probability = float(data.get("win_rate", 50.0))
        samples = int(data.get("samples", 0))

        confidence = "LOW_SAMPLE"
        if samples >= 100:
            confidence = "STRONGER_SAMPLE"
        elif samples >= 30:
            confidence = "MEDIUM_SAMPLE"

        return ProbabilityEstimate(
            score=float(score),
            historical_win_probability=round(probability, 2),
            confidence=confidence,
            sample_size=samples,
            notes=[
                "Historical calibration only.",
                "Requires continuous replay and forward validation."
            ],
        )
