"""Terminal entry point for Freakto's foundational live-data paper demo."""
from __future__ import annotations

import argparse

from engine.live_demo import (
    DEFAULT_PUBLIC_EXCHANGES,
    CcxtPublicMarketData,
    MarketSnapshot,
    MockBroker,
    run_live_loop,
)


def should_execute_trade(_market_data: MarketSnapshot, _broker: MockBroker) -> tuple[str, float]:
    """Integration seam for validated Freakto decisions.

    Return ("BUY", base_amount), ("SELL", base_amount), or ("HOLD", 0.0).
    The safe default intentionally never creates a trade.
    """
    return "HOLD", 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Freakto public-data-only live paper demo")
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--exchange", default="auto", help="Primary exchange or 'auto' for project fallback order")
    parser.add_argument("--interval", type=float, default=15.0)
    parser.add_argument("--balance", type=float, default=10_000.0)
    parser.add_argument("--fee-bps", type=float, default=10.0)
    parser.add_argument("--slippage-bps", type=float, default=5.0)
    parser.add_argument("--once", action="store_true", help="Fetch one snapshot and exit")
    args = parser.parse_args()

    if args.exchange.lower() == "auto":
        exchanges = DEFAULT_PUBLIC_EXCHANGES
    else:
        primary = args.exchange.lower()
        exchanges = (primary, *(item for item in DEFAULT_PUBLIC_EXCHANGES if item != primary))
    market_data = CcxtPublicMarketData(exchanges)
    broker = MockBroker(
        market_data,
        initial_balance=args.balance,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
    )
    print("Freakto Live Demo | PAPER ONLY | no exchange credentials or real orders", flush=True)
    print(f"Public provider order: {', '.join(exchanges)}", flush=True)
    run_live_loop(
        args.symbol,
        market_data,
        broker,
        should_execute_trade,
        interval_seconds=args.interval,
        once=args.once,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
