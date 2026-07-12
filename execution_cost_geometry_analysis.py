"""CLI for Freakto execution-cost and trade-geometry optimization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.execution_cost_optimizer import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    ExecutionGeometryConfig,
    run_execution_geometry_optimizer,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Optimize execution-cost gates and alternative trade geometry on chronological "
            "Train/Optimize data, then audit one selected candidate on untouched Holdout."
        )
    )
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--minimum-train-rows", type=int, default=300)
    parser.add_argument("--minimum-optimize-rows", type=int, default=150)
    parser.add_argument("--minimum-holdout-rows", type=int, default=150)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = ExecutionGeometryConfig(
        minimum_train_rows=args.minimum_train_rows,
        minimum_optimize_rows=args.minimum_optimize_rows,
        minimum_holdout_rows=args.minimum_holdout_rows,
    )
    result, artifacts = run_execution_geometry_optimizer(
        Path(args.dataset),
        output_dir=Path(args.output_dir),
        run_id=args.run_id,
        config=config,
    )
    print("=" * 116)
    print("Freakto Execution Cost & Trade Geometry Optimizer")
    print("=" * 116)
    print(f"Status                    : {result.status}")
    print(f"Mode                      : {result.mode}")
    print(f"Selected replay run       : {result.selected_run_id}")
    print(f"Rows loaded/usable        : {result.rows_loaded} / {result.rows_usable}")
    print(f"Candidates evaluated      : {len(artifacts.candidate_summary)}")
    print(f"Canonical Holdout n       : {result.canonical_metrics.get('sample_count', 0)}")
    print(f"Canonical Holdout exp     : {result.canonical_metrics.get('expectancy', 0):.6f}%")
    print(f"Canonical Holdout PF      : {result.canonical_metrics.get('profit_factor', 0):.6f}")
    print(f"Selected candidate        : {None if result.selected_candidate is None else result.selected_candidate.get('candidate_id')}")
    print(f"Candidate Holdout n       : {result.holdout_metrics.get('sample_count', 0)}")
    print(f"Candidate Holdout exp     : {result.holdout_metrics.get('expectancy', 0):.6f}%")
    print(f"Candidate Holdout PF      : {result.holdout_metrics.get('profit_factor', 0):.6f}")
    print(f"Recommended policy        : {result.recommended_policy}")
    print(f"Promotion applied         : {result.promotion_applied}")
    if result.key_findings:
        print("Key findings:")
        for item in result.key_findings:
            print(f"- {item}")
    if result.blockers:
        print("Blockers:")
        for item in result.blockers:
            print(f"- {item}")
    print(f"Report                    : {result.output_files.get('report_json', '')}")
    print(f"Candidates                : {result.output_files.get('candidate_summary_csv', '')}")
    print("Safety                    : research-only; runtime geometry, Paper and Live are unchanged.")
    print("=" * 116)
    print(json.dumps({
        "status": result.status,
        "recommended_policy": result.recommended_policy,
        "promotion_applied": result.promotion_applied,
        "paper_live_enabled": result.paper_live_enabled,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
