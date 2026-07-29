"""Cross-platform, fail-closed supervisor for the local Paper demo."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Sequence

from freakto.core import PAPER_SAFETY
from freakto.paper.orchestrator import ProcessLock
from freakto.paper.state_paths import paper_state_paths
from freakto.ui.paper_demo import validate_refresh_seconds


TRUTHY = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DemoCommands:
    worker: tuple[str, ...]
    dashboard: tuple[str, ...]


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_python(root: Path) -> Path:
    relative = Path(".venv/Scripts/python.exe") if os.name == "nt" else Path(".venv/bin/python")
    return root / relative


def validate_port(value: int) -> int:
    if not 1024 <= int(value) <= 65535:
        raise ValueError("Port must be between 1024 and 65535.")
    return int(value)


def safe_environment(parent: dict[str, str] | None = None, *, refresh_seconds: int = 10) -> dict[str, str]:
    source = dict(os.environ if parent is None else parent)
    for name in ("LIVE_TRADING_ENABLED", "REAL_CAPITAL_ENABLED"):
        if source.get(name, "").strip().lower() in TRUTHY:
            raise RuntimeError(f"Unsafe parent configuration: {name} is enabled.")
    environment = PAPER_SAFETY.child_environment(source)
    environment["FREAKTO_DEMO_REFRESH_SECONDS"] = str(validate_refresh_seconds(refresh_seconds))
    return environment


def build_commands(
    root: Path,
    python: Path,
    *,
    port: int,
    no_browser: bool,
) -> DemoCommands:
    port = validate_port(port)
    worker = (
        str(python),
        "-X",
        "utf8",
        "-m",
        "freakto.paper.orchestrator",
        "--loop",
        "--no-immediate",
    )
    dashboard = (
        str(python),
        "-X",
        "utf8",
        "-m",
        "streamlit",
        "run",
        str(root / "freakto_control_center.py"),
        "--server.address",
        "127.0.0.1",
        "--server.port",
        str(port),
        "--server.headless",
        "true" if no_browser else "false",
    )
    return DemoCommands(worker, dashboard)


def worker_lock_status(root: Path) -> tuple[bool, int | None]:
    lock = paper_state_paths(root).canonical("orchestrator.lock")
    try:
        payload = json.loads(lock.read_text(encoding="utf-8"))
        pid = int(payload.get("pid", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False, None
    return ProcessLock._pid_alive(pid), pid


def preflight(root: Path, python: Path) -> None:
    if not python.is_file():
        raise RuntimeError(
            f"Project virtual environment is missing: {python}. "
            "Create .venv and install the documented requirements first."
        )
    if not (root / "freakto_control_center.py").is_file():
        raise RuntimeError("Streamlit entry point is missing.")
    if not (root / "freakto" / "paper" / "orchestrator.py").is_file():
        raise RuntimeError("Paper worker entry point is missing.")


def _display(command: Sequence[str], root: Path) -> str:
    return " ".join(
        f'"{Path(item).relative_to(root)}"' if Path(item).is_absolute() and str(item).startswith(str(root)) else item
        for item in command
    )


def stop_children(children: list[subprocess.Popen], timeout: float = 8.0) -> None:
    for child in children:
        if child.poll() is None:
            child.terminate()
    deadline = time.monotonic() + timeout
    for child in children:
        remaining = max(0.0, deadline - time.monotonic())
        if child.poll() is None:
            try:
                child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=2)


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch the local, Paper-only Freakto demo.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dashboard-only", action="store_true")
    mode.add_argument("--worker-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--refresh-seconds", type=int, default=10)
    args = parser.parse_args(argv)

    root = repository_root()
    python = project_python(root)
    try:
        preflight(root, python)
        environment = safe_environment(refresh_seconds=args.refresh_seconds)
        commands = build_commands(root, python, port=args.port, no_browser=args.no_browser)
    except (RuntimeError, ValueError) as exc:
        print(f"[BLOCKED] {exc}", file=sys.stderr)
        return 2

    active_worker, worker_pid = worker_lock_status(root)
    if active_worker and not args.dashboard_only:
        print(
            f"[BLOCKED] Paper worker PID {worker_pid} is already active. "
            "Use --dashboard-only.",
            file=sys.stderr,
        )
        return 3

    selected = []
    if not args.dashboard_only:
        selected.append(("worker", commands.worker))
    if not args.worker_only:
        selected.append(("dashboard", commands.dashboard))
    if args.dry_run:
        print("Freakto Paper demo dry run")
        print("Safety: LIVE_TRADING_ENABLED=false, REAL_CAPITAL_ENABLED=false")
        print("Binding: 127.0.0.1")
        for name, command in selected:
            print(f"{name}: {_display(command, root)}")
        return 0

    children: list[subprocess.Popen] = []
    try:
        for name, command in selected:
            print(f"Starting {name}: {_display(command, root)}")
            children.append(
                subprocess.Popen(
                    command,
                    cwd=root,
                    env=environment,
                    shell=False,
                )
            )
        while children:
            for child in children:
                code = child.poll()
                if code is not None:
                    print(f"A demo process exited with code {code}.", file=sys.stderr)
                    return int(code)
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("Stopping Freakto Paper demo...")
        return 130
    finally:
        stop_children(children)
    return 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
