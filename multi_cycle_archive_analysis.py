"""CLI for Freakto Multi-Cycle Historical Archive v2."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from engine.multi_cycle_archive import MultiCycleArchiveConfig, run_multi_cycle_archive
from engine.multi_cycle_validation import (
    MultiCycleValidationConfig,
    load_replay_files,
    run_multi_cycle_validation,
)


def _csv_list(value: str) -> List[str]:
    return [item.strip() for item in str(value).split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Freakto Multi-Cycle Historical Archive v2")
    parser.add_argument("--symbols", default="BTC/USDT,ETH/USDT,SOL/USDT")
    parser.add_argument("--timeframe", default="4h")
    parser.add_argument("--windows", default="3Y,5Y,FULL")
    parser.add_argument("--cutoff", default="", help="Frozen development cutoff. Defaults to Fresh OOS manifest.")
    parser.add_argument("--full-start", default="2017-01-01T00:00:00+00:00")
    parser.add_argument("--archive-root", default="data/multi_cycle_archive_v2")
    parser.add_argument("--output-dir", default="logs/multi_cycle_archive_v2")
    parser.add_argument("--source-data-dir", default="data/market_replay")
    parser.add_argument("--fresh-freeze-dir", default="logs/fresh_oos_v2/development_freeze")
    parser.add_argument("--exchange", default="auto")
    parser.add_argument("--exchange-order", default="kucoin,okx,bybit,kraken")
    parser.add_argument("--build", action="store_true", help="Fetch/build separated development archives.")
    parser.add_argument("--run-replay", action="store_true", help="Run replay for 3Y/5Y/FULL archives.")
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--score-threshold", type=float, default=70.0)
    parser.add_argument("--rolling-days", type=int, default=365)
    parser.add_argument("--rolling-step-days", type=int, default=180)
    parser.add_argument("--expanding-min-train-days", type=int, default=730)
    parser.add_argument("--expanding-test-days", type=int, default=180)
    parser.add_argument("--min-window-samples", type=int, default=50)
    return parser


def _write_markdown(archive_report, validation_report, output_dir: Path) -> None:
    lines = [
        "# Freakto Multi-Cycle Historical Archive v2",
        "",
        f"- Archive status: **{archive_report.status}**",
        f"- Validation status: **{validation_report.status}**",
        f"- Development cutoff: `{archive_report.development_cutoff_utc}`",
        f"- Dataset manifests: **{len(archive_report.datasets)}**",
        f"- Replay windows: **{len(archive_report.replay_runs)}**",
        f"- Fixed benchmark: `score >= {validation_report.fixed_score_threshold:g}`",
        f"- Promotion applied: **{validation_report.promotion_applied}**",
        f"- Paper/Live enabled: **{validation_report.paper_live_enabled}**",
        "",
        "## Window results",
        "",
    ]
    if not validation_report.by_window:
        lines.append("No replay windows are available yet. Build archives and run replay first.")
    for row in validation_report.by_window:
        fixed = row.get("fixed_gate", {})
        all_directional = row.get("all_directional", {})
        lines.extend(
            [
                f"### {row.get('window')}",
                f"- Directional n: {all_directional.get('sample_count', 0)}",
                f"- Directional expectancy: {all_directional.get('expectancy', 0):.6f}%",
                f"- Directional PF: {all_directional.get('profit_factor', 0)}",
                f"- Fixed-gate n: {fixed.get('sample_count', 0)}",
                f"- Fixed-gate expectancy: {fixed.get('expectancy', 0):.6f}%",
                f"- Fixed-gate PF: {fixed.get('profit_factor', 0)}",
                "",
            ]
        )
    if archive_report.blockers or validation_report.blockers:
        lines.append("## Blockers")
        for blocker in [*archive_report.blockers, *validation_report.blockers]:
            lines.append(f"- {blocker}")
        lines.append("")
    lines.extend(
        [
            "## Safety",
            "",
            "This tool is development-research only. It does not reopen the Fresh OOS freeze, tune a threshold, promote a policy, or enable Paper/Live trading.",
        ]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "multi_cycle_archive_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = build_parser().parse_args()
    archive_config = MultiCycleArchiveConfig(
        symbols=_csv_list(args.symbols),
        timeframe=args.timeframe,
        windows=[item.upper() for item in _csv_list(args.windows)],
        development_cutoff_utc=args.cutoff,
        full_history_start_utc=args.full_start,
        archive_root=args.archive_root,
        output_dir=args.output_dir,
        source_data_dir=args.source_data_dir,
        fresh_freeze_dir=args.fresh_freeze_dir,
        exchange=args.exchange,
        exchange_order=_csv_list(args.exchange_order),
        build_archives=bool(args.build),
        run_replays=bool(args.run_replay),
        force_refresh=bool(args.force_refresh),
        replay_step=max(1, int(args.step)),
        fixed_score_threshold=float(args.score_threshold),
    )
    archive_report = run_multi_cycle_archive(archive_config)
    frames = load_replay_files(args.output_dir)
    validation_config = MultiCycleValidationConfig(
        output_dir=args.output_dir,
        fixed_score_threshold=float(args.score_threshold),
        rolling_window_days=max(1, int(args.rolling_days)),
        rolling_step_days=max(1, int(args.rolling_step_days)),
        expanding_min_train_days=max(1, int(args.expanding_min_train_days)),
        expanding_test_days=max(1, int(args.expanding_test_days)),
        min_window_samples=max(1, int(args.min_window_samples)),
    )
    validation_report = run_multi_cycle_validation(frames, validation_config)
    output_dir = Path(args.output_dir)
    _write_markdown(archive_report, validation_report, output_dir)

    print("=" * 116)
    print("Freakto Multi-Cycle Historical Archive v2")
    print("=" * 116)
    print(f"Archive status            : {archive_report.status}")
    print(f"Validation status         : {validation_report.status}")
    print(f"Mode                      : {archive_report.mode}")
    print(f"Development cutoff        : {archive_report.development_cutoff_utc}")
    print(f"Archive datasets          : {len(archive_report.datasets)}")
    print(f"Replay windows            : {len(archive_report.replay_runs)}")
    print(f"Fixed threshold           : score >= {validation_report.fixed_score_threshold:g}")
    print(f"Rolling windows           : {len(validation_report.rolling_windows)}")
    print(f"Expanding windows         : {len(validation_report.expanding_windows)}")
    print(f"Drift diagnostics         : {len(validation_report.drift)}")
    print(f"Regime stability rows     : {len(validation_report.regime_stability)}")
    print(f"Promotion applied         : {validation_report.promotion_applied}")
    print(f"Paper/Live enabled        : {validation_report.paper_live_enabled}")
    blockers = [*archive_report.blockers, *validation_report.blockers]
    if blockers:
        print("Blockers:")
        for item in blockers:
            print(f"- {item}")
    warnings = [*archive_report.warnings, *validation_report.warnings]
    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"- {item}")
    print(f"Report                    : {output_dir / 'multi_cycle_archive_report.md'}")
    print("Safety                    : development-only; Fresh OOS freeze, Paper and Live are unchanged.")
    print("=" * 116)
    print(json.dumps({
        "archive_status": archive_report.status,
        "validation_status": validation_report.status,
        "promotion_applied": False,
        "paper_live_enabled": False,
    }, ensure_ascii=False))
    return 0 if not blockers else 2


if __name__ == "__main__":
    raise SystemExit(main())
