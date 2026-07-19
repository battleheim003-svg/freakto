"""Build or audit replay-safe historical data for the live-demo universe."""
from __future__ import annotations

import argparse

from engine.historical_data_store import format_historical_data_console
from engine.live_demo_universe import build_history, history_status, load_universe, select_symbols


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit/backfill Freakto live-demo universe history")
    parser.add_argument("--universe-file", default="live_demo_universe.json")
    parser.add_argument("--groups", default="all", help="core,growth,meme or all")
    parser.add_argument("--symbols", default="", help="Comma-separated override")
    parser.add_argument("--data-dir", default="data/market_replay")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--status", action="store_true", help="Read-only local history audit")
    mode.add_argument("--build", action="store_true", help="Download/update replay-safe OHLCV history")
    args = parser.parse_args()

    universe = load_universe(args.universe_file)
    groups = ("core", "growth", "meme") if args.groups.lower() == "all" else args.groups.split(",")
    symbols = select_symbols(
        universe,
        groups=groups,
        explicit_symbols=args.symbols.split(",") if args.symbols else (),
    )
    print(f"Universe history target: {len(symbols)} symbols | {universe.target_years:.1f}Y | {universe.timeframe}")
    report = (
        build_history(universe, symbols, args.data_dir)
        if args.build
        else history_status(universe, symbols, args.data_dir)
    )
    print(format_historical_data_console(report))
    return 0 if report.failed_symbols == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
