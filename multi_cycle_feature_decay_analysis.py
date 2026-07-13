"""CLI for Freakto Multi-Cycle Feature Decay & Regime Drift analysis."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from engine.multi_cycle_feature_decay import (
    DEFAULT_COMPONENTS,
    FeatureDecayConfig,
    load_and_analyze,
)
from engine.regime_drift import RegimeDriftConfig


def _csv_list(value: str) -> List[str]:
    return [item.strip() for item in str(value).split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-root", default="logs/multi_cycle_archive_v2")
    parser.add_argument("--output-dir", default="logs/multi_cycle_feature_decay")
    parser.add_argument("--cutoff", default="2026-07-09T12:00:00Z")
    parser.add_argument("--recent-years", type=int, default=3)
    parser.add_argument("--transition-years", type=int, default=5)
    parser.add_argument("--score-threshold", type=float, default=70.0)
    parser.add_argument("--min-era-samples", type=int, default=100)
    parser.add_argument("--min-scope-samples", type=int, default=60)
    parser.add_argument("--min-quantile-samples", type=int, default=20)
    parser.add_argument("--quantile-bins", type=int, default=4)
    parser.add_argument("--association-tolerance", type=float, default=0.03)
    parser.add_argument("--spread-tolerance", type=float, default=0.05)
    parser.add_argument("--decay-tolerance", type=float, default=0.05)
    parser.add_argument("--psi-moderate", type=float, default=0.10)
    parser.add_argument("--psi-severe", type=float, default=0.25)
    parser.add_argument("--components", default=",".join(DEFAULT_COMPONENTS))
    parser.add_argument("--regime-min-samples", type=int, default=40)
    parser.add_argument("--regime-decay-tolerance", type=float, default=0.10)
    parser.add_argument("--regime-share-drift", type=float, default=0.10)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    regime_config = RegimeDriftConfig(
        min_samples_per_cell=max(1, int(args.regime_min_samples)),
        decay_tolerance_pct=max(0.0, float(args.regime_decay_tolerance)),
        share_drift_tolerance=max(0.0, float(args.regime_share_drift)),
    )
    config = FeatureDecayConfig(
        development_cutoff_utc=args.cutoff,
        recent_years=max(1, int(args.recent_years)),
        transition_years=max(2, int(args.transition_years)),
        fixed_score_threshold=float(args.score_threshold),
        minimum_era_samples=max(1, int(args.min_era_samples)),
        minimum_scope_samples=max(1, int(args.min_scope_samples)),
        minimum_quantile_samples=max(1, int(args.min_quantile_samples)),
        quantile_bins=max(2, int(args.quantile_bins)),
        association_tolerance=max(0.0, float(args.association_tolerance)),
        spread_tolerance_pct=max(0.0, float(args.spread_tolerance)),
        decay_tolerance=max(0.0, float(args.decay_tolerance)),
        psi_moderate=max(0.0, float(args.psi_moderate)),
        psi_severe=max(0.0, float(args.psi_severe)),
        components=tuple(_csv_list(args.components)),
        regime=regime_config,
    )
    report, artifacts = load_and_analyze(args.replay_root, args.output_dir, config)

    print("=" * 116)
    print("Freakto Multi-Cycle Feature Decay & Regime Drift Analyzer")
    print("=" * 116)
    print(f"Status                    : {report.status}")
    print(f"Mode                      : {report.mode}")
    print(f"Selected replay window    : {report.selected_replay_window}")
    print(f"Available replay windows  : {','.join(report.available_replay_windows)}")
    print(f"Development cutoff        : {report.development_cutoff_utc}")
    print(f"Rows loaded/usable        : {report.rows_loaded} / {report.rows_usable}")
    print(f"Components analyzed       : {len(report.available_components)}")
    print(f"Era counts                : {json.dumps(report.era_counts, ensure_ascii=False)}")
    print(f"Fixed benchmark           : score >= {report.fixed_score_threshold:g}")
    print(f"Component classifications : {len(artifacts.component_decay_summary)}")
    print(f"Regime classifications    : {len(artifacts.regime_drift_summary)}")
    print(f"Promotion applied         : {report.promotion_applied}")
    print(f"Paper/Live enabled        : {report.paper_live_enabled}")
    if report.key_findings:
        print("Key findings:")
        for item in report.key_findings:
            print(f"- {item}")
    if report.blockers:
        print("Blockers:")
        for item in report.blockers:
            print(f"- {item}")
    if report.warnings:
        print("Warnings:")
        for item in report.warnings:
            print(f"- {item}")
    print(f"Report                    : {Path(args.output_dir) / 'multi_cycle_feature_decay_report.md'}")
    print("Safety                    : development diagnostic only; no weights, thresholds, Paper or Live were changed.")
    print("=" * 116)
    print(
        json.dumps(
            {
                "status": report.status,
                "selected_replay_window": report.selected_replay_window,
                "promotion_applied": report.promotion_applied,
                "paper_live_enabled": report.paper_live_enabled,
            },
            ensure_ascii=False,
        )
    )
    return 2 if report.blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
