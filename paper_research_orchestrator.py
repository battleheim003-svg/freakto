"""Freakto automated research-paper cycle orchestrator.

One process coordinates the complete zero-real-order paper workflow:

* readiness preflight and fail-closed arming;
* one-shot market monitor;
* ordinary decision evaluation;
* event/cost-gated paper observation scan;
* paper-trade evaluation and readiness status;
* periodic incremental historical-cache refresh and Fresh OOS replay;
* UTC candle-boundary scheduling, process locking, retries and audit logs.

The orchestrator never imports an exchange order API and cannot enable Live.
"""
from __future__ import annotations

import argparse
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from engine.paper_observation_v2 import arm_paper_mode, load_arm_state
from engine.paper_readiness_v2 import build_paper_launch_readiness, write_paper_readiness_outputs

VERSION = "1.0.0"
DEFAULT_OUTPUT_DIR = Path("logs") / "paper_cycle"
DEFAULT_PAPER_DIR = Path("logs") / "paper_launch_v2"
DEFAULT_EVENT_DIR = Path("logs") / "event_opportunity_v2"
DEFAULT_COST_DIR = Path("logs") / "cost_gate_diagnostics"
DEFAULT_FRESH_REPORT = Path("logs") / "fresh_oos_v2" / "fresh_oos_report.json"


@dataclass(frozen=True)
class OrchestratorConfig:
    project_root: str = "."
    output_dir: str = str(DEFAULT_OUTPUT_DIR)
    paper_output_dir: str = str(DEFAULT_PAPER_DIR)
    event_dir: str = str(DEFAULT_EVENT_DIR)
    cost_dir: str = str(DEFAULT_COST_DIR)
    fresh_report: str = str(DEFAULT_FRESH_REPORT)
    decision_file: str = str(Path("logs") / "decisions.csv")
    timeframe_minutes: int = 240
    settle_delay_seconds: int = 120
    run_immediately: bool = True
    step_timeout_seconds: int = 1800
    step_retries: int = 1
    retry_delay_seconds: int = 20
    run_decision_evaluator: bool = True
    maintenance_enabled: bool = True
    maintenance_every_cycles: int = 6
    historical_years: float = 5.0
    symbols: tuple[str, ...] = ("BTC/USDT", "ETH/USDT", "SOL/USDT")
    timeframes: tuple[str, ...] = ("4h",)
    data_dir: str = str(Path("data") / "market_replay")
    auto_arm_research: bool = True
    auto_upgrade_strategy: bool = True
    max_log_bytes: int = 5_000_000
    log_backups: int = 5


