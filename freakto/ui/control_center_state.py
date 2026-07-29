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
from freakto.paper.state_paths import paper_state_paths
from freakto.ui.paper_demo import collect_paper_demo_snapshot


ROOT = Path(__file__).resolve().parents[2]
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
    runner: str = "freakto"


WORKFLOW_KINDS = (
    "DATA_REPLAY",
    "REPORT_REFRESH",
    "MARKET_DATA_AUDIT",
    "MARKET_REPLAY",
    "FORWARD_SHADOW_CYCLE",
    "AIRDROP_OUTCOMES",
    "CROSS_ASSET_RANK",
    "CROSS_ASSET_EVALUATE",
)

SCRIPT_ALLOWLIST = {
    "market_adapter_dashboard.py",
    "airdrop_backtest_dashboard.py",
    "cross_asset_opportunity_ranker.py",
}


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


def _safe_iso_date(value: object, fallback: str) -> str:
    text = str(value or fallback).strip()
    try:
        datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"Invalid ISO date: {text}") from exc
    return text


def _safe_workspace_csv(value: object, *, root: Path) -> str:
    candidate = Path(str(value or "").strip())
    if not candidate:
        raise ValueError("A CSV path is required.")
    resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("CSV inputs must stay inside the Freakto workspace.") from exc
    if resolved.suffix.lower() != ".csv":
        raise ValueError("Only CSV inputs are accepted.")
    if not resolved.is_file():
        raise ValueError(f"CSV input does not exist: {resolved}")
    return str(resolved)


def workflow_plan(
    kind: str,
    options: dict | None = None,
    *,
    root: Path = ROOT,
) -> tuple[QuickStep, ...]:
    """Build one of the fixed research-only dashboard workflows."""
    canonical = str(kind).strip().upper()
    values = dict(options or {})
    if canonical not in WORKFLOW_KINDS:
        raise ValueError(f"Unsupported control-center workflow: {canonical}")

    if canonical == "DATA_REPLAY":
        return (
            QuickStep("data_status", ("data", "status")),
            QuickStep("data_build", ("data", "build"), long_running=True),
            QuickStep("replay_status", ("replay", "status")),
            QuickStep("replay_run", ("replay", "run", "--compact"), long_running=True),
        )
    if canonical == "REPORT_REFRESH":
        return (
            QuickStep("paper_report", ("report", "paper", "--no-plot"), accepted_exit_codes=(0, 2)),
            QuickStep("research_report", ("report", "research"), accepted_exit_codes=(0, 2)),
            QuickStep("forward_report", ("report", "forward"), accepted_exit_codes=(0, 2)),
            QuickStep("go_live_check", ("paper", "go-live-check"), accepted_exit_codes=(0, 2)),
        )

    if canonical == "MARKET_DATA_AUDIT":
        start = _safe_iso_date(values.get("start"), "2023-01-01")
        end = _safe_iso_date(values.get("end"), "2026-01-01")
        return (
            QuickStep(
                "audit_eur_usd",
                ("market_adapter_dashboard.py", "forex", "--symbol", "EUR/USD", "--timeframe", "1d", "--start", start, "--end", end),
                long_running=True,
                runner="script",
            ),
            QuickStep(
                "audit_xau_usd",
                ("market_adapter_dashboard.py", "gold", "--symbol", "XAU/USD", "--timeframe", "1d", "--start", start, "--end", end),
                long_running=True,
                runner="script",
            ),
        )
    if canonical == "MARKET_REPLAY":
        return (
            QuickStep(
                "replay_forex_gold",
                (
                    "replay", "run", "--symbols", "EUR/USD,XAU/USD",
                    "--timeframe", "1d", "--start", "2023-01-01", "--end", "2025-12-31",
                    "--fee-bps", "0.525", "--slippage-bps", "3.643",
                    "--fixed-execution-costs", "--compact",
                ),
                long_running=True,
            ),
            QuickStep("replay_status", ("replay", "status", "--symbols", "EUR/USD,XAU/USD", "--timeframe", "1d", "--compact")),
        )
    if canonical == "FORWARD_SHADOW_CYCLE":
        return (
            QuickStep("paper_preflight", ("paper", "preflight")),
            QuickStep("arm_research", ("paper", "arm-research")),
            QuickStep("paper_cycle", ("paper", "cycle"), long_running=True),
            QuickStep("forward_report", ("report", "forward"), accepted_exit_codes=(0, 2)),
            QuickStep("paper_status", ("paper", "status"), accepted_exit_codes=(0, 2)),
        )
    if canonical == "AIRDROP_OUTCOMES":
        return (
            QuickStep(
                "airdrop_sync",
                ("airdrop_backtest_dashboard.py", "sync"),
                accepted_exit_codes=(0, 2),
                runner="script",
            ),
            QuickStep(
                "airdrop_report",
                ("airdrop_backtest_dashboard.py", "report", "--min-resolved", "30"),
                runner="script",
            ),
        )
    if canonical == "CROSS_ASSET_RANK":
        source = _safe_workspace_csv(values.get("input"), root=root)
        return (
            QuickStep(
                "cross_asset_rank",
                ("cross_asset_opportunity_ranker.py", "rank", "--input", source),
                accepted_exit_codes=(0, 2),
                runner="script",
            ),
        )
    rankings = _safe_workspace_csv(values.get("rankings"), root=root)
    outcomes = _safe_workspace_csv(values.get("outcomes"), root=root)
    return (
        QuickStep(
            "cross_asset_evaluate",
            (
                "cross_asset_opportunity_ranker.py", "evaluate",
                "--rankings", rankings, "--outcomes", outcomes,
            ),
            accepted_exit_codes=(0, 2),
            runner="script",
        ),
    )


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
    paths = paper_state_paths(root)
    paper_dir = paths.canonical_dir
    market_dir = root / "data" / "market_replay"
    data_files = list(market_dir.rglob("*.csv*")) if market_dir.exists() else []
    log_files = list((root / "logs").rglob("*.json")) if (root / "logs").exists() else []
    arm_resolution = paths.resolve_for_read("arm_state.json")
    arm = _json(arm_resolution.path)
    adapter_manifests = list(market_dir.rglob("*.adapter.json")) if market_dir.exists() else []
    forward_reports = list((root / "logs" / "forward_testing").glob("*.json"))
    airdrop_db = root / "history" / "airdrop_outcomes.db"
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
        "paper_demo": collect_paper_demo_snapshot(root),
        "runtime": {
            "json_artifacts": len(log_files),
            "latest_utc": _latest_timestamp(log_files),
        },
        "workflows": {
            "market_adapter_manifests": len(adapter_manifests),
            "forward_latest_utc": _latest_timestamp(forward_reports),
            "airdrop_tracker_exists": airdrop_db.is_file(),
            "cross_asset_input_exists": (root / "data" / "cross_asset" / "opportunities.csv").is_file(),
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


def run_script(
    arguments: Sequence[str],
    *,
    root: Path = ROOT,
    timeout: int = 900,
) -> CommandResult:
    values = tuple(str(value) for value in arguments)
    if not values or values[0] not in SCRIPT_ALLOWLIST:
        raise ValueError("Script is not allowlisted for Control Center execution.")
    script = (root / values[0]).resolve()
    try:
        script.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("Script must stay inside the Freakto workspace.") from exc
    command = (sys.executable, "-X", "utf8", str(script), *values[1:])
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
