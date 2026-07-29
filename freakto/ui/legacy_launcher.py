"""Compatibility launcher that redirects legacy UI commands to Control Center."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Sequence

from freakto.core import PAPER_SAFETY


def control_center_command(
    root: Path,
    *,
    address: str = "127.0.0.1",
    extra: Sequence[str] = (),
) -> tuple[str, ...]:
    return (
        sys.executable,
        "-X",
        "utf8",
        "-m",
        "streamlit",
        "run",
        str(Path(root).resolve() / "freakto_control_center.py"),
        "--server.address",
        address,
        *extra,
    )


def launch_control_center(source: str, *, root: Path | None = None) -> int:
    project = Path(root or Path(__file__).resolve().parents[2]).resolve()
    print(
        f"[DEPRECATED] {source} now opens the unified Freakto Control Center.",
        file=sys.stderr,
    )
    environment = PAPER_SAFETY.child_environment(os.environ)
    return subprocess.call(
        control_center_command(project),
        cwd=project,
        env=environment,
    )


__all__ = ["control_center_command", "launch_control_center"]
