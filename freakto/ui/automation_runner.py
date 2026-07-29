"""Small local supervisor for persisted Control Center schedules."""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

from freakto.ui.automation import list_automations, run_due_automations, scheduler_status, utc_now, write_scheduler_state


def run_scheduler(root: Path, *, poll_seconds: int = 20) -> int:
    state = scheduler_status(root)
    state.update(
        status="RUNNING",
        pid=os.getpid(),
        started_utc=state.get("started_utc") or utc_now().isoformat(),
        heartbeat_utc=utc_now().isoformat(),
        ended_utc=None,
        error=None,
    )
    write_scheduler_state(state, root=root)
    try:
        while any(item.get("enabled") for item in list_automations(root)):
            run_due_automations(root=root)
            state.update(status="RUNNING", heartbeat_utc=utc_now().isoformat())
            write_scheduler_state(state, root=root)
            time.sleep(max(1, int(poll_seconds)))
        state.update(status="STOPPED", heartbeat_utc=utc_now().isoformat(), ended_utc=utc_now().isoformat())
        write_scheduler_state(state, root=root)
        return 0
    except Exception as exc:
        state.update(status="FAILED", heartbeat_utc=utc_now().isoformat(), ended_utc=utc_now().isoformat(), error=f"{type(exc).__name__}: {exc}")
        write_scheduler_state(state, root=root)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    return run_scheduler(args.root)


if __name__ == "__main__":
    raise SystemExit(main())
