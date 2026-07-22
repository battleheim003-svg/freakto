"""Canonical composition root for Freakto command-line operations."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Sequence

from freakto.core import PAPER_SAFETY
from freakto.paper import PAPER_COMMANDS, PaperService, load_readiness
from freakto.research import resolve_data_replay, resolve_report

ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "logs" / "paper_launch_v2"

EXIT_OK = 0
EXIT_RUNTIME_ERROR = 1
EXIT_BLOCKED = 2

MIGRATED_MODULES = {
    "market_replay_dashboard.py": "freakto.research.adapters.market_replay",
    "forward_test_dashboard.py": "freakto.research.adapters.forward_status",
    "freakto_research_suite_dashboard.py": "freakto.research.adapters.suite_report",
    "paper_performance_dashboard.py": "freakto.paper.performance_report",
    "paper_research_orchestrator.py": "freakto.paper.orchestrator",
}


def _version() -> str:
    try:
        return version("freakto")
    except PackageNotFoundError:
        return "10.3.0"


def _safety() -> dict[str, bool | float]:
    """Compatibility helper retained for existing callers and tests."""
    return PAPER_SAFETY.payload()


def _safe_child_env() -> dict[str, str]:
    return PAPER_SAFETY.child_environment()


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _run_script(script: str, arguments: Sequence[str] = ()) -> int:
    """Run a retained entry script and propagate its process exit code."""
    path = ROOT / script
    if not path.is_file():
        _emit({"status": "CLI_TARGET_MISSING", "target": script, **_safety()})
        return EXIT_RUNTIME_ERROR
    module = MIGRATED_MODULES.get(script)
    target = ["-m", module] if module else [str(path)]
    command = [sys.executable, "-X", "utf8", *target, *arguments]
    try:
        return int(subprocess.call(command, cwd=ROOT, env=_safe_child_env()))
    except OSError as exc:
        _emit(
            {
                "status": "CLI_TARGET_FAILED",
                "target": script,
                "error": f"{type(exc).__name__}: {exc}",
                **_safety(),
            }
        )
        return EXIT_RUNTIME_ERROR


def _readiness():
    """Compatibility seam used by PaperService and existing fail-closed tests."""
    return load_readiness(PAPER_DIR)


def preflight() -> tuple[int, dict[str, Any]]:
    return PaperService(ROOT, _run_script, _readiness).preflight()


def _add_passthrough_command(subparsers, name: str, help_text: str) -> argparse.ArgumentParser:
    return subparsers.add_parser(name, help=help_text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="freakto",
        description="Safe Freakto research, replay, paper, and reporting interface",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_version()}")
    areas = parser.add_subparsers(dest="area", required=True)

    data = areas.add_parser("data", help="Inspect or build historical market-data cache")
    data_commands = data.add_subparsers(dest="command", required=True)
    _add_passthrough_command(data_commands, "status", "Inspect cached historical datasets")
    _add_passthrough_command(data_commands, "build", "Build or incrementally update data cache")

    replay = areas.add_parser("replay", help="Run causal historical replay workflows")
    replay_commands = replay.add_subparsers(dest="command", required=True)
    _add_passthrough_command(replay_commands, "status", "Inspect replay and dataset status")
    _add_passthrough_command(replay_commands, "run", "Replay existing cached datasets")
    _add_passthrough_command(replay_commands, "full", "Build data and then run replay")
    resume = _add_passthrough_command(replay_commands, "resume", "Resume an interrupted replay")
    resume.add_argument("run_id", help="Replay run identifier to resume")

    paper = areas.add_parser("paper", help="Operate fail-closed paper research workflows")
    paper.add_argument("command", choices=PAPER_COMMANDS)

    report = areas.add_parser("report", help="Generate canonical operational reports")
    report_commands = report.add_subparsers(dest="command", required=True)
    _add_passthrough_command(report_commands, "paper", "Generate paper performance outputs")
    _add_passthrough_command(report_commands, "research", "Generate the research-suite report")
    _add_passthrough_command(report_commands, "forward", "Show forward-validation status")
    return parser


def _run_data_or_replay(args: argparse.Namespace) -> int:
    command = resolve_data_replay(
        args.area,
        args.command,
        args.arguments,
        run_id=getattr(args, "run_id", None),
    )
    return _run_script(command.script, command.arguments)


def _run_report(args: argparse.Namespace) -> int:
    command = resolve_report(args.command, args.arguments)
    return _run_script(command.script, command.arguments)


def _run_paper(command: str) -> int:
    code, payload = PaperService(ROOT, _run_script, _readiness).execute(command)
    if payload is not None:
        _emit(payload)
    return code


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args, forwarded = parser.parse_known_args(argv)
    if args.area == "paper" and forwarded:
        parser.error(f"unrecognized arguments: {' '.join(forwarded)}")
    if args.area == "report" and args.command == "forward":
        unsupported = [argument for argument in forwarded if argument != "--send"]
        if unsupported:
            parser.error(
                "report forward is read-only; unsupported arguments: " + " ".join(unsupported)
            )
    args.arguments = forwarded
    if args.area in {"data", "replay"}:
        return _run_data_or_replay(args)
    if args.area == "report":
        return _run_report(args)
    return _run_paper(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
