from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from engine.baseline_benchmarks import (
    BenchmarkConfig,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPLAY_ROOT,
    analyze_feature_architecture_v2,
    load_multi_cycle_replays,
    write_benchmark_outputs,
    evaluate_frozen_candidate,
)
from engine.feature_architecture_v2 import FeatureArchitectureV2Config


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Freakto Feature Architecture v2 & Baseline Benchmark Suite")
    p.add_argument("--replay-root", default=str(DEFAULT_REPLAY_ROOT))
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--cutoff", default="2026-07-09T12:00:00Z")
    p.add_argument("--purge-timestamps", type=int, default=6)
    p.add_argument("--minimum-train-per-side", type=int, default=250)
    p.add_argument("--minimum-holdout-samples", type=int, default=100)
    p.add_argument("--bootstrap-samples", type=int, default=300)
    p.add_argument("--frozen-model", default="", help="Optional frozen candidate joblib for fixed Fresh OOS evaluation")
    p.add_argument("--fresh-oos-file", default="", help="Optional Fresh OOS CSV/CSV.GZ; no fitting or threshold tuning is performed")
    return p


def main() -> int:
    args = parser().parse_args()
    architecture = FeatureArchitectureV2Config(
        development_cutoff_utc=args.cutoff,
        purge_timestamps=args.purge_timestamps,
        minimum_train_samples_per_side=args.minimum_train_per_side,
        minimum_holdout_samples=args.minimum_holdout_samples,
    )
    config = BenchmarkConfig(architecture=architecture, bootstrap_samples=args.bootstrap_samples)
    frames = load_multi_cycle_replays(args.replay_root)
    report, artifacts = analyze_feature_architecture_v2(frames, config)
    files = write_benchmark_outputs(report, artifacts, args.output_dir)

    print("=" * 116)
    print("Freakto Feature Architecture v2 & Baseline Benchmark Suite")
    print("=" * 116)
    print(f"Status                    : {report.status}")
    print(f"Mode                      : {report.mode}")
    print(f"Selected replay window    : {report.selected_replay_window}")
    print(f"Available replay windows  : {','.join(report.available_replay_windows) or 'NONE'}")
    print(f"Rows loaded/usable        : {report.rows_loaded} / {report.rows_usable}")
    print(f"Variants evaluated        : {len(report.variants_evaluated)}")
    print(f"Baselines evaluated       : {len(report.baselines_evaluated)}")
    print(f"Development candidate     : {report.development_candidate}")
    if not artifacts.holdout_benchmarks.empty:
        print("Holdout leaders:")
        leaders = artifacts.holdout_benchmarks.sort_values(["expectancy", "profit_factor"], ascending=False).head(8)
        for _, row in leaders.iterrows():
            print(
                f"- {row['strategy']}: family={row['family']} | n={int(row['sample_count'])} | "
                f"exp={float(row['expectancy']):.6f}% | PF={row['profit_factor']} | "
                f"CI=[{float(row['expectancy_ci_low']):.6f}, {float(row['expectancy_ci_high']):.6f}]"
            )
    print("Key findings:")
    for finding in report.key_findings:
        print(f"- {finding}")
    if report.blockers:
        print("Blockers:")
        for blocker in report.blockers:
            print(f"- {blocker}")
    print(f"Report                    : {files['markdown']}")
    print("Safety                    : development-only; no runtime weights, Paper or Live settings were changed.")
    print("=" * 116)
    if args.frozen_model or args.fresh_oos_file:
        if not (args.frozen_model and args.fresh_oos_file):
            raise SystemExit("--frozen-model and --fresh-oos-file must be supplied together")
        fresh = pd.read_csv(args.fresh_oos_file, low_memory=False)
        fresh_result, fresh_selected = evaluate_frozen_candidate(args.frozen_model, fresh)
        fresh_json = Path(args.output_dir) / "fresh_oos_fixed_evaluation.json"
        fresh_csv = Path(args.output_dir) / "fresh_oos_fixed_selected_rows.csv"
        fresh_json.write_text(json.dumps(fresh_result, ensure_ascii=False, indent=2), encoding="utf-8")
        fresh_selected.to_csv(fresh_csv, index=False, encoding="utf-8-sig")
        print(f"Fresh OOS fixed evaluation: {fresh_result}")

    print(json.dumps({
        "status": report.status,
        "development_candidate": report.development_candidate,
        "fresh_oos_required": report.fresh_oos_required,
        "promotion_applied": report.promotion_applied,
        "paper_live_enabled": report.paper_live_enabled,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
