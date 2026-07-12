"""Command-line runner for leakage-resistant calibration validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.calibration_validation import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    ValidationConfig,
    run_calibration_validation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate Freakto calibration and optimize empirical edge-gate thresholds."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--train-ratio", type=float, default=0.60)
    parser.add_argument("--optimize-ratio", type=float, default=0.20)
    parser.add_argument("--purge-rows", type=int, default=6)
    parser.add_argument("--bucket-width", type=int, default=10)
    parser.add_argument("--prior-strength", type=float, default=20.0)
    parser.add_argument("--minimum-total-rows", type=int, default=180)
    parser.add_argument("--minimum-selected", type=int, default=30)
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Promote the policy and mapping only when untouched holdout status is PASS.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = ValidationConfig(
        train_ratio=args.train_ratio,
        optimize_ratio=args.optimize_ratio,
        purge_rows=args.purge_rows,
        bucket_width=args.bucket_width,
        prior_strength=args.prior_strength,
        minimum_total_rows=args.minimum_total_rows,
        minimum_selected=args.minimum_selected,
    )
    result = run_calibration_validation(
        args.input,
        output_dir=args.output_dir,
        config=config,
        promote=args.promote,
    )

    print("=" * 100)
    print("Freakto Calibration Validation & Threshold Optimizer")
    print("=" * 100)
    print(f"Status              : {result.status}")
    print(f"Rows loaded/usable  : {result.rows_loaded} / {result.rows_usable}")
    print(f"Promoted            : {result.promoted}")
    print("Recommended policy  :")
    print(json.dumps(result.recommended_policy, ensure_ascii=False, indent=2))
    print("Baseline holdout     :")
    print(json.dumps(result.baseline_holdout, ensure_ascii=False, indent=2))
    print("Optimized holdout    :")
    print(json.dumps(result.optimized_holdout, ensure_ascii=False, indent=2))
    print("Calibration metrics  :")
    print(json.dumps(result.calibration_metrics, ensure_ascii=False, indent=2))
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")
    if result.blockers:
        print("Blockers:")
        for blocker in result.blockers:
            print(f"- {blocker}")
    print(f"Report              : {result.output_files.get('report_json')}")
    print("Safety              : research-only; no Paper/Live trading is enabled.")
    print("=" * 100)
    return 0 if result.status in {"PASS", "PASS_WITH_WARNINGS"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
