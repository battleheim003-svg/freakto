from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from engine.baseline_benchmarks import load_multi_cycle_replays
from engine.cost_aware_label_v2 import (
    CostAwareLabelConfig,
    EventMetaLabelConfig,
    evaluate_frozen_event_candidate,
)
from engine.event_opportunity_benchmarks import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_REPLAY_ROOT,
    analyze_event_opportunity_universe,
    write_event_opportunity_outputs,
)
from engine.event_opportunity_universe import EventUniverseConfig


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Freakto Event-Based Opportunity Universe & Cost-Aware Label v2")
    p.add_argument("--replay-root", default=str(DEFAULT_REPLAY_ROOT))
    p.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    p.add_argument("--cutoff", default="2026-07-09T12:00:00Z")
    p.add_argument("--horizon", type=int, default=6)
    p.add_argument("--purge-timestamps", type=int, default=6)
    p.add_argument("--minimum-train-events", type=int, default=300)
    p.add_argument("--minimum-holdout-events", type=int, default=100)
    p.add_argument("--bootstrap-samples", type=int, default=300)
    p.add_argument("--frozen-model", default="")
    p.add_argument("--fresh-oos-file", default="")
    return p


def main() -> int:
    args = parser().parse_args()
    event = EventUniverseConfig(development_cutoff_utc=args.cutoff)
    label = CostAwareLabelConfig(horizon_candles=args.horizon)
    config = EventMetaLabelConfig(
        event=event,
        label=label,
        purge_timestamps=args.purge_timestamps,
        minimum_train_events=args.minimum_train_events,
        minimum_holdout_events=args.minimum_holdout_events,
        bootstrap_samples=args.bootstrap_samples,
    )
    frames = load_multi_cycle_replays(args.replay_root)
    report, artifacts = analyze_event_opportunity_universe(frames, config)
    files = write_event_opportunity_outputs(report, artifacts, args.output_dir)

    print("=" * 116)
    print("Freakto Event-Based Opportunity Universe & Cost-Aware Label v2")
    print("=" * 116)
    print(f"Status                    : {report.status}")
    print(f"Mode                      : {report.mode}")
    print(f"Selected replay window    : {report.selected_replay_window}")
    print(f"Available replay windows  : {','.join(report.available_replay_windows) or 'NONE'}")
    print(f"Rows loaded/directional   : {report.rows_loaded} / {report.directional_rows}")
    print(f"Event rows                : {report.event_rows}")
    print(f"Cost-gated event rows     : {report.cost_gated_event_rows}")
    print(f"Event rate                : {report.event_rate:.2%}")
    print(f"Development candidate     : {report.development_candidate}")
    if not artifacts.holdout_benchmarks.empty:
        print("Holdout leaders:")
        leaders = artifacts.holdout_benchmarks.sort_values(["expectancy", "profit_factor"], ascending=False).head(10)
        for _, row in leaders.iterrows():
            print(
                f"- {row['strategy']}: family={row['family']} | n={int(row['sample_count'])} | "
                f"exp={float(row['expectancy']):.6f}% | PF={row['profit_factor']} | "
                f"CI=[{float(row['expectancy_ci_low']):.6f}, {float(row['expectancy_ci_high']):.6f}]"
            )
    print("Key findings:")
    for item in report.key_findings:
        print(f"- {item}")
    if report.blockers:
        print("Blockers:")
        for item in report.blockers:
            print(f"- {item}")
    print(f"Report                    : {files['markdown']}")
    print("Safety                    : development-only; no runtime policy, Paper or Live settings were changed.")
    print("=" * 116)

    if args.frozen_model or args.fresh_oos_file:
        if not (args.frozen_model and args.fresh_oos_file):
            raise SystemExit("--frozen-model and --fresh-oos-file must be supplied together")
        fresh = pd.read_csv(args.fresh_oos_file, low_memory=False)
        result, selected = evaluate_frozen_event_candidate(args.frozen_model, fresh)
        output = Path(args.output_dir)
        (output / "fresh_oos_fixed_event_evaluation.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        selected.to_csv(output / "fresh_oos_fixed_event_selected_rows.csv", index=False, encoding="utf-8-sig")
        print(f"Fresh OOS fixed evaluation: {result}")

    print(
        json.dumps(
            {
                "status": report.status,
                "development_candidate": report.development_candidate,
                "fresh_oos_required": report.fresh_oos_required,
                "promotion_applied": report.promotion_applied,
                "paper_live_enabled": report.paper_live_enabled,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
