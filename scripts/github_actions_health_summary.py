#!/usr/bin/env python3
"""
Build a compact GitHub Actions health summary for Freakto scheduled runs.

This script is safe for CI:
- reads only logs/history outputs
- never reads .env or secrets
- writes a Markdown summary to GitHub's step summary when available
- always exits 0 so it does not hide the real failure from earlier steps
"""

from __future__ import annotations

import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
OUT_DIR = LOGS / "github_actions"


def _read_csv_rows(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception:
        return []
    if limit is None:
        return rows
    return rows[-limit:]


def _latest_file(pattern: str) -> Path | None:
    files = sorted(ROOT.glob(pattern), key=lambda p: p.stat().st_mtime if p.exists() else 0)
    return files[-1] if files else None


def _load_latest_status() -> dict[str, Any]:
    path = _latest_file("logs/forward_testing/forward_test_status_*.json")
    if not path:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"_status_json_error": str(path)}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _safe_text(value: Any, default: str = "-") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _extract_progress(status: dict[str, Any]) -> dict[str, Any]:
    # The forward status JSON has changed across versions; this accepts both
    # flat and nested shapes so the health report does not break future runs.
    progress = status.get("progress") if isinstance(status.get("progress"), dict) else status
    return {
        "status": _safe_text(progress.get("status") or progress.get("collection_status"), "UNKNOWN"),
        "progress_score": _safe_int(progress.get("progress_score")),
        "readiness_level": _safe_text(progress.get("readiness_level"), "UNKNOWN"),
        "complete_evaluations": _safe_int(progress.get("complete_evaluations")),
        "closed_paper_trades": _safe_int(progress.get("closed_paper_trades")),
        "open_paper_trades": _safe_int(progress.get("open_paper_trades")),
        "regime_labeled": _safe_int(progress.get("regime_labeled")),
        "forward_runs": _safe_int(progress.get("forward_runs")),
        "successful_forward_runs": _safe_int(progress.get("successful_forward_runs")),
        "forward_days": _safe_int(progress.get("forward_days")),
        "live_ready": bool(progress.get("live_ready", False)),
        "paper_ready": bool(progress.get("paper_ready", False)),
    }


def _run_rows() -> list[dict[str, str]]:
    return _read_csv_rows(LOGS / "forward_test_runs.csv", limit=10)


def _status_icon(row: dict[str, str]) -> str:
    ok = str(row.get("ok", "")).lower().strip()
    if ok in {"true", "1", "yes", "ok"}:
        return "✅"
    if ok in {"false", "0", "no", "failed"}:
        return "❌"
    return "•"


def build_summary() -> str:
    now = datetime.now(timezone.utc).isoformat()
    status = _extract_progress(_load_latest_status())
    rows = _run_rows()
    last_run = rows[-1] if rows else {}

    lines: list[str] = []
    lines.append("# Freakto GitHub Actions Health Summary")
    lines.append("")
    lines.append(f"Generated UTC: `{now}`")
    lines.append("")
    lines.append("## Current Forward Status")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Status | `{status['status']}` |")
    lines.append(f"| Progress Score | `{status['progress_score']}/100` |")
    lines.append(f"| Readiness Level | `{status['readiness_level']}` |")
    lines.append(f"| Paper Ready | `{status['paper_ready']}` |")
    lines.append(f"| Live Ready | `{status['live_ready']}` |")
    lines.append(f"| Complete Evaluations | `{status['complete_evaluations']}/100` |")
    lines.append(f"| Closed Paper Trades | `{status['closed_paper_trades']}/30` |")
    lines.append(f"| Open Paper Trades | `{status['open_paper_trades']}` |")
    lines.append(f"| Regime-labeled Samples | `{status['regime_labeled']}/30` |")
    lines.append(f"| Forward Runs | `{status['successful_forward_runs']}/{status['forward_runs']} successful` |")
    lines.append(f"| Forward Days | `{status['forward_days']}/30` |")
    lines.append("")

    lines.append("## Last Forward Run")
    lines.append("")
    if last_run:
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        for key in ["run_id", "ok", "started_utc", "finished_utc", "duration_sec"]:
            lines.append(f"| {key} | `{_safe_text(last_run.get(key))}` |")
    else:
        lines.append("No `logs/forward_test_runs.csv` rows found yet.")
    lines.append("")

    if rows:
        lines.append("## Recent Runs")
        lines.append("")
        lines.append("| | Run ID | OK | Started UTC | Duration |")
        lines.append("|---|---|---:|---|---:|")
        for row in rows[-5:]:
            lines.append(
                f"| {_status_icon(row)} | `{_safe_text(row.get('run_id'))}` | `{_safe_text(row.get('ok'))}` | "
                f"`{_safe_text(row.get('started_utc'))}` | `{_safe_text(row.get('duration_sec'))}` |"
            )
        lines.append("")

    lines.append("## Operational Notes")
    lines.append("")
    if status["live_ready"]:
        lines.append("⚠️ `live_ready=True` appeared in status, but still review validation reports manually before any real trading.")
    elif status["paper_ready"]:
        lines.append("🟡 Paper readiness may be improving. Continue collecting data; do not enable live trading automatically.")
    else:
        lines.append("✅ Normal collection mode. This is still research/forward-test infrastructure, not live trading.")
    lines.append("")
    lines.append("Expected next checks: Telegram message, green workflow run, `data-logs` branch update, and uploaded artifacts.")
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    text = build_summary()
    out_path = OUT_DIR / "github_actions_health_summary.md"
    out_path.write_text(text, encoding="utf-8")
    print(text)

    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary:
        with open(step_summary, "a", encoding="utf-8") as f:
            f.write(text)
            f.write("\n")


if __name__ == "__main__":
    main()
