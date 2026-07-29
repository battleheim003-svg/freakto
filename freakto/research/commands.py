"""Stable research commands mapped to retained phase-5 implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class LegacyCommand:
    script: str
    arguments: tuple[str, ...] = ()

    def with_arguments(self, arguments: Sequence[str]) -> "LegacyCommand":
        return LegacyCommand(self.script, (*self.arguments, *arguments))


def resolve_data_replay(
    area: str,
    command: str,
    forwarded: Sequence[str],
    *,
    run_id: str | None = None,
) -> LegacyCommand:
    mode = {
        ("data", "status"): "--status",
        ("data", "build"): "--build-data",
        ("replay", "status"): "--status",
        ("replay", "run"): "--replay",
        ("replay", "full"): "--full",
        ("replay", "resume"): "--resume",
    }.get((area, command))
    if mode is None:
        raise ValueError(f"Unsupported research command: {area} {command}")
    arguments = [mode]
    if command == "resume":
        if not run_id:
            raise ValueError("Replay resume requires a run id")
        arguments.append(run_id)
    arguments.extend(forwarded)
    return LegacyCommand("market_replay_dashboard.py", tuple(arguments))


def resolve_report(command: str, forwarded: Sequence[str]) -> LegacyCommand:
    target = {
        "paper": LegacyCommand("paper_performance_dashboard.py"),
        "research": LegacyCommand("freakto_research_suite_dashboard.py"),
        "forward": LegacyCommand("forward_test_dashboard.py", ("--status",)),
    }.get(command)
    if target is None:
        raise ValueError(f"Unsupported report command: {command}")
    return target.with_arguments(forwarded)
