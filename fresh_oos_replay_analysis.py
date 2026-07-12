from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from engine.fresh_oos_replay import FreshOOSConfig, run_fresh_oos_pipeline


def _csv_list(value: str):
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Freakto Fresh Out-of-Sample Replay & Feature Store v2")
    parser.add_argument("--development-replay", default="logs/market_replay/market_replay_evaluations.csv")
    parser.add_argument("--output-dir", default="logs/fresh_oos_v2")
    parser.add_argument("--symbols", default="BTC/USDT,ETH/USDT,SOL/USDT")
    parser.add_argument("--timeframes", default="4h")
    parser.add_argument("--data-dir", default="data/market_replay")
    parser.add_argument("--max-path-candles", type=int, default=24)
    parser.add_argument("--min-fresh-rows", type=int, default=300)
    parser.add_argument("--min-rows-per-symbol", type=int, default=50)
    parser.add_argument("--cost-profile-file", default="")
    parser.add_argument("--run-replay", action="store_true")
    parser.add_argument("--force-refreeze", action="store_true")
    args = parser.parse_args()

    config = FreshOOSConfig(
        development_replay_csv=args.development_replay,
        output_dir=args.output_dir,
        symbols=_csv_list(args.symbols),
        timeframes=_csv_list(args.timeframes),
        data_dir=args.data_dir,
        max_path_candles=max(1, args.max_path_candles),
        min_fresh_directional_rows=max(1, args.min_fresh_rows),
        min_rows_per_symbol=max(1, args.min_rows_per_symbol),
        cost_profile_file=args.cost_profile_file,
        run_replay=bool(args.run_replay),
        force_refreeze=bool(args.force_refreeze),
    )
    report = run_fresh_oos_pipeline(config)
    print("=" * 116)
    print("Freakto Fresh Out-of-Sample Replay & Feature Store v2")
    print("=" * 116)
    print(f"Status                    : {report.status}")
    print(f"Mode                      : {report.mode}")
    print(f"Development dataset       : {report.development_dataset_id}")
    print(f"Development cutoff        : {report.development_cutoff_utc}")
    print(f"Source replay rows        : {report.source_replay_rows}")
    print(f"Fresh rows                : {report.fresh_rows}")
    print(f"Fresh directional rows    : {report.fresh_directional_rows}")
    print(f"Fixed threshold           : score >= {report.fixed_threshold:g}")
    print(f"Fixed-gate samples        : {report.fixed_gate.get('sample_count', 0)}")
    print(f"Fixed-gate expectancy     : {report.fixed_gate.get('expectancy', 0.0):.6f}%")
    print(f"Fixed-gate profit factor  : {report.fixed_gate.get('profit_factor', 0.0)}")
    print(f"Feature rows              : {report.feature_store.get('feature_rows', 0)}")
    print(f"Outcome path rows         : {report.feature_store.get('path_rows', 0)}")
    print(f"Promotion applied         : {report.promotion_applied}")
    print(f"Paper/Live enabled        : {report.paper_live_enabled}")
    if report.blockers:
        print("Blockers:")
        for item in report.blockers:
            print(f"- {item}")
    if report.warnings:
        print("Warnings:")
        for item in report.warnings[:20]:
            print(f"- {item}")
    print(f"Report                    : {args.output_dir}/fresh_oos_report.json")
    print(f"Feature store             : {args.output_dir}/feature_store_v2")
    print("Safety                    : fixed benchmark only; no tuning, promotion, Paper or Live activation.")
    print("=" * 116)
    print(json.dumps({
        "status": report.status,
        "fresh_directional_rows": report.fresh_directional_rows,
        "promotion_applied": report.promotion_applied,
        "paper_live_enabled": report.paper_live_enabled,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
