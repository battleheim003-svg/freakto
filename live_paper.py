"""Freakto shadow/paper Decision-to-Execution CLI. Real orders are impossible."""
from __future__ import annotations

import argparse
import json
import time

from engine.live_demo import CcxtPublicMarketData, DEFAULT_PUBLIC_EXCHANGES
from engine.live_demo_universe import load_universe, select_symbols
from engine.live_paper_runtime import (
    LivePaperRuntime, RuntimeAlreadyRunningError, RuntimeLock,
    load_runtime_config, shadow_gate_status,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("shadow", "paper"), default="shadow")
    parser.add_argument("--groups", default="core")
    parser.add_argument("--symbols", default="")
    parser.add_argument("--exchange", default="kucoin")
    parser.add_argument("--config", default="live_paper_config.json")
    parser.add_argument("--universe-file", default="live_demo_universe.json")
    parser.add_argument("--gate-status", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop", action="store_true", help="Repeat safely; duplicate candle decisions are ignored")
    parser.add_argument("--interval", type=float, default=300.0, help="Seconds between complete universe cycles")
    args = parser.parse_args()
    config = load_runtime_config(args.config)
    universe = load_universe(args.universe_file)
    exchanges = (args.exchange, *(x for x in DEFAULT_PUBLIC_EXCHANGES if x != args.exchange))
    try:
        from telegram_notifier import send_telegram_message
    except Exception:
        send_telegram_message = None
    runtime = LivePaperRuntime(config, universe, CcxtPublicMarketData(exchanges), mode=args.mode, notifier=send_telegram_message)
    if args.gate_status:
        print(json.dumps(shadow_gate_status(runtime.store, config), ensure_ascii=False, indent=2))
        return 0
    groups = ("core", "growth", "meme") if args.groups == "all" else args.groups.split(",")
    symbols = select_symbols(universe, groups=groups, explicit_symbols=args.symbols.split(",") if args.symbols else ())
    if args.loop and args.once:
        parser.error("choose either --once or --loop")
    if args.interval <= 0:
        parser.error("--interval must be positive")
    results = []
    try:
        with RuntimeLock(runtime.root / "runtime.lock"):
            while True:
                results = []
                runtime.manage_exits()
                for symbol in symbols:
                    try:
                        results.append(runtime.process_symbol(symbol))
                    except Exception as exc:
                        runtime.store.record_handled_symbol_failure(symbol, exc)
                        result = {"symbol": symbol, "status": "HANDLED_SYMBOL_FAILURE", "error": f"{type(exc).__name__}: {exc}"}
                        results.append(result)
                        if send_telegram_message:
                            send_telegram_message(f"Freakto live-paper symbol failure (handled)\n{symbol}\n{result['error']}")
                print(json.dumps({"mode": args.mode, "paper_execution_authorized": runtime._execution_authorized(), "results": results}, ensure_ascii=False, indent=2, default=str), flush=True)
                if not args.loop:
                    break
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Freakto live-paper runtime stopped safely.")
    except RuntimeAlreadyRunningError as exc:
        print(f"Freakto live-paper worker is already running: {exc}")
        return 2
    except Exception as exc:
        runtime.store.record_unhandled_crash(exc)
        if send_telegram_message:
            send_telegram_message(f"Freakto live-paper UNHANDLED runtime crash\n{type(exc).__name__}: {exc}")
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
