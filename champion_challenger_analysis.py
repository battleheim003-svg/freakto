"""CLI for Freakto expectancy-aware Champion/Challenger research."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from engine.champion_challenger import (
    DEFAULT_DATASET,
    DEFAULT_OUTPUT_DIR,
    ChampionChallengerConfig,
    run_champion_challenger,
)
from engine.expectancy_challenger import ChallengerConfig, DEFAULT_VARIANTS
from engine.experiment_registry import DEFAULT_REGISTRY_PATH, ExperimentRegistry


EXPERIMENT_FAMILY = "EXPECTANCY_CHALLENGER_V10_7"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _experiment_id(dataset_fingerprint: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"challenger_{stamp}_{dataset_fingerprint[:10]}"


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
    parser.add_argument("--experiment-id", default="")
    parser.add_argument(
        "--experiment-family",
        default=EXPERIMENT_FAMILY,
        choices=(EXPERIMENT_FAMILY,),
    )
    parser.add_argument("--registry-path", default=str(DEFAULT_REGISTRY_PATH))
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

    dataset = Path(args.dataset)
    if not dataset.is_file():
        print(json.dumps({"status": "BLOCKED", "blocker": "DATASET_MISSING"}))
        return 2
    dataset_fingerprint = _sha256(dataset)
    experiment_id = args.experiment_id or _experiment_id(dataset_fingerprint)
    output_dir = Path(args.output_dir) / experiment_id
    if output_dir.exists():
        print(json.dumps({
            "status": "BLOCKED",
            "blocker": "EXPERIMENT_OUTPUT_ALREADY_EXISTS",
            "experiment_id": experiment_id,
        }))
        return 2

    config = ChampionChallengerConfig(
        minimum_holdout_selected=args.minimum_holdout_selected,
    )
    challenger_config = ChallengerConfig(
        additional_execution_cost_pct=args.additional_execution_cost_pct,
    )
    registry = ExperimentRegistry(args.registry_path)
    if registry.get_run(experiment_id) is not None:
        print(json.dumps({
            "status": "BLOCKED",
            "blocker": "EXPERIMENT_ID_ALREADY_REGISTERED",
            "experiment_id": experiment_id,
        }))
        return 2
    registry.start_run(
        experiment_id,
        "CHAMPION_CHALLENGER",
        hyperparameters={
            "experiment_family": args.experiment_family,
            "selected_replay_run_id": args.run_id,
            "minimum_holdout_selected": args.minimum_holdout_selected,
            "additional_execution_cost_pct": args.additional_execution_cost_pct,
            "official_evidence_eligible": False,
            "evidence_scope": "RESEARCH_SHADOW_ONLY",
        },
        data_fingerprint=dataset_fingerprint,
        notes="One-shot research Holdout; never eligible for official Paper or Go-live evidence.",
        replace_existing=False,
    )
    if not registry.claim_holdout(dataset_fingerprint, args.experiment_family, experiment_id):
        blocked = {
            "status": "BLOCKED",
            "blocker": "HOLDOUT_ALREADY_CONSUMED",
            "experiment_id": experiment_id,
            "dataset_fingerprint": dataset_fingerprint,
            "official_evidence_eligible": False,
        }
        registry.finish_run(experiment_id, "BLOCKED", blocked)
        print(json.dumps(blocked, ensure_ascii=False))
        return 2

    try:
        result, artifacts = run_champion_challenger(
            dataset,
            output_dir=output_dir,
            run_id=args.run_id,
            config=config,
            challenger_config=challenger_config,
        )
    except Exception as exc:
        registry.finish_run(
            experiment_id,
            "FAILED",
            {
                "status": "FAILED",
                "error": f"{type(exc).__name__}: {exc}",
                "official_evidence_eligible": False,
            },
        )
        raise
    registry.finish_run(
        experiment_id,
        "COMPLETED",
        {
            **result.to_dict(),
            "experiment_id": experiment_id,
            "dataset_fingerprint": dataset_fingerprint,
            "official_evidence_eligible": False,
            "evidence_scope": "RESEARCH_SHADOW_ONLY",
        },
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
    print(f"Experiment ID            : {experiment_id}")
    print(f"Official evidence         : {result.official_evidence_eligible}")
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
        "experiment_id": experiment_id,
        "recommended_variant": result.recommended_variant,
        "promotion_applied": result.promotion_applied,
        "paper_live_enabled": result.paper_live_enabled,
        "official_evidence_eligible": result.official_evidence_eligible,
        "evidence_scope": result.evidence_scope,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
