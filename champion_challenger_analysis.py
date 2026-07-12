"""CLI for Freakto expectancy-aware Champion/Challenger research."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from engine.champion_challenger import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    ChampionChallengerConfig,
    run_champion_challenger,
)
from engine.expectancy_challenger import ChallengerConfig, DEFAULT_VARIANTS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Freakto's technical Champion benchmark with expectancy-aware "
            "shadow challengers using chronological Train/Optimize/Holdout and "
            "pre-holdout walk-forward validation."
        )
    )
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--minimum-holdout-selected",
        type=int,
        default=60,
        help="Minimum untouched Holdout decisions required for promotion research.",
    )
    parser.add_argument(
        "--additional-execution-cost-pct",
        type=float,
        default=0.05,
        help="Extra shadow slippage/execution safety buffer in percentage points.",
    )
    parser.add_argument(
        "--list-variants",
        action="store_true",
        help="List challenger variants and exit.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.list_variants:
        for variant in DEFAULT_VARIANTS:
            print(f"{variant.name}: {variant.description}")
        return 0

    config = ChampionChallengerConfig(
        minimum_holdout_selected=args.minimum_holdout_selected,
    )
    challenger_config = ChallengerConfig(
        additional_execution_cost_pct=args.additional_execution_cost_pct,
    )
    result, artifacts = run_champion_challenger(
        Path(args.dataset),
        output_dir=Path(args.output_dir),
        run_id=args.run_id,
        config=config,
        challenger_config=challenger_config,
    )

    print("=" * 116)
    print("Freakto Expectancy-Aware Champion–Challenger Engine")
    print("=" * 116)
    print(f"Status                    : {result.status}")
    print(f"Mode                      : {result.mode}")
    print(f"Selected replay run       : {result.selected_run_id}")
    print(f"Rows loaded/usable        : {result.rows_loaded} / {result.rows_usable}")
    print(f"Champion samples          : {result.champion_holdout.get('sample_count', 0)}")
    print(f"Champion expectancy       : {result.champion_holdout.get('expectancy', 0)}%")
    print(f"Champion profit factor    : {result.champion_holdout.get('profit_factor', 0)}")
    print(f"Recommended challenger    : {result.recommended_variant}")
    print(f"Recommended EV threshold  : {result.recommended_threshold_pct}")
    print(f"Promotion applied         : {result.promotion_applied}")
    if not artifacts.summary.empty:
        print("Challenger Holdout:")
        for _, row in artifacts.summary.iterrows():
            print(
                f"- {row['variant']}: status={row['status']} | n={int(row['sample_count'])} | "
                f"selected_exp={float(row['expectancy']):.6f}% | "
                f"selected_PF={float(row['profit_factor']):.6f} | "
                f"EV>=0 n={int(row['fixed_zero_ev_sample_count'])} | "
                f"EV>=0 exp={float(row['fixed_zero_ev_expectancy']):.6f}% | "
                f"EV>=0 PF={float(row['fixed_zero_ev_profit_factor']):.6f} | "
                f"WF pass={float(row['walk_forward_pass_rate']):.2%}"
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
    print(f"Shadow predictions        : {result.output_files.get('holdout_shadow_predictions_csv', '')}")
    print("Safety                    : research/shadow-only; Champion, score weights, Paper and Live are unchanged.")
    print("=" * 116)

    # A machine-readable one-line status is useful in CI without enabling any
    # deployment or promotion action.
    print(json.dumps({
        "status": result.status,
        "recommended_variant": result.recommended_variant,
        "promotion_applied": result.promotion_applied,
        "paper_live_enabled": result.paper_live_enabled,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
