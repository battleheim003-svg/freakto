"""Detached-process controller for the Showcase Paper worker."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from freakto.showcase_paper.risk import risk_policy
from freakto.showcase_paper.performance import performance_report
from freakto.showcase_paper.quality import maturity_report, quality_profile, runbook_alignment
from freakto.ui.control_center_state import ROOT
from freakto.ui.job_manager import pid_alive


def runtime_dir(root: Path = ROOT) -> Path:
    return root / ".freakto-runtime" / "showcase-paper"


def output_dir(root: Path = ROOT) -> Path:
    return root / "logs" / "showcase_paper"


def _read(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def showcase_status(root: Path = ROOT) -> dict[str, Any]:
    path = runtime_dir(root) / "worker.json"
    state = _read(path)
    if state.get("status") in {"STARTING", "RUNNING", "STOP_REQUESTED"} and not pid_alive(state.get("pid")):
        state.update(status="INTERRUPTED", ended_utc=datetime.now(timezone.utc).isoformat(), error="Showcase worker is no longer running.")
        _write(path, state)
    session = _read(output_dir(root) / "session.json")
    trades = list(session.get("trades") or [])
    state.update(
        open_trades=sum(1 for trade in trades if trade.get("status") == "OPEN"),
        closed_trades=sum(1 for trade in trades if trade.get("status") == "CLOSED"),
        total_trades=len(trades),
        latest_trade=trades[-1] if trades else None,
        official_evidence_eligible=False,
        live_orders_enabled=False,
        real_capital_enabled=False,
        last_scan=dict(session.get("last_scan") or {}),
        recent_errors=list(session.get("errors") or [])[-5:],
        risk_policy=dict(session.get("risk_policy") or {}),
        quality_policy=dict(session.get("quality_policy") or {}),
        session_guard=dict(session.get("session_guard") or {}),
    )
    baseline = int((session.get("session_guard") or {}).get("baseline_closed_trades", 0) or 0)
    settings = dict(session.get("settings") or state.get("settings") or {})
    alignment = runbook_alignment(
        quality_mode=str(settings.get("quality_mode", "WIN_RATE")),
        risk_level=int(settings.get("risk_level", 30) or 30),
        analysis_depth=int(settings.get("analysis_depth", 100) or 100),
    )
    state["runbook_alignment"] = alignment
    state["runbook_aligned"] = bool(alignment["runbook_aligned"])
    maturity_profiles = {
        key: maturity_report(trades, profile_key=key, session_baseline=baseline)
        for key in ("WIN_RATE", "BALANCED", "VOLUME")
    }
    state["quality_maturity_profiles"] = maturity_profiles
    state["quality_maturity"] = maturity_profiles.get(
        str(settings.get("quality_mode", "WIN_RATE")).upper(), maturity_profiles["WIN_RATE"],
    )
    # Rebuild read-only diagnostics from the current session on every status
    # read so worker states written by an older version cannot hide new fields.
    state["performance"] = performance_report(trades, session_baseline=baseline)
    return state


def list_showcase_trades(root: Path = ROOT) -> list[dict[str, Any]]:
    session = _read(output_dir(root) / "session.json")
    return list(reversed(list(session.get("trades") or [])))


def start_showcase(
    *,
    daily_trade_limit: int = 0,
    scan_interval_seconds: int = 300,
    maximum_holding_minutes: int = 60,
    leverage: float = 1.0,
    risk_level: int = 35,
    analysis_depth: int = 100,
    session_equity_usdt: float = 1_000.0,
    session_profit_target_pct: float | None = None,
    session_loss_limit_pct: float | None = None,
    market_mode: str = "LIVE_PUBLIC",
    quality_mode: str = "WIN_RATE",
    replay_timeframe: str = "AUTO",
    break_even_trigger_r: float = 0.75,
    root: Path = ROOT,
) -> dict[str, Any]:
    current = showcase_status(root)
    if current.get("status") in {"STARTING", "RUNNING", "STOP_REQUESTED"}:
        raise RuntimeError(f"Showcase Paper is already active (PID {current.get('pid')})")
    normalized_mode = str(market_mode).upper()
    if not 0 <= int(risk_level) <= 100:
        raise ValueError("risk_level must stay between 0 and 100")
    if not 0 <= int(analysis_depth) <= 100:
        raise ValueError("analysis_depth must stay between 0 and 100")
    policy = risk_policy(risk_level)
    quality = quality_profile(quality_mode)
    profit_target = policy.session_profit_target_pct if session_profit_target_pct is None else float(session_profit_target_pct)
    loss_limit = policy.session_loss_limit_pct if session_loss_limit_pct is None else float(session_loss_limit_pct)
    if not 100 <= float(session_equity_usdt) <= 1_000_000:
        raise ValueError("session_equity_usdt must stay between 100 and 1,000,000")
    if not 0 <= profit_target <= 20 or not 0 <= loss_limit <= 20:
        raise ValueError("session profit target and loss limit must stay between 0 and 20 percent")
    if normalized_mode not in {"LIVE_PUBLIC", "ACCELERATED_REPLAY"}:
        raise ValueError("market_mode must be LIVE_PUBLIC or ACCELERATED_REPLAY")
    if str(replay_timeframe).upper() not in {"AUTO", "15M", "1H", "4H"}:
        raise ValueError("replay_timeframe must be AUTO, 15m, 1h, or 4h")
    if not 0 <= float(break_even_trigger_r) <= 3:
        raise ValueError("break_even_trigger_r must stay between 0 and 3")
    if not 5 <= int(scan_interval_seconds) <= 3600:
        raise ValueError("scan_interval_seconds must stay between 5 and 3,600")
    runtime = runtime_dir(root)
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "stop.requested").unlink(missing_ok=True)
    command = [
        sys.executable, "-X", "utf8", "-m", "freakto.showcase_paper.worker",
        "--root", str(root), "--daily-trade-limit", str(int(daily_trade_limit)),
        "--scan-interval-seconds", str(int(scan_interval_seconds)),
        "--maximum-holding-minutes", str(int(maximum_holding_minutes)),
        "--leverage", str(float(leverage)),
        "--risk-level", str(int(risk_level)),
        "--analysis-depth", str(int(analysis_depth)),
        "--session-equity-usdt", str(float(session_equity_usdt)),
        "--session-profit-target-pct", str(profit_target),
        "--session-loss-limit-pct", str(loss_limit),
        "--market-mode", normalized_mode,
        "--quality-mode", quality.key,
        "--replay-timeframe", str(replay_timeframe),
        "--break-even-trigger-r", str(float(break_even_trigger_r)),
    ]
    environment = os.environ.copy()
    environment.update({"LIVE_TRADING_ENABLED": "false", "REAL_CAPITAL_ENABLED": "false", "LIVE_DEMO_EXECUTION_ENABLED": "false", "PYTHONUTF8": "1"})
    with (runtime / "worker.stdout.log").open("a", encoding="utf-8") as stdout, (runtime / "worker.stderr.log").open("a", encoding="utf-8") as stderr:
        process = subprocess.Popen(command, cwd=root, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    alignment = runbook_alignment(
        quality_mode=quality.key, risk_level=int(risk_level), analysis_depth=int(analysis_depth),
    )
    state = {
        "schema_version": 1,
        "status": "STARTING",
        "pid": process.pid,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "heartbeat_utc": None,
        "ended_utc": None,
        "settings": {
            "daily_trade_limit": int(daily_trade_limit), "scan_interval_seconds": int(scan_interval_seconds),
            "maximum_holding_minutes": int(maximum_holding_minutes), "leverage": float(leverage),
            "risk_level": int(risk_level), "analysis_depth": int(analysis_depth), "market_mode": normalized_mode,
            "quality_mode": quality.key, "replay_timeframe": str(replay_timeframe),
            "break_even_trigger_r": float(break_even_trigger_r),
            "session_equity_usdt": float(session_equity_usdt),
            "session_profit_target_pct": profit_target,
            "session_loss_limit_pct": loss_limit,
            "minimum_closed_trades_for_profit_stop": policy.minimum_closed_trades_for_profit_stop,
        },
        "error": None,
        "runbook_alignment": alignment,
        "runbook_aligned": bool(alignment["runbook_aligned"]),
        "live_orders_enabled": False,
        "real_capital_enabled": False,
        "official_evidence_eligible": False,
    }
    _write(runtime / "worker.json", state)
    return state


def stop_showcase(root: Path = ROOT) -> dict[str, Any]:
    state = showcase_status(root)
    if state.get("status") not in {"STARTING", "RUNNING"}:
        raise ValueError("Showcase Paper is not running")
    runtime = runtime_dir(root)
    (runtime / "stop.requested").write_text(datetime.now(timezone.utc).isoformat(), encoding="utf-8")
    state.update(status="STOP_REQUESTED", heartbeat_utc=datetime.now(timezone.utc).isoformat())
    _write(runtime / "worker.json", state)
    return state


def write_worker_state(payload: dict[str, Any], root: Path = ROOT) -> None:
    _write(runtime_dir(root) / "worker.json", payload)
