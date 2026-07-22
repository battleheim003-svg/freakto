"""Verify a completed Control Center job as Phase-12 E2E evidence."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from freakto.ui.job_manager import ROOT, jobs_dir, list_jobs, read_state


EXPECTED_STEPS = (
    "data_status",
    "data_build",
    "replay_status",
    "replay_run",
    "paper_preflight",
    "arm_research",
    "paper_cycle",
    "paper_status",
    "paper_report",
    "forward_report",
    "go_live_check",
)


def verify_job(job: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    steps = list(job.get("steps") or [])
    keys = tuple(step.get("key") for step in steps)
    paper_output = "\n".join(
        str(step.get("stdout_tail") or "")
        for step in steps
        if step.get("key") in {"paper_preflight", "arm_research", "paper_cycle", "paper_status"}
    ).lower()
    checks = {
        "job_succeeded": job.get("status") == "SUCCEEDED",
        "complete_ordered_pipeline": keys == EXPECTED_STEPS,
        "all_exits_accepted": bool(steps) and all(step.get("accepted") is True for step in steps),
        "go_live_review_only_exit": bool(steps) and steps[-1].get("exit_code") in {0, 2},
        "live_orders_disabled": '"live_orders_enabled": false' in paper_output or "live orders enabled       : false" in paper_output,
        "real_capital_disabled": '"real_capital_enabled": false' in paper_output,
        "zero_allocation": '"allocation_pct": 0.0' in paper_output,
    }
    manifest = {
        "schema_version": 1,
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "job_id": job.get("job_id"),
        "job_status": job.get("status"),
        "checks": checks,
        "passed": all(checks.values()),
        "step_results": [
            {"key": step.get("key"), "exit_code": step.get("exit_code"), "accepted": step.get("accepted")}
            for step in steps
        ],
    }
    return bool(manifest["passed"]), manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.job_id:
        job = read_state(jobs_dir(ROOT) / args.job_id / "state.json")
    else:
        jobs = list_jobs(ROOT)
        job = jobs[0] if jobs else {}
    passed, manifest = verify_job(job)
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
