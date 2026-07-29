"""Authoritative, versioned contracts for future research experiments."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping


LEGACY_EVENT_META_WALK_FORWARD_CONTRACT = "event-meta-walk-forward-3fold-purge6-v1"
FUTURE_EVENT_META_WALK_FORWARD_CONTRACT = "event-meta-walk-forward-4fold-purge6-v2"


@dataclass(frozen=True)
class WalkForwardContract:
    version: str
    future_only: bool
    walk_forward_folds: int
    purge_timestamps: int
    minimum_valid_folds: int
    minimum_positive_fraction: float
    event_meta_minimum_fit_rows: int
    paper_fold_minimum_samples: int
    holdout_candidate_minimum_samples: int

    def validate(self) -> None:
        expected = {
            "version": FUTURE_EVENT_META_WALK_FORWARD_CONTRACT,
            "future_only": True,
            "walk_forward_folds": 4,
            "purge_timestamps": 6,
            "minimum_valid_folds": 3,
            "minimum_positive_fraction": 2.0 / 3.0,
            "event_meta_minimum_fit_rows": 300,
            "paper_fold_minimum_samples": 30,
            "holdout_candidate_minimum_samples": 100,
        }
        if asdict(self) != expected:
            raise ValueError(
                "WALK_FORWARD_CONTRACT_VIOLATION: contract changed without a version bump"
            )


FUTURE_WALK_FORWARD_CONTRACT = WalkForwardContract(
    version=FUTURE_EVENT_META_WALK_FORWARD_CONTRACT,
    future_only=True,
    walk_forward_folds=4,
    purge_timestamps=6,
    minimum_valid_folds=3,
    minimum_positive_fraction=2.0 / 3.0,
    event_meta_minimum_fit_rows=300,
    paper_fold_minimum_samples=30,
    holdout_candidate_minimum_samples=100,
)


def research_contract_fingerprint(
    evidence: Mapping[str, Any],
    contract: WalkForwardContract = FUTURE_WALK_FORWARD_CONTRACT,
) -> str:
    contract.validate()
    payload = {"contract": asdict(contract), "evidence": dict(evidence)}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
