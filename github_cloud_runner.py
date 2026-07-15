from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

REQUIRED_SECRETS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
OPTIONAL_SECRETS = ("OPENAI_API_KEY", "COINALYZE_API_KEY")


@dataclass
class StepResult:
    name: str
    command: list[str]
    attempt: int
    return_code: int
    duration_seconds: float
    stdout_tail: str
    stderr_tail: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_environment() -> dict:
    missing = [name for name in REQUIRED_SECRETS if not os.getenv(name, "").strip()]
    optional_missing = [name for name in OPTIONAL_SECRETS if not os.getenv(name, "").strip()]
    return {
        "valid": not missing,
        "missing_required": missing,
        "missing_optional": optional_missing,
    }


def _tail(text: str, limit: int = 8000) -> str:
    return text[-limit:] if len(text) > limit else text


def run_step(
    name: str,
    command: Sequence[str],
    *,
    retries: int = 1,
    timeout_seconds: int = 1800,
    cwd: Path | None = None,
) -> StepResult:
    last: StepResult | None = None
    for attempt in range(1, retries + 2):
        started = time.monotonic()
        try:
            completed = subprocess.run(
                list(command),
                cwd=str(cwd) if cwd else None,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
                env=os.environ.copy(),
            )
            last = StepResult(
                name=name,
                command=list(command),
                attempt=attempt,
                return_code=completed.returncode,
                duration_seconds=round(time.monotonic() - started, 3),
                stdout_tail=_tail(completed.stdout),
                stderr_tail=_tail(completed.stderr),
            )
        except subprocess.TimeoutExpired as exc:
            last = StepResult(
                name=name,
                command=list(command),
                attempt=attempt,
                return_code=124,
                duration_seconds=round(time.monotonic() - started, 3),
                stdout_tail=_tail((exc.stdout or "") if isinstance(exc.stdout, str) else ""),
                stderr_tail=f"Timeout after {timeout_seconds} seconds",
            )
        print(json.dumps(asdict(last), ensure_ascii=False), flush=True)
        if last.return_code == 0:
            return last
        if attempt <= retries:
            time.sleep(min(10, 2**attempt))
    assert last is not None
    return last


def send_failure_alert(message: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False
    try:
        import requests

        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat_id, "text": message},
            timeout=15,
        )
        return response.ok
    except Exception:
        return False


def discover_cycle_command(root: Path) -> list[str]:
    orchestrator = root / "paper_research_orchestrator.py"
    if orchestrator.exists():
        return [sys.executable, "-X", "utf8", str(orchestrator.name), "--once"]
    raise FileNotFoundError(
        "paper_research_orchestrator.py is missing. Apply the Automated Paper Research Orchestrator package before enabling cloud runs."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one fail-closed Freakto cloud paper-research cycle.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--report", default="logs/cloud_runner/cloud_cycle_report.json")
    parser.add_argument("--skip-secret-check", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report_path = root / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    env_status = validate_environment()
    report: dict = {
        "schema_version": 1,
        "started_at_utc": utc_now(),
        "environment": env_status,
        "live_orders_enabled": False,
        "real_capital_enabled": False,
        "steps": [],
    }

    if not args.skip_secret_check and not env_status["valid"]:
        report.update(status="BLOCKED_MISSING_REQUIRED_SECRETS", finished_at_utc=utc_now())
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 2

    try:
        cycle_command = discover_cycle_command(root)
    except FileNotFoundError as exc:
        report.update(status="BLOCKED_MISSING_ORCHESTRATOR", error=str(exc), finished_at_utc=utc_now())
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 3

    result = run_step("paper_research_cycle", cycle_command, retries=1, timeout_seconds=3300, cwd=root)
    report["steps"].append(asdict(result))
    report["status"] = "COMPLETE" if result.return_code == 0 else "FAILED"
    report["finished_at_utc"] = utc_now()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if result.return_code != 0:
        send_failure_alert(
            "⚠️ Freakto cloud paper cycle failed\n"
            f"UTC: {report['finished_at_utc']}\n"
            f"Exit code: {result.return_code}\n"
            "Check the GitHub Actions artifact and logs."
        )
    print(json.dumps({"status": report["status"], "report": str(report_path)}, ensure_ascii=False))
    return result.return_code


if __name__ == "__main__":
    raise SystemExit(main())
