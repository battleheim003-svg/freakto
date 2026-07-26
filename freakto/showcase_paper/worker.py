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
from freakto.showcase_paper.replay_lab import AcceleratedReplayMarket
from freakto.showcase_paper.risk import risk_policy


def _signal_source(symbol: str):
    from portfolio_scanner import analyze_symbol
    return analyze_symbol(symbol)


def run_worker(root: Path, settings: ShowcaseSettings, *, scan_interval_seconds: int) -> int:
    runtime = runtime_dir(root)
    state = showcase_status(root)
    state.update(status="RUNNING", pid=os.getpid(), heartbeat_utc=datetime.now(timezone.utc).isoformat(), error=None)
    write_worker_state(state, root)
    replay_market = None
    if settings.market_mode == "ACCELERATED_REPLAY":
        replay_market = AcceleratedReplayMarket(root, settings.symbols)
        market_data = replay_market
        signal_source = replay_market.signal
    else:
        market_data = build_showcase_market_data()
        signal_source = _signal_source
    engine = ShowcaseEngine(output_dir(root), settings, market_data, signal_source, logo_path=root / "assets" / "freakto-logo.png")
    try:
        scan_count = 0
        while True:
            stop_requested = (runtime / "stop.requested").exists()
            state.update(phase="MARKING_POSITIONS", heartbeat_utc=datetime.now(timezone.utc).isoformat())
            write_worker_state(state, root)
            engine.mark_and_close(close_all=stop_requested)
            if stop_requested:
                state.update(status="STOPPED", heartbeat_utc=datetime.now(timezone.utc).isoformat(), ended_utc=datetime.now(timezone.utc).isoformat())
                write_worker_state(state, root)
                return 0
            state.update(phase="SCANNING", heartbeat_utc=datetime.now(timezone.utc).isoformat())
            write_worker_state(state, root)
            opened = engine.open_available()
            scan_count += 1
            if replay_market is not None:
                replay_market.advance()
            now = datetime.now(timezone.utc)
            state.update(
                status="RUNNING",
                phase="WAITING",
                heartbeat_utc=now.isoformat(),
                last_scan_utc=now.isoformat(),
                next_scan_utc=datetime.fromtimestamp(
                    now.timestamp() + max(5, int(scan_interval_seconds)), tz=timezone.utc
                ).isoformat(),
                scan_count=scan_count,
                last_scan=dict(engine.state.get("last_scan") or {}),
                opened_last_scan=len(opened),
                replay_progress=replay_market.progress() if replay_market is not None else None,
            )
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
    parser.add_argument("--risk-level", type=int, default=35)
    parser.add_argument("--market-mode", choices=("LIVE_PUBLIC", "ACCELERATED_REPLAY"), default="LIVE_PUBLIC")
    args = parser.parse_args()
    policy = risk_policy(args.risk_level)
    settings = ShowcaseSettings(
        daily_trade_limit=args.daily_trade_limit,
        maximum_open_positions=policy.maximum_open_positions,
        notional_usdt=policy.notional_usdt,
        maximum_holding_minutes=args.maximum_holding_minutes,
        leverage=args.leverage,
        stop_loss_pct=policy.stop_loss_pct,
        take_profit_pct=policy.take_profit_pct,
        risk_level=policy.level,
        reentry_cooldown_minutes=policy.reentry_cooldown_minutes,
        market_mode=args.market_mode,
    ).validated()
    return run_worker(args.root.resolve(), settings, scan_interval_seconds=args.scan_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
