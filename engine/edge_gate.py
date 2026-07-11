"""
Freakto Empirical Edge Gate

Blocks decisions where historical evidence does not support actionability.
"""

from dataclasses import dataclass


@dataclass
class EdgeGateResult:
    actionable: bool
    probability: float
    reason: str


def evaluate_edge(probability: float, minimum_probability: float = 55.0) -> EdgeGateResult:
    if probability < minimum_probability:
        return EdgeGateResult(
            False,
            probability,
            "Historical calibrated probability below action threshold."
        )

    return EdgeGateResult(
        True,
        probability,
        "Historical evidence supports actionability."
    )
