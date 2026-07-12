"""CLI for leakage-resistant side/regime segmented calibration validation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.calibration_validation import DEFAULT_DATASET
from engine.segmented_calibration import (
    DEFAULT_OUTPUT_DIR,
    SegmentedCalibrationConfig,
    run_segmented_calibration_validation,
)
from engine.segmented_threshold_optimizer import SegmentedThresholdSearchConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate side, regime and side+regime calibration segments using common "
            "chronological Train/Optimize/Holdout boundaries and development-only walk-forward checks."
        )
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--train-ratio", type=float, default=0.60)
    parser.add_argument("--optimize-ratio", type=float, default=0.20)
    parser.add_argument("--purge-rows", type=int, default=6)
    parser.add_argument("--bucket-width", type=int, default=10)
    parser.add_argument("--prior-strength", type=float, default=20.0)
    parser.add_argument("--minimum-total-rows", type=int, default=300)
    parser.add_argument("--minimum-train-rows", type=int, default=120)
    parser.add_argument("--minimum-optimize-rows", type=int, default=40)
    parser.add_argument("--minimum-holdout-rows", type=int, default=40)
    parser.add_argument("--minimum-selected-optimize", type=int, default=20)
    parser.add_argument("--minimum-selected-holdout", type=int, default=20)
    parser.add_argument("--walk-forward-folds", type=int, default=3)
    parser.add_argument(
        "--promote",
        action="store_true",
        help="Write active segmented policy files only when at least one segment has strict PASS status.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    search = SegmentedThresholdSearchConfig(minimum_selected=args.minimum_selected_optimize)
    config = SegmentedCalibrationConfig(
        train_ratio=args.train_ratio,
        optimize_ratio=args.optimize_ratio,
        purge_rows=args.purge_rows,
        bucket_width=args.bucket_width,
        prior_strength=args.prior_strength,
        minimum_total_rows=args.minimum_total_rows,
        minimum_train_rows=args.minimum_train_rows,
        minimum_optimize_rows=args.minimum_optimize_rows,
        minimum_holdout_rows=args.minimum_holdout_rows,
        minimum_selected_holdout=args.minimum_selected_holdout,
        walk_forward_folds=args.walk_forward_folds,
        search=search,
    )
    result = run_segmented_calibration_validation(
        args.input,
        output_dir=args.output_dir,
        config=config,
        promote=args.promote,
    )

    status_counts: dict[str, int] = {}
    for item in result.segment_results:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1

    print("=" * 108)
    print("Freakto Side & Regime Segmented Calibration Validator")
    print("=" * 108)
    print(f"Status                 : {result.status}")
    print(f"Rows loaded/usable     : {result.rows_loaded} / {result.rows_usable}")
    print(f"Segments evaluated     : {len(result.segment_results)}")
    print(f"Segment status counts  : {json.dumps(status_counts, ensure_ascii=False)}")
    print(f"Recommended policies   : {len(result.recommended_policies)}")
    print(f"Promoted               : {result.promoted}")

    if result.recommended_policies:
        print("Robust segments:")
        for item in result.recommended_policies:
            segment = item["segment"]["segment_id"]
            metrics = item["holdout_metrics"]
            print(
                f"- {segment}: n={metrics.get('sample_count', 0)}, "
                f"expectancy={metrics.get('expectancy', 0.0):.6f}%, "
                f"PF={metrics.get('profit_factor', 0.0):.6f}"
            )

    if result.blockers:
        print("Blockers:")
        for blocker in result.blockers:
            print(f"- {blocker}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")

    print(f"Summary                : {result.output_files.get('segment_summary')}")
    print(f"Report                 : {result.output_files.get('report_json')}")
    print("Safety                 : research-only; Paper/Live settings are unchanged.")
    print("=" * 108)
    return 0 if result.status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
