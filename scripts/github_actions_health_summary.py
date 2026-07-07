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


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "ok"}


def _value(progress: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Return the first present/non-empty value across known schema aliases."""
    for key in keys:
        value = progress.get(key)
        if value is not None and value != "":
            return value
    return default


def _run_metrics_from_csv() -> dict[str, Any]:
    rows = _run_rows()
    successes = [row for row in rows if _truthy(row.get("ok") or row.get("success") or row.get("status"))]
    starts: list[datetime] = []
    for row in rows:
        raw = _safe_text(row.get("started_utc") or row.get("started") or row.get("timestamp"), "")
        if not raw:
            continue
        try:
            starts.append(datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except Exception:
            continue
    return {
        "rows": rows,
        "forward_runs": len(rows),
        "successful_forward_runs": len(successes),
        "forward_days": len({dt.date().isoformat() for dt in starts}),
    }


def _extract_progress(status: dict[str, Any]) -> dict[str, Any]:
    # The forward status JSON has changed across versions; this accepts both
    # flat and nested shapes. For GitHub Actions, logs/forward_test_runs.csv
    # is the source of truth for run/day counters because the latest restored
    # status JSON can be old, incomplete, or generated before append_forward_run().
    progress = status.get("progress") if isinstance(status.get("progress"), dict) else status
    run_metrics = _run_metrics_from_csv()

    json_forward_runs = _safe_int(_value(progress, "forward_runs", "forward_run_count"), 0)
    json_successful_runs = _safe_int(_value(progress, "successful_forward_runs", "successful_run_count"), 0)
    json_forward_days = _safe_int(_value(progress, "forward_days", "forward_days_observed"), 0)

    csv_forward_runs = _safe_int(run_metrics.get("forward_runs"), 0)
    csv_successful_runs = _safe_int(run_metrics.get("successful_forward_runs"), 0)
    csv_forward_days = _safe_int(run_metrics.get("forward_days"), 0)

    # Prefer CSV metrics whenever any restored run rows exist. This fixes the
    # health summary case where `Last Forward Run` is visible but `Forward Runs`
    # still displays 0/0 because an older status JSON was restored.
    if csv_forward_runs > 0:
        forward_runs = csv_forward_runs
        successful_runs = csv_successful_runs
        forward_days = csv_forward_days
    else:
        forward_runs = json_forward_runs
        successful_runs = json_successful_runs
        forward_days = json_forward_days

    # Extra guard: if CSV parsing somehow produces no count but a latest run is
    # still present, count at least that single observed run/day.
    rows = run_metrics.get("rows") or []
    if rows and forward_runs == 0:
        forward_runs = len(rows)
    if rows and successful_runs == 0:
        successful_runs = len([r for r in rows if _truthy(r.get("ok") or r.get("success") or r.get("status"))])
    if rows and forward_days == 0:
        seen_days: set[str] = set()
        for row in rows:
            raw = _safe_text(row.get("started_utc") or row.get("started") or row.get("timestamp"), "")
            if not raw:
                continue
            try:
                seen_days.add(datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat())
            except Exception:
                # Fallback for strings that start with YYYY-MM-DD.
                if len(raw) >= 10 and raw[4:5] == "-" and raw[7:8] == "-":
                    seen_days.add(raw[:10])
        forward_days = len(seen_days)

    return {
        "status": _safe_text(_value(progress, "status", "collection_status"), "UNKNOWN"),
        "progress_score": _safe_int(progress.get("progress_score")),
        "readiness_level": _safe_text(progress.get("readiness_level"), "UNKNOWN"),
        "complete_evaluations": _safe_int(progress.get("complete_evaluations")),
        "closed_paper_trades": _safe_int(progress.get("closed_paper_trades")),
        "open_paper_trades": _safe_int(progress.get("open_paper_trades")),
        "regime_labeled": _safe_int(_value(progress, "regime_labeled", "regime_labeled_samples")),
        "forward_runs": max(0, forward_runs),
        "successful_forward_runs": max(0, successful_runs),
        "forward_days": max(0, forward_days),
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
        for key in ["run_id", "ok", "started_utc", "finished_utc"]:
            lines.append(f"| {key} | `{_safe_text(last_run.get(key))}` |")
        duration = _safe_text(last_run.get("duration_seconds") or last_run.get("duration_sec") or last_run.get("duration") or last_run.get("duration_s"))
        lines.append(f"| duration | `{duration}` |")
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
                f"`{_safe_text(row.get('started_utc'))}` | `{_safe_text(row.get('duration_sec') or row.get('duration_seconds'))}` |"
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
