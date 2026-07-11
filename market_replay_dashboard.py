"""CLI dashboard for Freakto v10.1.5 Historical Data Store + Market Replay."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from config import PORTFOLIO_SYMBOLS, TIMEFRAME
from engine.historical_data_store import (
    DEFAULT_DATA_DIR,
    HistoricalDataRequest,
    build_historical_data,
    format_historical_data_console,
    scan_historical_data,
)
from engine.market_replay import (
    MarketReplayConfig,
    format_market_replay_console,
    load_market_replay_status,
    run_market_replay,
)
from telegram_notifier import send_telegram_message


def _safe_print(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    print(str(text).encode(encoding, errors="replace").decode(encoding))


def _symbols(value: str) -> List[str]:
    return [item.strip() for item in str(value).split(",") if item.strip()]


def _horizons(value: str) -> List[int]:
    result = []
    for item in str(value).split(","):
        item = item.strip()
        if item:
            result.append(max(1, int(item)))
    return sorted(set(result)) or [1, 3, 6]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Freakto v10.1.5 Historical Data Store and Market Replay",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--build-data", action="store_true", help="Fetch/cache paginated historical OHLCV only")
    mode.add_argument("--replay", action="store_true", help="Replay existing local historical datasets")
    mode.add_argument("--full", action="store_true", help="Build historical data, then run replay")
    mode.add_argument("--status", action="store_true", help="Inspect local historical data and cumulative replay status")
    mode.add_argument("--resume", metavar="RUN_ID", default="", help="Resume an interrupted replay run")

    parser.add_argument("--symbols", default=",".join(PORTFOLIO_SYMBOLS))
    parser.add_argument("--timeframe", default=TIMEFRAME)
    parser.add_argument("--years", type=float, default=3.0)
    parser.add_argument("--start", default="", help="UTC start date, e.g. 2023-01-01")
    parser.add_argument("--end", default="", help="UTC end date; default is now")
    parser.add_argument("--exchange", default="auto", help="auto or one exchange id")
    parser.add_argument("--exchange-order", default="kucoin,okx,bybit,kraken")
    parser.add_argument("--batch-limit", type=int, default=1000)
    parser.add_argument("--min-coverage", type=float, default=90.0)
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--force-refresh", action="store_true")
    parser.add_argument("--no-update-cache", action="store_true")

    parser.add_argument("--min-window", type=int, default=120)
    parser.add_argument("--step", type=int, default=1, help="Replay every N candles")
    parser.add_argument("--min-side-score", type=int, default=50)
    parser.add_argument("--horizons", default="1,3,6", help="Future candle offsets")
    parser.add_argument("--directional-only", action="store_true", help="Do not store NEUTRAL replay rows")
    parser.add_argument("--max-decisions-per-symbol", type=int, default=0)
    parser.add_argument("--fee-bps", type=float, default=10.0, help="Fee per entry/exit side")
    parser.add_argument("--slippage-bps", type=float, default=5.0, help="Slippage per entry/exit side")
    parser.add_argument("--fixed-execution-costs", action="store_true", help="Disable volatility/liquidity slippage adjustment")
    parser.add_argument("--max-slippage-bps", type=float, default=100.0)
    parser.add_argument("--execution-delay-candles", type=int, default=1, help="Minimum bars between decision and executable fill")
    parser.add_argument("--fixed-evaluation-horizon", action="store_true", help="Disable regime-adaptive companion horizon")
    parser.add_argument("--context-file", default="", help="Optional timestamped historical context CSV")
    parser.add_argument("--context-max-age-hours", type=float, default=24.0)
    parser.add_argument("--checkpoint-every", type=int, default=250)
    parser.add_argument("--no-strict-audit", action="store_true", help="Continue even if causal-feature audit fails")
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    parser.add_argument("--send", action="store_true")
    return parser


def _data_request(args, symbols: List[str]) -> HistoricalDataRequest:
    return HistoricalDataRequest(
        symbols=symbols,
        timeframe=args.timeframe,
        start_utc=args.start,
        end_utc=args.end,
        years=args.years,
        exchange=args.exchange,
        exchange_order=_symbols(args.exchange_order),
        batch_limit=args.batch_limit,
        min_acceptable_coverage_pct=args.min_coverage,
        data_dir=args.data_dir,
        update_existing=not args.no_update_cache,
        force_refresh=args.force_refresh,
    )


def _replay_config(args, symbols: List[str]) -> MarketReplayConfig:
    return MarketReplayConfig(
        symbols=symbols,
        timeframe=args.timeframe,
        start_utc=args.start,
        end_utc=args.end,
        data_dir=args.data_dir,
        min_window=args.min_window,
        step=args.step,
        min_side_score=args.min_side_score,
        horizons=_horizons(args.horizons),
        include_neutral=not args.directional_only,
        max_decisions_per_symbol=args.max_decisions_per_symbol,
        fee_bps_per_side=args.fee_bps,
        slippage_bps_per_side=args.slippage_bps,
        dynamic_execution_costs=not args.fixed_execution_costs,
        max_slippage_bps_per_side=args.max_slippage_bps,
        execution_delay_candles=max(1, args.execution_delay_candles),
        adaptive_evaluation_horizon=not args.fixed_evaluation_horizon,
        context_file=args.context_file,
        context_max_age_hours=args.context_max_age_hours,
        checkpoint_every=args.checkpoint_every,
        strict_leakage_audit=not args.no_strict_audit,
    )


def main() -> None:
    args = build_parser().parse_args()
    symbols = _symbols(args.symbols)
    if not symbols:
        raise SystemExit("No symbols were provided.")

    output_blocks: List[str] = []

    if args.status or not any([args.build_data, args.replay, args.full, args.resume]):
        data_status = scan_historical_data(
            symbols=symbols,
            timeframe=args.timeframe,
            years=args.years,
            data_dir=args.data_dir,
            start_utc=args.start,
            end_utc=args.end,
        )
        replay_status = load_market_replay_status()
        output_blocks = [
            format_historical_data_console(data_status, compact=args.compact),
            format_market_replay_console(replay_status, compact=args.compact),
        ]

    if args.build_data or args.full:
        data_report = build_historical_data(_data_request(args, symbols))
        output_blocks.append(format_historical_data_console(data_report, compact=args.compact))
        if args.full and data_report.completed_symbols == 0:
            text = "\n\n".join(output_blocks)
            _safe_print(text)
            raise SystemExit("Historical data build returned no usable datasets; replay was not started.")

    if args.replay or args.full or args.resume:
        run, summary, _ = run_market_replay(
            _replay_config(args, symbols),
            run_id=args.resume,
            resume=bool(args.resume),
            save=not args.no_save,
        )
        output_blocks.append(format_market_replay_console(summary, compact=args.compact))
        if not run.ok:
            text = "\n\n".join(output_blocks)
            _safe_print(text)
            raise SystemExit(1)

    text = "\n\n".join(output_blocks)
    _safe_print(text)
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
