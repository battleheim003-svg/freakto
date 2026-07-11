"""Build or inspect the economic score calibration artifact."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from engine.economic_calibration import (
    DEFAULT_ARTIFACT,
    build_economic_calibration,
    load_economic_calibration,
    save_economic_calibration,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    artifact = build_economic_calibration() if args.build else load_economic_calibration()
    if artifact is None:
        raise SystemExit(f"No artifact exists at {DEFAULT_ARTIFACT}; run with --build.")
    if args.build:
        save_economic_calibration(artifact)
    payload = asdict(artifact)
    print(json.dumps({
        "status": payload["status"],
        "usable_for_allocation": payload["usable_for_allocation"],
        "source_replay_run_id": payload["source_replay_run_id"],
        "train_samples": payload["train_samples"],
        "validation_samples": payload["validation_samples"],
        "validation_score_return_correlation": payload["validation_score_return_correlation"],
        "validation_high_minus_low_r": payload["validation_high_minus_low_r"],
        "bands": payload["bands"],
        "blockers": payload["blockers"],
    }, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
