"""Background worker for visual multi-trade Showcase Paper sessions."""

from __future__ import annotations

import argparse
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from freakto.showcase_paper.controller import output_dir, runtime_dir, showcase_status, write_worker_state
from freakto.showcase_paper.engine import ShowcaseEngine, ShowcaseSettings
from freakto.showcase_paper.live_intraday import LiveIntradayTechnicalMarket
from freakto.showcase_paper.replay_lab import AcceleratedReplayMarket
from freakto.showcase_paper.risk import risk_policy


def run_worker(root: Path, settings: ShowcaseSettings, *, scan_interval_seconds: int) -> int:
    runtime = runtime_dir(root)
    state = showcase_status(root)
    state.update(status="RUNNING", pid=os.getpid(), heartbeat_utc=datetime.now(timezone.utc).isoformat(), error=None)
    write_worker_state(state, root)
    replay_market = None
    if settings.market_mode == "ACCELERATED_REPLAY":
        replay_market = AcceleratedReplayMarket(
            root, settings.symbols, risk_level=settings.risk_level,
            analysis_depth=settings.analysis_depth,
        )
        market_data = replay_market
        signal_source = replay_market.signal
    else:
        live_market = LiveIntradayTechnicalMarket(
            risk_level=settings.risk_level, analysis_depth=settings.analysis_depth
        )
        market_data = live_market
        signal_source = live_market.signal
    engine = ShowcaseEngine(output_dir(root), settings, market_data, signal_source, logo_path=root / "assets" / "freakto-logo.png")
    engine.start_session_guard()
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
            guard = engine.evaluate_session_guard()
            if guard.get("status") in {"PROFIT_TARGET_REACHED", "LOSS_LIMIT_REACHED"}:
                engine.mark_and_close(close_all=True)
                guard = engine.evaluate_session_guard()
                state.update(
                    status=str(guard["status"]),
                    phase="SESSION_GUARD_STOP",
                    session_guard=guard,
                    heartbeat_utc=datetime.now(timezone.utc).isoformat(),
                    ended_utc=datetime.now(timezone.utc).isoformat(),
                )
                write_worker_state(state, root)
                return 0
            state.update(phase="SCANNING", heartbeat_utc=datetime.now(timezone.utc).isoformat())
            write_worker_state(state, root)
            observations = [
                (float(trade.get("confidence", 0) or 0) / 100.0, float(trade.get("pnl_pct", 0) or 0) > 0)
                for trade in engine.trades
                if trade.get("status") == "CLOSED" and str(trade.get("engine_version", "")).startswith("technical-v2")
            ]
            adapter = getattr(market_data, "adapter", None)
            if adapter is not None and hasattr(adapter, "set_calibration_observations"):
                adapter.set_calibration_observations(observations)
                segmented = []
                for trade in engine.trades:
                    if trade.get("status") != "CLOSED" or not str(trade.get("engine_version", "")).startswith("technical-v2"):
                        continue
                    technical = dict(trade.get("technical_v2") or {})
                    setup = dict(technical.get("setup") or {})
                    segmented.append({
                        "probability": float(trade.get("confidence", 0) or 0) / 100.0,
                        "outcome": float(trade.get("pnl_pct", 0) or 0) > 0,
                        "symbol": str(trade.get("symbol", "")),
                        "setup": str(setup.get("name", "UNKNOWN")),
                        "regime": str((technical.get("regime") or {}).get("label", "UNKNOWN")),
                        "side": str(trade.get("side", "")),
                        "timeframe": str(setup.get("entry_timeframe", "UNKNOWN")),
                    })
                adapter.set_segmented_observations(segmented)
                adapter.set_portfolio_positions([trade for trade in engine.trades if trade.get("status") == "OPEN"])
            opened = engine.open_available()
            scan_count += 1
            if replay_market is not None:
                replay_market.advance()
            now = datetime.now(timezone.utc)
            scan_payload = dict(engine.state.get("last_scan") or {})
            state.update(
                status="RUNNING",
                phase="WAITING",
                heartbeat_utc=now.isoformat(),
                last_scan_utc=now.isoformat(),
                next_scan_utc=datetime.fromtimestamp(
                    now.timestamp() + max(5, int(scan_interval_seconds)), tz=timezone.utc
                ).isoformat(),
                scan_count=scan_count,
                last_scan=scan_payload,
                risk_policy=dict(scan_payload.get("risk_policy") or {}),
                opened_last_scan=len(opened),
                replay_progress=replay_market.progress() if replay_market is not None else None,
                session_guard=engine.evaluate_session_guard(),
            )
            write_worker_state(state, root)
            remaining = max(5, int(scan_interval_seconds))
            while remaining > 0 and not (runtime / "stop.requested").exists():
                chunk = min(0.25, remaining)
                time.sleep(chunk)
                remaining -= chunk
    except Exception as exc:
        state.update(status="FAILED", heartbeat_utc=datetime.now(timezone.utc).isoformat(), ended_utc=datetime.now(timezone.utc).isoformat(), error=f"{type(exc).__name__}: {exc}")
        write_worker_state(state, root)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--daily-trade-limit", type=int, default=0)
    parser.add_argument("--scan-interval-seconds", type=int, default=300)
    parser.add_argument("--maximum-holding-minutes", type=int, default=60)
    parser.add_argument("--leverage", type=float, default=1.0)
    parser.add_argument("--risk-level", type=int, default=35)
    parser.add_argument("--analysis-depth", type=int, default=100)
    parser.add_argument("--session-equity-usdt", type=float, default=1_000.0)
    parser.add_argument("--session-profit-target-pct", type=float)
    parser.add_argument("--session-loss-limit-pct", type=float)
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
        analysis_depth=args.analysis_depth,
        reentry_cooldown_minutes=policy.reentry_cooldown_minutes,
        market_mode=args.market_mode,
        session_equity_usdt=args.session_equity_usdt,
        session_profit_target_pct=(policy.session_profit_target_pct if args.session_profit_target_pct is None else args.session_profit_target_pct),
        session_loss_limit_pct=(policy.session_loss_limit_pct if args.session_loss_limit_pct is None else args.session_loss_limit_pct),
        minimum_closed_trades_for_profit_stop=policy.minimum_closed_trades_for_profit_stop,
    ).validated()
    return run_worker(args.root.resolve(), settings, scan_interval_seconds=args.scan_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
