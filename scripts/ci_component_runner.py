"""Execute a CI component under an explicit required/optional policy."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


def _tail(value: str, limit: int = 4000) -> str:
    return str(value or "")[-limit:]


def _load_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "components": []}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "components": []}
    if not isinstance(payload.get("components"), list):
        payload["components"] = []
    return payload


def _write_report(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _load_report(path)
    payload["updated_at_utc"] = datetime.now(timezone.utc).isoformat()
    payload["components"].append(record)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _write_step_summary(record: dict[str, Any]) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY", "").strip()
    if not summary_path:
        return
    marker = {"PASSED": "✅", "DEGRADED": "⚠️", "FAILED": "❌"}[record["status"]]
    with Path(summary_path).open("a", encoding="utf-8") as handle:
        handle.write(
            f"- {marker} **{record['name']}** — {record['status']} "
            f"(policy: `{record['policy']}`, exit: `{record['exit_code']}`)\n"
        )


def run_component(
    name: str,
    policy: str,
    command: Sequence[str],
    report_path: Path,
) -> int:
    if not command:
        raise ValueError("Component command cannot be empty")
    started = datetime.now(timezone.utc)
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        exit_code = int(completed.returncode)
        stdout = completed.stdout
        stderr = completed.stderr
    except OSError as exc:
        exit_code = 1
        stdout = ""
        stderr = f"{type(exc).__name__}: {exc}"
    if exit_code == 0:
        status = "PASSED"
    elif policy == "optional":
        status = "DEGRADED"
    else:
        status = "FAILED"
    record = {
        "name": name,
        "policy": policy,
        "status": status,
        "exit_code": exit_code,
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": list(command),
        "stdout_tail": _tail(stdout),
        "stderr_tail": _tail(stderr),
    }
    _write_report(report_path, record)
    _write_step_summary(record)
    if os.getenv("GITHUB_ACTIONS", "").lower() == "true" and status != "PASSED":
        annotation = "warning" if status == "DEGRADED" else "error"
        print(f"::{annotation} title={name}::{status} (policy={policy}, exit={exit_code})")
    if stdout:
        print(stdout, end="" if stdout.endswith("\n") else "\n")
    if stderr:
        print(stderr, end="" if stderr.endswith("\n") else "\n", file=sys.stderr)
    print(f"component={name} policy={policy} status={status} exit={exit_code}")
    return exit_code if policy == "required" else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one explicitly classified CI component")
    parser.add_argument("--name", required=True)
    parser.add_argument("--policy", choices=("required", "optional"), required=True)
    parser.add_argument(
        "--report",
        default=os.getenv("FREAKTO_COMPONENT_REPORT", "logs/ci/component-results.json"),
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    return run_component(args.name, args.policy, command, Path(args.report))


if __name__ == "__main__":
    raise SystemExit(main())
