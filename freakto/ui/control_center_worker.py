"""Background worker for the Control Center quick-start pipeline."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from freakto.ui.control_center_state import quick_start_plan, run_cli
from freakto.ui.job_manager import read_state, utc_now, write_state


def _cancelled(directory: Path) -> bool:
    return (directory / "cancel.requested").exists()


def _append_log(path: Path, heading: str, stdout: str, stderr: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n{'=' * 88}\n{heading}\n{'=' * 88}\n")
        if stdout:
            handle.write(stdout.rstrip() + "\n")
        if stderr:
            handle.write("[stderr]\n" + stderr.rstrip() + "\n")


def run_job(state_path: Path, root: Path) -> int:
    directory = state_path.parent
    state = read_state(state_path)
    plan = quick_start_plan(include_data_build=bool(state.get("full")), include_replay=bool(state.get("full")))
    state.update(
        status="RUNNING",
        pid=os.getpid(),
        started_utc=state.get("started_utc") or utc_now(),
        heartbeat_utc=utc_now(),
        total_steps=len(plan),
    )
    write_state(state_path, state)
    try:
        for index, step in enumerate(plan, start=1):
            if _cancelled(directory):
                state.update(status="CANCELLED", ended_utc=utc_now(), current_step=None)
                write_state(state_path, state)
                return 3
            state.update(current_step=step.key, heartbeat_utc=utc_now())
            write_state(state_path, state)
            result = run_cli(step.arguments, root=root, timeout=3600 if step.long_running else 900)
            accepted = result.exit_code in step.accepted_exit_codes
            _append_log(directory / "pipeline.log", f"{index}/{len(plan)} freakto {' '.join(step.arguments)} [exit={result.exit_code}]", result.stdout, result.stderr)
            state["steps"].append(
                {
                    "index": index,
                    "key": step.key,
                    "command": "freakto " + " ".join(step.arguments),
                    "exit_code": result.exit_code,
                    "accepted": accepted,
                    "completed_utc": utc_now(),
                    "stdout_tail": result.stdout[-2000:],
                    "stderr_tail": result.stderr[-2000:],
                }
            )
            state.update(completed_steps=index, heartbeat_utc=utc_now())
            if _cancelled(directory):
                state.update(status="CANCELLED", ended_utc=utc_now(), current_step=None)
                write_state(state_path, state)
                return 3
            if not accepted:
                state.update(status="FAILED", ended_utc=utc_now(), current_step=None, error=f"Step {step.key} exited with {result.exit_code}")
                write_state(state_path, state)
                return result.exit_code or 1
            write_state(state_path, state)
        state.update(status="SUCCEEDED", ended_utc=utc_now(), current_step=None, heartbeat_utc=utc_now())
        write_state(state_path, state)
        return 0
    except Exception as exc:
        state.update(status="FAILED", ended_utc=utc_now(), current_step=None, error=f"{type(exc).__name__}: {exc}")
        write_state(state_path, state)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    return run_job(args.state, args.root)


if __name__ == "__main__":
    raise SystemExit(main())