@dataclass
class StepResult:
    name: str
    command: List[str]
    started_utc: str
    finished_utc: str
    exit_code: int
    attempts: int
    status: str
    duration_seconds: float
    stdout_tail: List[str] = field(default_factory=list)
    stderr_tail: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CycleResult:
    cycle_id: str
    started_utc: str
    finished_utc: str
    status: str
    maintenance_run: bool
    readiness_status: str
    arm_mode: str
    live_orders_enabled: bool
    steps: List[StepResult] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProcessLock(AbstractContextManager["ProcessLock"]):
    """Cross-platform best-effort single-process lock with stale PID recovery."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.acquired = False

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False
        return True

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            try:
                fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                payload = {
                    "pid": os.getpid(),
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "version": VERSION,
                }
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(payload, handle, ensure_ascii=False, indent=2)
                self.acquired = True
                return
            except FileExistsError:
                try:
                    payload = json.loads(self.path.read_text(encoding="utf-8"))
                    pid = int(payload.get("pid", 0))
                except Exception:
                    pid = 0
                if self._pid_alive(pid):
                    raise RuntimeError(f"Paper orchestrator is already running (PID {pid}).")
                self.path.unlink(missing_ok=True)
        raise RuntimeError("Could not acquire paper orchestrator lock.")

    def release(self) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)
            self.acquired = False

    def __enter__(self) -> "ProcessLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def next_candle_run(
    now: datetime,
    *,
    timeframe_minutes: int = 240,
    settle_delay_seconds: int = 120,
) -> datetime:
    """Return the next UTC candle boundary plus a settlement delay."""
    if timeframe_minutes <= 0:
        raise ValueError("timeframe_minutes must be positive")
    if settle_delay_seconds < 0:
        raise ValueError("settle_delay_seconds cannot be negative")
    current = now.astimezone(timezone.utc)
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    elapsed_seconds = int((current - epoch).total_seconds())
    interval_seconds = timeframe_minutes * 60
    boundary_seconds = (elapsed_seconds // interval_seconds) * interval_seconds
    boundary = epoch + timedelta(seconds=boundary_seconds)
    candidate = boundary + timedelta(seconds=settle_delay_seconds)
    if current >= candidate:
        candidate = boundary + timedelta(seconds=interval_seconds + settle_delay_seconds)
    return candidate


def should_run_maintenance(cycle_number: int, every_cycles: int, enabled: bool = True) -> bool:
    if not enabled:
        return False
    if every_cycles <= 0:
        raise ValueError("maintenance_every_cycles must be positive")
    return cycle_number == 1 or cycle_number % every_cycles == 0


def _tail(text: str, lines: int = 40) -> List[str]:
    return str(text or "").splitlines()[-max(1, lines):]


def _command_text(command: Sequence[str]) -> str:
    return subprocess.list2cmdline(list(command)) if os.name == "nt" else shlex.join(command)


def _configure_logging(output_dir: Path, max_bytes: int, backups: int) -> logging.Logger:
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("freakto.paper_cycle")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)sZ | %(levelname)s | %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    file_handler = RotatingFileHandler(
        output_dir / "paper_cycle.log",
        maxBytes=max(1, max_bytes),
        backupCount=max(1, backups),
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(stream)
    logger.addHandler(file_handler)
    return logger


def _run_subprocess(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=max(1, timeout_seconds),
        check=False,
    )


def run_step(
    name: str,
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: int,
    retries: int,
    retry_delay_seconds: int,
    logger: logging.Logger,
    runner: Callable[..., subprocess.CompletedProcess[str]] = _run_subprocess,
) -> StepResult:
    started = utc_now()
    last: Optional[subprocess.CompletedProcess[str]] = None
    attempts = 0
    total_attempts = max(1, retries + 1)
    for attempt in range(1, total_attempts + 1):
        attempts = attempt
        logger.info("STEP %s attempt %s/%s: %s", name, attempt, total_attempts, _command_text(command))
        try:
            last = runner(command, cwd=cwd, timeout_seconds=timeout_seconds)
            if last.stdout:
                logger.info("%s stdout:\n%s", name, last.stdout.rstrip())
            if last.stderr:
                logger.warning("%s stderr:\n%s", name, last.stderr.rstrip())
            if last.returncode == 0:
                break
        except subprocess.TimeoutExpired as exc:
            last = subprocess.CompletedProcess(list(command), 124, exc.stdout or "", exc.stderr or "timeout")
            logger.error("STEP %s timed out after %ss", name, timeout_seconds)
        except Exception as exc:  # fail closed, but keep later audit/evaluation steps running
            last = subprocess.CompletedProcess(list(command), 125, "", f"{type(exc).__name__}: {exc}")
            logger.exception("STEP %s failed to start", name)
        if attempt < total_attempts:
            time.sleep(max(0, retry_delay_seconds))
    finished = utc_now()
    assert last is not None
    status = "PASSED" if last.returncode == 0 else "FAILED"
    logger.info("STEP %s %s exit=%s", name, status, last.returncode)
    return StepResult(
        name=name,
        command=list(command),
        started_utc=iso_utc(started),
        finished_utc=iso_utc(finished),
        exit_code=int(last.returncode),
        attempts=attempts,
        status=status,
        duration_seconds=round((finished - started).total_seconds(), 3),
        stdout_tail=_tail(last.stdout),
        stderr_tail=_tail(last.stderr),
    )


def cycle_commands(config: OrchestratorConfig, python_executable: str) -> List[tuple[str, List[str], bool]]:
    root = Path(config.project_root)
    commands: List[tuple[str, List[str], bool]] = [
        ("market_monitor", [python_executable, "-X", "utf8", str(root / "monitor.py"), "--once"], True),
    ]
    if config.run_decision_evaluator:
        commands.append(("decision_evaluator", [python_executable, "-X", "utf8", str(root / "decision_evaluator.py")], False))
    commands.extend(
        [
            (
                "paper_scan",
                [
                    python_executable,
                    "-X",
                    "utf8",
                    str(root / "paper_trade_launch_dashboard.py"),
                    "--scan",
                    "--decision-file",
                    config.decision_file,
                ],
                False,
            ),
            (
                "paper_evaluator",
                [python_executable, "-X", "utf8", str(root / "paper_trade_launch_dashboard.py"), "--evaluate"],
                False,
            ),
            (
                "paper_status",
                [python_executable, "-X", "utf8", str(root / "paper_trade_launch_dashboard.py"), "--status"],
                False,
            ),
        ]
    )
    return commands


def maintenance_commands(config: OrchestratorConfig, python_executable: str) -> List[tuple[str, List[str], bool]]:
    root = Path(config.project_root)
    symbols = ",".join(config.symbols)
    timeframes = ",".join(config.timeframes)
    return [
        (
            "historical_incremental_update",
            [
                python_executable,
                "-X",
                "utf8",
                str(root / "paper_research_orchestrator.py"),
                "--update-history-only",
                "--symbols",
                symbols,
                "--timeframes",
                timeframes,
                "--data-dir",
                config.data_dir,
                "--historical-years",
                str(config.historical_years),
            ],
            False,
        ),
        (
            "fresh_oos_replay",
            [
                python_executable,
                "-X",
                "utf8",
                str(root / "fresh_oos_replay_analysis.py"),
                "--run-replay",
                "--symbols",
                symbols,
                "--timeframes",
                timeframes,
                "--data-dir",
                config.data_dir,
            ],
            False,
        ),
    ]


def update_historical_cache(config: OrchestratorConfig) -> Dict[str, Any]:
    """Incrementally refresh local OHLCV archives; never touches orders or Paper state."""
    from engine.historical_data_store import HistoricalDataRequest, build_historical_data

    reports: Dict[str, Any] = {"status": "COMPLETE", "timeframes": {}, "live_orders_enabled": False}
    for timeframe in config.timeframes:
        request = HistoricalDataRequest(
            symbols=list(config.symbols),
            timeframe=timeframe,
            years=max(0.1, float(config.historical_years)),
            data_dir=config.data_dir,
            update_existing=True,
            force_refresh=False,
            discover_listing_boundary=False,
        )
        report = build_historical_data(request)
        reports["timeframes"][timeframe] = {
            "completed_symbols": report.completed_symbols,
            "failed_symbols": report.failed_symbols,
            "total_rows": report.total_rows,
            "blockers": report.blockers,
            "warnings": report.warnings,
        }
        if report.failed_symbols:
            reports["status"] = "PARTIAL"
    return reports


class PaperResearchOrchestrator:
    def __init__(
        self,
        config: OrchestratorConfig,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = _run_subprocess,
        sleeper: Callable[[float], None] = time.sleep,
        now_fn: Callable[[], datetime] = utc_now,
    ):
        self.config = config
        self.root = Path(config.project_root).resolve()
        self.output_dir = (self.root / config.output_dir).resolve()
        self.paper_output_dir = (self.root / config.paper_output_dir).resolve()
        self.logger = _configure_logging(self.output_dir, config.max_log_bytes, config.log_backups)
        self.runner = runner
        self.sleeper = sleeper
        self.now_fn = now_fn
        self.stop_requested = False
        self.cycle_number = self._load_cycle_number()

    def _load_cycle_number(self) -> int:
        path = self.output_dir / "orchestrator_state.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return int(payload.get("cycle_number", 0))
        except Exception:
            return 0

    def _write_json_atomic(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(path)

    def _refresh_readiness(self):
        readiness, walk = build_paper_launch_readiness(
            self.root / self.config.event_dir,
            self.root / self.config.cost_dir,
            self.root / self.config.fresh_report,
        )
        write_paper_readiness_outputs(readiness, walk, self.paper_output_dir)
        return readiness

    def _ensure_arm(self, readiness) -> Dict[str, Any]:
        state = load_arm_state(self.paper_output_dir)
        current_mode = str(state.get("mode", "DISARMED")).upper()
        desired_mode = current_mode
        if self.config.auto_upgrade_strategy and readiness.strategy_paper_ready:
            desired_mode = "STRATEGY"
        elif self.config.auto_arm_research and readiness.research_collection_ready:
            desired_mode = "RESEARCH"
        if desired_mode in {"RESEARCH", "STRATEGY"} and (
            not bool(state.get("armed")) or current_mode != desired_mode
        ):
            arm_paper_mode(readiness, desired_mode, self.paper_output_dir)
            state = load_arm_state(self.paper_output_dir)
            self.logger.info("Paper mode armed automatically: %s", desired_mode)
        # Hard assertions: this orchestrator never permits real capital or live orders.
        if bool(state.get("live_orders_enabled")) or bool(state.get("real_capital_enabled")):
            raise RuntimeError("Unsafe arm state detected; orchestrator refuses to continue.")
        return state

    def _run_commands(self, commands: Iterable[tuple[str, List[str], bool]]) -> List[StepResult]:
        results: List[StepResult] = []
        for name, command, critical in commands:
            result = run_step(
                name,
                command,
                cwd=self.root,
                timeout_seconds=self.config.step_timeout_seconds,
                retries=self.config.step_retries,
                retry_delay_seconds=self.config.retry_delay_seconds,
                logger=self.logger,
                runner=self.runner,
            )
            results.append(result)
            if critical and result.status != "PASSED":
                self.logger.error("Critical step %s failed; continuing only with safe evaluation/status steps.", name)
        return results

    def run_cycle(self, *, force_maintenance: bool = False) -> CycleResult:
        self.cycle_number += 1
        started = self.now_fn()
        cycle_id = started.strftime("paper_cycle_%Y%m%d_%H%M%S")
        self.logger.info("=== CYCLE %s START ===", cycle_id)
        warnings: List[str] = []

        readiness = self._refresh_readiness()
        state = self._ensure_arm(readiness)
        maintenance = force_maintenance or should_run_maintenance(
            self.cycle_number,
            self.config.maintenance_every_cycles,
            self.config.maintenance_enabled,
        )

        steps = self._run_commands(cycle_commands(self.config, sys.executable))
        if maintenance:
            self.logger.info("Daily maintenance is due on cycle %s.", self.cycle_number)
            steps.extend(self._run_commands(maintenance_commands(self.config, sys.executable)))
            # Fresh OOS may change readiness; re-arm only within virtual Paper modes.
            readiness = self._refresh_readiness()
            state = self._ensure_arm(readiness)

        failed = [item for item in steps if item.status != "PASSED"]
        if failed:
            warnings.extend(f"{item.name} failed with exit code {item.exit_code}." for item in failed)
        status = "COMPLETE" if not failed else "COMPLETE_WITH_STEP_FAILURES"
        finished = self.now_fn()
        result = CycleResult(
            cycle_id=cycle_id,
            started_utc=iso_utc(started),
            finished_utc=iso_utc(finished),
            status=status,
            maintenance_run=maintenance,
            readiness_status=readiness.status,
            arm_mode=str(state.get("mode", "DISARMED")),
            live_orders_enabled=False,
            steps=steps,
            warnings=warnings,
        )
        payload = result.to_dict()
        self._write_json_atomic(self.output_dir / "last_cycle.json", payload)
        with (self.output_dir / "cycle_history.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self._write_json_atomic(
            self.output_dir / "orchestrator_state.json",
            {
                "version": VERSION,
                "cycle_number": self.cycle_number,
                "last_cycle_id": cycle_id,
                "last_cycle_status": status,
                "last_finished_utc": result.finished_utc,
                "next_scheduled_utc": None,
                "arm_mode": result.arm_mode,
                "live_orders_enabled": False,
            },
        )
        self.logger.info("=== CYCLE %s END status=%s ===", cycle_id, status)
        return result

    def request_stop(self, *_args) -> None:
        self.stop_requested = True
        self.logger.info("Stop requested; current safe step will finish before shutdown.")

    def run_loop(self) -> int:
        if self.config.run_immediately:
            self.run_cycle()
        while not self.stop_requested:
            now = self.now_fn()
            scheduled = next_candle_run(
                now,
                timeframe_minutes=self.config.timeframe_minutes,
                settle_delay_seconds=self.config.settle_delay_seconds,
            )
            wait_seconds = max(0.0, (scheduled - now).total_seconds())
            self._write_json_atomic(
                self.output_dir / "heartbeat.json",
                {
                    "version": VERSION,
                    "pid": os.getpid(),
                    "status": "WAITING_FOR_NEXT_CANDLE",
                    "now_utc": iso_utc(now),
                    "next_scheduled_utc": iso_utc(scheduled),
                    "wait_seconds": round(wait_seconds, 3),
                    "live_orders_enabled": False,
                },
            )
            self.logger.info("Next cycle scheduled for %s (%.0f seconds).", iso_utc(scheduled), wait_seconds)
            remaining = wait_seconds
            while remaining > 0 and not self.stop_requested:
                chunk = min(30.0, remaining)
                self.sleeper(chunk)
                remaining -= chunk
            if not self.stop_requested:
                self.run_cycle()
        self._write_json_atomic(
            self.output_dir / "heartbeat.json",
            {
                "version": VERSION,
                "pid": os.getpid(),
                "status": "STOPPED",
                "stopped_utc": iso_utc(self.now_fn()),
                "live_orders_enabled": False,
            },
        )
        return 0


def _csv_tuple(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in str(value).split(",") if item.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Freakto automated zero-real-order Paper research cycle")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="Run one complete cycle and exit")
    mode.add_argument("--loop", action="store_true", help="Run immediately, then after each UTC candle close")
    mode.add_argument("--update-history-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--timeframe-minutes", type=int, default=240)
    parser.add_argument("--settle-delay-seconds", type=int, default=120)
    parser.add_argument("--maintenance-every-cycles", type=int, default=6)
    parser.add_argument("--no-maintenance", action="store_true")
    parser.add_argument("--maintenance-now", action="store_true")
    parser.add_argument("--no-decision-evaluator", action="store_true")
    parser.add_argument("--no-auto-strategy", action="store_true")
    parser.add_argument("--no-immediate", action="store_true")
    parser.add_argument("--step-timeout-seconds", type=int, default=1800)
    parser.add_argument("--step-retries", type=int, default=1)
    parser.add_argument("--retry-delay-seconds", type=int, default=20)
    parser.add_argument("--symbols", default="BTC/USDT,ETH/USDT,SOL/USDT")
    parser.add_argument("--timeframes", default="4h")
    parser.add_argument("--data-dir", default="data/market_replay")
    parser.add_argument("--historical-years", type=float, default=5.0)
    return parser


def config_from_args(args: argparse.Namespace) -> OrchestratorConfig:
    return OrchestratorConfig(
        project_root=args.project_root,
        timeframe_minutes=max(1, args.timeframe_minutes),
        settle_delay_seconds=max(0, args.settle_delay_seconds),
        run_immediately=not args.no_immediate,
        step_timeout_seconds=max(1, args.step_timeout_seconds),
        step_retries=max(0, args.step_retries),
        retry_delay_seconds=max(0, args.retry_delay_seconds),
        run_decision_evaluator=not args.no_decision_evaluator,
        maintenance_enabled=not args.no_maintenance,
        maintenance_every_cycles=max(1, args.maintenance_every_cycles),
        historical_years=max(0.1, args.historical_years),
        symbols=_csv_tuple(args.symbols),
        timeframes=_csv_tuple(args.timeframes),
        data_dir=args.data_dir,
        auto_upgrade_strategy=not args.no_auto_strategy,
    )


def main() -> int:
    args = build_parser().parse_args()
    config = config_from_args(args)
    if args.update_history_only:
        payload = update_historical_cache(config)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload.get("status") == "COMPLETE" else 2

    root = Path(config.project_root).resolve()
    output = root / config.output_dir
    lock = ProcessLock(output / "orchestrator.lock")
    try:
        with lock:
            orchestrator = PaperResearchOrchestrator(config)
            signal.signal(signal.SIGINT, orchestrator.request_stop)
            if hasattr(signal, "SIGTERM"):
                signal.signal(signal.SIGTERM, orchestrator.request_stop)
            if args.loop:
                return orchestrator.run_loop()
            result = orchestrator.run_cycle(force_maintenance=bool(args.maintenance_now))
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return 0 if result.status == "COMPLETE" else 2
    except RuntimeError as exc:
        print(f"Orchestrator blocked: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
