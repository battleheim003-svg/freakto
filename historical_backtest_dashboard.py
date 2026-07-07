"""
historical_backtest_dashboard.py

Freakto v5.3 - CLI dashboard for Historical Backfill & Backtest.
"""

import argparse

from config import PORTFOLIO_SYMBOLS, TIMEFRAME
from engine.historical_backtest import (
    HistoricalBacktestConfig,
    format_summary_console,
    load_all_backtest_summary,
    parse_symbols,
    run_historical_backtest,
)
from telegram_notifier import send_telegram_message


def build_parser():
    parser = argparse.ArgumentParser(description="Freakto Historical Backfill & Backtest v5.3")
    parser.add_argument("--symbols", default=",".join(PORTFOLIO_SYMBOLS), help="Comma-separated symbols")
    parser.add_argument("--timeframe", default=TIMEFRAME)
    parser.add_argument("--limit", type=int, default=800, help="OHLCV candles per symbol")
    parser.add_argument("--min-window", type=int, default=120, help="Minimum historical candles before first replay decision")
    parser.add_argument("--step", type=int, default=6, help="Replay every N candles. 6 on 4h ~= daily decisions")
    parser.add_argument("--min-side-score", type=int, default=50)
    parser.add_argument("--max-rows-per-symbol", type=int, default=0, help="0 means no cap")
    parser.add_argument("--actionable-only", action="store_true", help="Skip MONITOR_ONLY rows in output")
    parser.add_argument("--status", action="store_true", help="Show cumulative backtest status only")
    parser.add_argument("--send", action="store_true", help="Send summary to Telegram")
    return parser


def main():
    args = build_parser().parse_args()

    if args.status:
        summary = load_all_backtest_summary()
        text = format_summary_console(summary)
        print(text)
        if args.send:
            send_telegram_message(text)
        return

    config = HistoricalBacktestConfig(
        symbols=parse_symbols(args.symbols, PORTFOLIO_SYMBOLS),
        timeframe=args.timeframe,
        limit=args.limit,
        min_window=args.min_window,
        step=args.step,
        min_side_score=args.min_side_score,
        max_rows_per_symbol=args.max_rows_per_symbol,
        include_monitor_only=not args.actionable_only,
    )

    run, summary, _ = run_historical_backtest(config)
    text = format_summary_console(summary)
    print(text)

    if args.send:
        send_telegram_message(text)

    if not run.ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
