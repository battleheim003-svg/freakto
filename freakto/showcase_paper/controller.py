"""Detached-process controller for the Showcase Paper worker."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


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
    )
    return state


def list_showcase_trades(root: Path = ROOT) -> list[dict[str, Any]]:
    session = _read(output_dir(root) / "session.json")
    return list(reversed(list(session.get("trades") or [])))


def start_showcase(
    *,
    daily_trade_limit: int = 6,
    scan_interval_seconds: int = 300,
    maximum_holding_minutes: int = 60,
    leverage: float = 1.0,
    risk_level: int = 35,
    market_mode: str = "LIVE_PUBLIC",
    root: Path = ROOT,
) -> dict[str, Any]:
    current = showcase_status(root)
    if current.get("status") in {"STARTING", "RUNNING", "STOP_REQUESTED"}:
        raise RuntimeError(f"Showcase Paper is already active (PID {current.get('pid')})")
    normalized_mode = str(market_mode).upper()
    if not 0 <= int(risk_level) <= 100:
        raise ValueError("risk_level must stay between 0 and 100")
    if normalized_mode not in {"LIVE_PUBLIC", "ACCELERATED_REPLAY"}:
        raise ValueError("market_mode must be LIVE_PUBLIC or ACCELERATED_REPLAY")
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
        "--market-mode", normalized_mode,
    ]
    environment = os.environ.copy()
    environment.update({"LIVE_TRADING_ENABLED": "false", "REAL_CAPITAL_ENABLED": "false", "LIVE_DEMO_EXECUTION_ENABLED": "false", "PYTHONUTF8": "1"})
    with (runtime / "worker.stdout.log").open("a", encoding="utf-8") as stdout, (runtime / "worker.stderr.log").open("a", encoding="utf-8") as stderr:
        process = subprocess.Popen(command, cwd=root, env=environment, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
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
            "risk_level": int(risk_level), "market_mode": normalized_mode,
        },
        "error": None,
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
