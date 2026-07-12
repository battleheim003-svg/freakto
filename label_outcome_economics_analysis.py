"""CLI for Freakto label, exit-policy, and outcome-economics audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.exit_policy_audit import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    ExitPolicyAuditConfig,
    run_exit_policy_audit,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Audit fixed-horizon labels, first-touch Target-1/Stop labels, adaptive horizon, "
            "execution-cost drag, and intrabar ambiguity without changing runtime behavior."
        )
    )
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--minimum-policy-rows", type=int, default=500)
    parser.add_argument("--canonical-horizon", type=int, default=6, choices=[1, 3, 6, 12])
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = ExitPolicyAuditConfig(
        minimum_policy_rows=args.minimum_policy_rows,
        canonical_horizon=args.canonical_horizon,
    )
    result, artifacts = run_exit_policy_audit(
        Path(args.dataset),
        output_dir=Path(args.output_dir),
        run_id=args.run_id,
        config=config,
    )
    print("=" * 116)
    print("Freakto Label & Outcome Economics Audit")
    print("=" * 116)
    print(f"Status                    : {result.status}")
    print(f"Mode                      : {result.mode}")
    print(f"Selected replay run       : {result.selected_run_id}")
    print(f"Rows loaded/usable        : {result.rows_loaded} / {result.rows_usable}")
    print(f"Canonical policy          : {result.canonical_policy}")
    canonical = result.diagnostics.get("canonical_metrics", {})
    print(f"Canonical expectancy      : {canonical.get('expectancy', 0)}%")
    print(f"Canonical profit factor   : {canonical.get('profit_factor', 0)}")
    print(f"Best observed policy      : {result.diagnostics.get('best_observed_policy')}")
    best = result.diagnostics.get("best_observed_metrics", {})
    print(f"Best observed expectancy  : {best.get('expectancy', 0)}%")
    print(f"Recommended replacement   : {result.recommended_policy}")
    print(f"Policy change applied     : {result.policy_change_applied}")
    if not artifacts.cost_drag.empty:
        print("Cost drag by all-directional horizon:")
        subset = artifacts.cost_drag[artifacts.cost_drag["scope"].eq("ALL_DIRECTIONAL")]
        for _, row in subset.iterrows():
            print(
                f"- {row['horizon_candles']}: gross={float(row['gross_expectancy']):.6f}% | "
                f"net={float(row['net_expectancy']):.6f}% | "
                f"drag={float(row['execution_cost_drag']):.6f}% | "
                f"net_PF={float(row['net_profit_factor']):.6f}"
            )
    if result.key_findings:
        print("Key findings:")
        for item in result.key_findings:
            print(f"- {item}")
    if result.blockers:
        print("Blockers:")
        for item in result.blockers:
            print(f"- {item}")
    print(f"Report                    : {result.output_files.get('report_json', '')}")
    print(f"Policy summary            : {result.output_files.get('policy_summary_csv', '')}")
    print("Safety                    : research-only; canonical labels, score weights, Paper and Live are unchanged.")
    print("=" * 116)
    print(json.dumps({
        "status": result.status,
        "recommended_policy": result.recommended_policy,
        "policy_change_applied": result.policy_change_applied,
        "paper_live_enabled": result.paper_live_enabled,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
