"""Read-only state and safe command execution for the local control center."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from freakto.core import PAPER_SAFETY
from freakto.paper.go_live import evaluate_files


ROOT = Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "logs" / "paper_launch_v2"


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


@dataclass(frozen=True)
class QuickStep:
    key: str
    arguments: tuple[str, ...]
    accepted_exit_codes: tuple[int, ...] = (0,)
    long_running: bool = False


def quick_start_plan(*, include_data_build: bool = True, include_replay: bool = True) -> tuple[QuickStep, ...]:
    """Return the ordered, zero-capital bootstrap pipeline."""
    steps = [QuickStep("data_status", ("data", "status"))]
    if include_data_build:
        steps.append(QuickStep("data_build", ("data", "build"), long_running=True))
    steps.append(QuickStep("replay_status", ("replay", "status")))
    if include_replay:
        steps.append(QuickStep("replay_run", ("replay", "run", "--compact"), long_running=True))
    steps.extend(
        [
            QuickStep("paper_preflight", ("paper", "preflight")),
            QuickStep("arm_research", ("paper", "arm-research")),
            QuickStep("paper_cycle", ("paper", "cycle"), long_running=True),
            QuickStep("paper_status", ("paper", "status")),
            QuickStep("paper_report", ("report", "paper", "--no-plot")),
            QuickStep("forward_report", ("report", "forward")),
            QuickStep("go_live_check", ("paper", "go-live-check"), accepted_exit_codes=(0, 2)),
        ]
    )
    return tuple(steps)


def _json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _latest_timestamp(paths: list[Path]) -> str | None:
    existing = [path for path in paths if path.is_file()]
    if not existing:
        return None
    stamp = max(path.stat().st_mtime for path in existing)
    return datetime.fromtimestamp(stamp, tz=timezone.utc).isoformat()


def collect_snapshot(root: Path = ROOT) -> dict:
    paper_dir = root / "logs" / "paper_launch_v2"
    market_dir = root / "data" / "market_replay"
    data_files = list(market_dir.rglob("*.csv")) if market_dir.exists() else []
    log_files = list((root / "logs").rglob("*.json")) if (root / "logs").exists() else []
    arm = _json(paper_dir / "arm_state.json")
    go_live = evaluate_files(
        root / "config" / "paper_go_live_policy.json",
        paper_dir / "go_live_evidence.json",
    )
    return {
        "safety": PAPER_SAFETY.payload(),
        "data": {
            "datasets": len(data_files),
            "latest_utc": _latest_timestamp(data_files),
            "path": str(market_dir),
        },
        "paper": {
            "armed": bool(arm.get("armed")),
            "mode": arm.get("mode", "DISARMED"),
            "updated_utc": arm.get("updated_utc") or arm.get("created_utc"),
        },
        "runtime": {
            "json_artifacts": len(log_files),
            "latest_utc": _latest_timestamp(log_files),
        },
        "go_live": go_live,
    }


def run_cli(arguments: Sequence[str], *, root: Path = ROOT, timeout: int = 900) -> CommandResult:
    command = (sys.executable, "-X", "utf8", "-m", "freakto.cli", *arguments)
    environment = os.environ.copy()
    environment.update(
        {
            "LIVE_TRADING_ENABLED": "false",
            "REAL_CAPITAL_ENABLED": "false",
            "PYTHONUTF8": "1",
        }
    )
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            command=command,
            exit_code=124,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + f"\nTimed out after {timeout} seconds.",
            timed_out=True,
        )
    return CommandResult(command, completed.returncode, completed.stdout, completed.stderr)
