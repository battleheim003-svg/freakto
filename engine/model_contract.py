"""Stable version contract shared by decision, replay and validation layers.

Versions are deliberately explicit instead of being inferred from package or
release names.  A score is only comparable with another score when these
identifiers match.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict


FEATURE_SET_VERSION = "technical-causal-v1"
DECISION_MODEL_VERSION = "heuristic-score-v4"
SCORE_CALIBRATION_VERSION = "replay-calibration-v2"
EXECUTION_MODEL_VERSION = "vol-liquidity-cost-v1"
SPLIT_PROTOCOL_VERSION = "chronological-60-20-20-v1"
META_LABEL_MODEL_VERSION = "logistic-meta-label-v1"


@dataclass(frozen=True)
class ModelContract:
    feature_set_version: str = FEATURE_SET_VERSION
    model_version: str = DECISION_MODEL_VERSION
    calibration_version: str = SCORE_CALIBRATION_VERSION
    execution_model_version: str = EXECUTION_MODEL_VERSION
    split_protocol_version: str = SPLIT_PROTOCOL_VERSION

    def as_dict(self) -> Dict[str, str]:
        return asdict(self)


CURRENT_MODEL_CONTRACT = ModelContract()

