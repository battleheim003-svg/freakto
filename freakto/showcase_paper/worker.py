"""Background worker for visual multi-trade Showcase Paper sessions."""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from freakto.research.adapters.showcase_market_data import build_showcase_market_data
from freakto.showcase_paper.controller import output_dir, runtime_dir, showcase_status, write_worker_state
from freakto.showcase_paper.engine import ShowcaseEngine, ShowcaseSettings


def _signal_source(symbol: str):
    from portfolio_scanner import analyze_symbol
    return analyze_symbol(symbol)


def run_worker(root: Path, settings: ShowcaseSettings, *, scan_interval_seconds: int) -> int:
    runtime = runtime_dir(root)
    state = showcase_status(root)
    state.update(status="RUNNING", pid=os.getpid(), heartbeat_utc=datetime.now(timezone.utc).isoformat(), error=None)
    write_worker_state(state, root)
    market_data = build_showcase_market_data()
    engine = ShowcaseEngine(output_dir(root), settings, market_data, _signal_source, logo_path=root / "assets" / "freakto-logo.png")
    try:
        while True:
            stop_requested = (runtime / "stop.requested").exists()
            engine.mark_and_close(close_all=stop_requested)
            if stop_requested:
                state.update(status="STOPPED", heartbeat_utc=datetime.now(timezone.utc).isoformat(), ended_utc=datetime.now(timezone.utc).isoformat())
                write_worker_state(state, root)
                return 0
            engine.open_available()
            state.update(status="RUNNING", heartbeat_utc=datetime.now(timezone.utc).isoformat())
            write_worker_state(state, root)
            remaining = max(5, int(scan_interval_seconds))
            while remaining > 0 and not (runtime / "stop.requested").exists():
                chunk = min(2, remaining)
                time.sleep(chunk)
                remaining -= chunk
    except Exception as exc:
        state.update(status="FAILED", heartbeat_utc=datetime.now(timezone.utc).isoformat(), ended_utc=datetime.now(timezone.utc).isoformat(), error=f"{type(exc).__name__}: {exc}")
        write_worker_state(state, root)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--daily-trade-limit", type=int, default=6)
    parser.add_argument("--scan-interval-seconds", type=int, default=300)
    parser.add_argument("--maximum-holding-minutes", type=int, default=60)
    parser.add_argument("--leverage", type=float, default=1.0)
    args = parser.parse_args()
    settings = ShowcaseSettings(daily_trade_limit=args.daily_trade_limit, maximum_holding_minutes=args.maximum_holding_minutes, leverage=args.leverage).validated()
    return run_worker(args.root.resolve(), settings, scan_interval_seconds=args.scan_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
