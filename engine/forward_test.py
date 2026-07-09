"""Freakto Forward Test Controller v5.1

Runs and tracks the safe data-collection workflow before any real-money test.
No exchange order is ever sent from this module. It only executes existing
research/paper-trading commands, stores run logs, and reports readiness progress.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None


VERSION = "v9.0.0"
LOG_DIR = Path("logs")
FORWARD_DIR = LOG_DIR / "forward_testing"
RUNS_CSV = LOG_DIR / "forward_test_runs.csv"

DECISIONS_FILE = LOG_DIR / "decisions.csv"
EVALUATIONS_FILE = LOG_DIR / "decision_evaluations.csv"
PAPER_TRADES_FILE = LOG_DIR / "paper_trades.csv"
PAPER_EVALUATIONS_FILE = LOG_DIR / "paper_trade_evaluations.csv"
PORTFOLIO_SCANS_FILE = LOG_DIR / "portfolio_scans.csv"

TARGET_COMPLETE_EVALUATIONS = 100
TARGET_CLOSED_PAPER_TRADES = 30
TARGET_REGIME_LABELED = 30
TARGET_FORWARD_DAYS = 30


@dataclass
class ForwardTask:
    name: str
    command: List[str]
    required: bool = True
    description: str = ""


@dataclass
class TaskRunResult:
    name: str
    command: str
    started_utc: str
    finished_utc: str
    duration_seconds: float
    return_code: int
    ok: bool
    output_file: str = ""
    error_file: str = ""
    stdout_tail: str = ""
    stderr_tail: str = ""


@dataclass
class ForwardRunResult:
    run_id: str
    started_utc: str
    finished_utc: str
    duration_seconds: float
    mode: str
    ok: bool
    tasks: List[TaskRunResult] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    report_file: str = ""


@dataclass
class ForwardProgress:
    status: str
    complete_evaluations: int = 0
    closed_paper_trades: int = 0
    open_paper_trades: int = 0
    total_paper_trades: int = 0
    regime_labeled_samples: int = 0
    unknown_regime_samples: int = 0
    distinct_symbols_evaluated: int = 0
    distinct_symbols_scanned: int = 0
    forward_run_count: int = 0
    successful_run_count: int = 0
    first_run_utc: str = ""
    last_run_utc: str = ""
    forward_days_observed: int = 0
    readiness_level: str = "RESEARCH_ONLY"
    paper_ready: bool = False
    live_ready: bool = False
    progress_score: int = 0
    notes: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)


@dataclass
class ForwardPlan:
    tasks: List[ForwardTask]
    validate_after_cycle: bool = True
    send_validation: bool = False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_stamp(dt: Optional[datetime] = None) -> str:
    return (dt or _utc_now()).strftime("%Y%m%d_%H%M%S")


def _iso(dt: Optional[datetime] = None) -> str:
    return (dt or _utc_now()).isoformat()


def _python_cmd(script: str, *args: str) -> List[str]:
    """Build a child Python command with UTF-8 mode forced.

    On Windows, subprocess pipes often default to a legacy code page such as
    cp1252. Several Freakto dashboards print Persian text and emojis, so the
    child process can crash with UnicodeEncodeError before the parent receives
    any useful output. Running children with ``-X utf8`` and PYTHONIOENCODING
    makes the Forward Test cycle safe for scheduled/background execution.
    """
    return [sys.executable, "-X", "utf8", script, *args]


def _forward_child_env() -> dict:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def build_forward_test_plan(
    *,
    symbols: str = "",
    include_monitor: bool = True,
    include_portfolio: bool = True,
    include_evaluator: bool = True,
    include_paper_evaluator: bool = True,
    include_validation: bool = False,
    include_risk_lab: bool = False,
    send: bool = False,
) -> ForwardPlan:
    tasks: List[ForwardTask] = []

    if include_monitor:
        tasks.append(
            ForwardTask(
                name="monitor_once",
                command=_python_cmd("monitor.py", "--once"),
                required=True,
                description="ثبت یک تصمیم جدید از Decision Engine و Intelligence Layer.",
            )
        )

    if include_portfolio:
        cmd = _python_cmd("portfolio_scanner.py", "--paper")
        if symbols.strip():
            cmd.extend(["--symbols", symbols.strip()])
        if send:
            cmd.append("--send")
        tasks.append(
            ForwardTask(
                name="portfolio_scan_paper_gate",
                command=cmd,
                required=True,
                description="اسکن پورتفو و ثبت Paper Trade فقط اگر گیت‌ها اجازه بدهند.",
            )
        )

    if include_evaluator:
        tasks.append(
            ForwardTask(
                name="automatic_event_collector",
                command=_python_cmd("automatic_event_collector_dashboard.py", "--compact"),
                required=False,
                description="جمع‌آوری خودکار رویدادها از منابع رسمی/معتبر و ساخت data/auto_events.csv بدون Paper/Live.",
            )
        )
        tasks.append(
            ForwardTask(
                name="causal_intelligence_probe",
                command=_python_cmd("causal_intelligence_dashboard.py", "--compact"),
                required=False,
                description="جمع‌آوری context علّی/رویدادی از منابع معتبر و ثبت catalyst/conflict بدون Paper/Live.",
            )
        )
        tasks.append(
            ForwardTask(
                name="market_narrative_probe",
                command=_python_cmd("market_narrative_dashboard.py", "--compact"),
                required=False,
                description="ساخت روایت بازار از eventهای فیلترشده و causal context بدون Paper/Live.",
            )
        )
        tasks.append(
            ForwardTask(
                name="narrative_decision_conflict_probe",
                command=_python_cmd("narrative_decision_dashboard.py", "--compact"),
                required=False,
                description="امتیازدهی تضاد/همسویی Narrative با bias تصمیم‌ها بدون Paper/Live.",
            )
        )
        tasks.append(
            ForwardTask(
                name="root_cause_discovery_probe",
                command=_python_cmd("root_cause_dashboard.py", "--compact"),
                required=False,
                description="کشف علت‌های محتمل حرکت/زمینه بازار با evidence weighting بدون Paper/Live.",
            )
        )
        tasks.append(
            ForwardTask(
                name="decision_log_repair",
                command=_python_cmd("decision_log_repair.py"),
                required=False,
                description="هماهنگ‌سازی schema فایل decisions.csv قبل از ارزیابی.",
            )
        )
        tasks.append(
            ForwardTask(
                name="forward_regime_label_injection",
                command=_python_cmd("forward_regime_label_dashboard.py", "--compact"),
                required=False,
                description="تزریق/ترمیم regime_label و metadata قبل از decision_evaluator و Shadow Gates.",
            )
        )
        tasks.append(
            ForwardTask(
                name="decision_evaluator",
                command=_python_cmd("decision_evaluator.py"),
                required=True,
                description="به‌روزرسانی ارزیابی تصمیم‌ها با کندل‌های جدید، raw market returns و metadata علت‌ها.",
            )
        )
        tasks.append(
            ForwardTask(
                name="root_cause_forward_validation_probe",
                command=_python_cmd("root_cause_forward_validation_dashboard.py", "--compact"),
                required=False,
                description="اعتبارسنجی Forward علت‌های کشف‌شده با return کندل‌های بعدی بدون Paper/Live.",
            )
        )
        tasks.append(
            ForwardTask(
                name="root_cause_sample_tracker",
                command=_python_cmd("root_cause_sample_dashboard.py", "--compact"),
                required=False,
                description="پایش بلوغ sampleهای Root Cause و فاصله تا حداقل اعتبارسنجی بدون Paper/Live.",
            )
        )
        tasks.append(
            ForwardTask(
                name="evidence_graph_probe",
                command=_python_cmd("evidence_graph_dashboard.py", "--compact"),
                required=False,
                description="ساخت گراف مسیر شواهد تا outcome برای یادگیری research-only بدون Paper/Live.",
            )
        )
        tasks.append(
            ForwardTask(
                name="shadow_gate_validator",
                command=_python_cmd("shadow_gate_dashboard.py", "--compact"),
                required=False,
                description="برچسب‌گذاری و ارزیابی Shadow Gateهای پایه و Regime-specific بدون ثبت Paper/Live.",
            )
        )
        tasks.append(
            ForwardTask(
                name="forward_shadow_coverage_probe",
                command=_python_cmd("forward_shadow_coverage_dashboard.py", "--compact"),
                required=False,
                description="بررسی coverage گیت‌ها، دلیل صفر بودن Regime Bear gates و Bull probe بدون Paper/Live.",
            )
        )

    if include_paper_evaluator:
        tasks.append(
            ForwardTask(
                name="paper_trade_evaluator",
                command=_python_cmd("paper_trading_dashboard.py", "--evaluate"),
                required=False,
                description="ارزیابی معاملات فرضی باز/بسته‌شده، اگر Paper Trade وجود داشته باشد.",
            )
        )

    if include_risk_lab:
        cmd = _python_cmd("risk_lab_dashboard.py")
        if send:
            cmd.append("--send")
        tasks.append(
            ForwardTask(
                name="risk_lab",
                command=cmd,
                required=False,
                description="اجرای Portfolio Memory، Calibration و Monte Carlo.",
            )
        )

    if include_validation:
        cmd = _python_cmd("validation_suite_dashboard.py")
        if send:
            cmd.append("--send")
        tasks.append(
            ForwardTask(
                name="validation_suite",
                command=cmd,
                required=False,
                description="اجرای کامل Validation Suite بعد از جمع‌آوری داده.",
            )
        )

    return ForwardPlan(tasks=tasks, validate_after_cycle=include_validation, send_validation=send)


def _read_csv_safe(path: Path):
    if pd is None or not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            return None


def _count_complete_evaluations() -> int:
    df = _read_csv_safe(EVALUATIONS_FILE)
    if df is None or df.empty:
        return 0
    if "evaluation_status" in df.columns:
        return int((df["evaluation_status"].astype(str).str.upper() == "COMPLETE").sum())
    return int(len(df))


def _count_distinct_symbols(path: Path, column: str = "symbol") -> int:
    df = _read_csv_safe(path)
    if df is None or df.empty or column not in df.columns:
        return 0
    values = df[column].dropna().astype(str).str.strip()
    values = values[values != ""]
    return int(values.nunique())


def _count_paper_trades() -> tuple[int, int, int]:
    total = open_count = closed = 0

    trades = _read_csv_safe(PAPER_TRADES_FILE)
    if trades is not None and not trades.empty:
        total = int(len(trades))
        if "status" in trades.columns:
            status = trades["status"].astype(str).str.upper()
            open_count = int(status.isin(["OPEN", "ACTIVE", "PENDING"]).sum())
            closed = int(status.isin(["CLOSED", "WIN", "LOSS", "BREAKEVEN"]).sum())

    evals = _read_csv_safe(PAPER_EVALUATIONS_FILE)
    if evals is not None and not evals.empty:
        if "status" in evals.columns:
            status = evals["status"].astype(str).str.upper()
            closed = max(closed, int(status.isin(["CLOSED", "WIN", "LOSS", "BREAKEVEN"]).sum()))
        else:
            closed = max(closed, int(len(evals)))

    return total, open_count, closed


def _count_regime_samples() -> tuple[int, int]:
    df = _read_csv_safe(EVALUATIONS_FILE)
    if df is None or df.empty or "regime_label" not in df.columns:
        return 0, _count_complete_evaluations()

    labels = df["regime_label"].fillna("UNKNOWN").astype(str).str.strip().str.upper()
    complete_mask = None
    if "evaluation_status" in df.columns:
        complete_mask = df["evaluation_status"].astype(str).str.upper() == "COMPLETE"
    else:
        complete_mask = labels.notna()

    labels = labels[complete_mask]
    known = int((labels != "UNKNOWN").sum())
    unknown = int((labels == "UNKNOWN").sum())
    return known, unknown


def _read_run_rows() -> List[dict]:
    if not RUNS_CSV.exists():
        return []
    try:
        with RUNS_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def _parse_dt(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def build_forward_progress() -> ForwardProgress:
    complete = _count_complete_evaluations()
    total_paper, open_paper, closed_paper = _count_paper_trades()
    known_regime, unknown_regime = _count_regime_samples()
    rows = _read_run_rows()

    successes = [row for row in rows if str(row.get("ok", "")).lower() in {"true", "1", "yes", "ok"}]
    starts = [_parse_dt(row.get("started_utc", "")) for row in rows]
    starts = [dt for dt in starts if dt]
    first = min(starts).isoformat() if starts else ""
    last = max(starts).isoformat() if starts else ""
    forward_days = 0
    if starts:
        dates = {dt.date().isoformat() for dt in starts}
        forward_days = len(dates)

    score = 0
    score += min(25, int((complete / TARGET_COMPLETE_EVALUATIONS) * 25))
    score += min(25, int((closed_paper / TARGET_CLOSED_PAPER_TRADES) * 25))
    score += min(20, int((known_regime / TARGET_REGIME_LABELED) * 20))
    score += min(15, int((forward_days / TARGET_FORWARD_DAYS) * 15))
    score += min(15, int((len(successes) / 20) * 15))

    blockers: List[str] = []
    notes: List[str] = []
    next_actions: List[str] = []

    if complete < TARGET_COMPLETE_EVALUATIONS:
        blockers.append(f"Complete evaluations کمتر از {TARGET_COMPLETE_EVALUATIONS} است: {complete}")
        next_actions.append("اجرای منظم decision_evaluator.py بعد از ثبت تصمیم‌های جدید.")
    else:
        notes.append("Complete evaluations به حد پایه Forward Test رسیده است.")

    if closed_paper < TARGET_CLOSED_PAPER_TRADES:
        blockers.append(f"Closed paper trades کمتر از {TARGET_CLOSED_PAPER_TRADES} است: {closed_paper}")
        next_actions.append("اجرای portfolio_scanner.py --paper تا فقط فرصت‌های مجاز Paper ثبت شوند.")
    else:
        notes.append("Closed paper trades به حد پایه Forward Test رسیده است.")

    if known_regime < TARGET_REGIME_LABELED:
        blockers.append(f"Regime-labeled samples کمتر از {TARGET_REGIME_LABELED} است: {known_regime}")
        next_actions.append("forward_regime_label_dashboard.py و چند اجرای جدید monitor.py --once پس از v6.2.1 لازم است تا regime_label وارد لاگ‌ها و evaluationها شود.")
    else:
        notes.append("Regime-labeled samples برای تحلیل اولیه کافی است.")

    if forward_days < TARGET_FORWARD_DAYS:
        blockers.append(f"روزهای Forward Test کمتر از {TARGET_FORWARD_DAYS} است: {forward_days}")
        next_actions.append("این چرخه را روزانه یا هر کندل 4h اجرا کن تا حداقل 30 روز داده Forward جمع شود.")
    else:
        notes.append("مدت Forward Test به حد پایه 30 روز رسیده است.")

    if closed_paper >= TARGET_CLOSED_PAPER_TRADES and complete >= TARGET_COMPLETE_EVALUATIONS:
        readiness_level = "PAPER_TRADING_PHASE"
        paper_ready = True
    else:
        readiness_level = "RESEARCH_ONLY"
        paper_ready = False

    live_ready = False
    if complete >= 100 and closed_paper >= 50 and known_regime >= 30 and forward_days >= 30:
        readiness_level = "MICRO_LIVE_REVIEW_CANDIDATE"
        live_ready = False
        blockers.append("قبل از Micro Live، باید Advanced Live Readiness همچنان MICRO_LIVE_READY را تأیید کند.")

    return ForwardProgress(
        status="FORWARD_TEST_COLLECTING" if blockers else "FORWARD_TEST_BASELINE_MET",
        complete_evaluations=complete,
        closed_paper_trades=closed_paper,
        open_paper_trades=open_paper,
        total_paper_trades=total_paper,
        regime_labeled_samples=known_regime,
        unknown_regime_samples=unknown_regime,
        distinct_symbols_evaluated=_count_distinct_symbols(EVALUATIONS_FILE),
        distinct_symbols_scanned=_count_distinct_symbols(PORTFOLIO_SCANS_FILE),
        forward_run_count=len(rows),
        successful_run_count=len(successes),
        first_run_utc=first,
        last_run_utc=last,
        forward_days_observed=forward_days,
        readiness_level=readiness_level,
        paper_ready=paper_ready,
        live_ready=live_ready,
        progress_score=max(0, min(100, score)),
        notes=notes,
        blockers=blockers,
        next_actions=next_actions,
    )


def _tail(text: str, max_chars: int = 1200) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _safe_filename(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)


def run_forward_cycle(
    plan: ForwardPlan,
    *,
    continue_on_error: bool = True,
    dry_run: bool = False,
) -> ForwardRunResult:
    started = _utc_now()
    run_id = f"forward_{_utc_stamp(started)}"
    FORWARD_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = FORWARD_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if dry_run:
        finished = _utc_now()
        result = ForwardRunResult(
            run_id=run_id,
            started_utc=_iso(started),
            finished_utc=_iso(finished),
            duration_seconds=0.0,
            mode="DRY_RUN",
            ok=True,
            tasks=[
                TaskRunResult(
                    name=task.name,
                    command=" ".join(task.command),
                    started_utc=_iso(started),
                    finished_utc=_iso(started),
                    duration_seconds=0.0,
                    return_code=0,
                    ok=True,
                )
                for task in plan.tasks
            ],
        )
        report = save_forward_run_report(result, progress=build_forward_progress())
        result.report_file = str(report)
        return result

    task_results: List[TaskRunResult] = []
    overall_ok = True
    blockers: List[str] = []

    for task in plan.tasks:
        task_start = _utc_now()
        safe = _safe_filename(task.name)
        out_path = run_dir / f"{safe}.stdout.txt"
        err_path = run_dir / f"{safe}.stderr.txt"

        try:
            completed = subprocess.run(
                task.command,
                cwd=Path.cwd(),
                env=_forward_child_env(),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=None,
            )
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
            return_code = int(completed.returncode)
        except Exception as exc:
            stdout = ""
            stderr = f"{type(exc).__name__}: {exc}"
            return_code = 999

        out_path.write_text(stdout, encoding="utf-8")
        err_path.write_text(stderr, encoding="utf-8")

        task_finish = _utc_now()
        ok = return_code == 0
        if not ok and task.required:
            overall_ok = False
            blockers.append(f"Required task failed: {task.name} rc={return_code}")

        task_results.append(
            TaskRunResult(
                name=task.name,
                command=" ".join(task.command),
                started_utc=_iso(task_start),
                finished_utc=_iso(task_finish),
                duration_seconds=round((task_finish - task_start).total_seconds(), 2),
                return_code=return_code,
                ok=ok,
                output_file=str(out_path),
                error_file=str(err_path),
                stdout_tail=_tail(stdout),
                stderr_tail=_tail(stderr),
            )
        )

        if not ok and task.required and not continue_on_error:
            break

    finished = _utc_now()
    result = ForwardRunResult(
        run_id=run_id,
        started_utc=_iso(started),
        finished_utc=_iso(finished),
        duration_seconds=round((finished - started).total_seconds(), 2),
        mode="EXECUTE",
        ok=overall_ok,
        tasks=task_results,
        blockers=blockers,
    )
    report = save_forward_run_report(result, progress=build_forward_progress())
    result.report_file = str(report)
    append_forward_run(result)
    return result


def append_forward_run(result: ForwardRunResult) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_id",
        "started_utc",
        "finished_utc",
        "duration_seconds",
        "mode",
        "ok",
        "task_count",
        "failed_tasks",
        "report_file",
    ]
    exists = RUNS_CSV.exists()
    failed_tasks = ";".join(task.name for task in result.tasks if not task.ok)
    with RUNS_CSV.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "run_id": result.run_id,
                "started_utc": result.started_utc,
                "finished_utc": result.finished_utc,
                "duration_seconds": result.duration_seconds,
                "mode": result.mode,
                "ok": result.ok,
                "task_count": len(result.tasks),
                "failed_tasks": failed_tasks,
                "report_file": result.report_file,
            }
        )


def format_forward_plan_console(plan: ForwardPlan) -> str:
    lines = [
        "=" * 110,
        f"🧭 Freakto Forward Test Plan {VERSION}",
        "=" * 110,
        "این برنامه فقط جمع‌آوری داده و Paper/Validation را اجرا می‌کند؛ هیچ سفارش واقعی ارسال نمی‌شود.",
        "",
        "Tasks:",
    ]
    for idx, task in enumerate(plan.tasks, start=1):
        required = "required" if task.required else "optional"
        lines.append(f"{idx}. {task.name} [{required}]")
        lines.append(f"   Command: {' '.join(task.command)}")
        if task.description:
            lines.append(f"   Note   : {task.description}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_forward_progress_console(progress: ForwardProgress) -> str:
    lines = [
        "=" * 110,
        f"🧭 Freakto Forward Test Status {VERSION}",
        "=" * 110,
        f"Status          : {progress.status}",
        f"Progress Score  : {progress.progress_score}/100",
        f"Readiness Level : {progress.readiness_level}",
        f"Paper Ready     : {progress.paper_ready}",
        f"Live Ready      : {progress.live_ready}",
        "",
        "Data Progress:",
        f"- Complete evaluations : {progress.complete_evaluations}/{TARGET_COMPLETE_EVALUATIONS}",
        f"- Closed paper trades  : {progress.closed_paper_trades}/{TARGET_CLOSED_PAPER_TRADES}",
        f"- Open paper trades    : {progress.open_paper_trades}",
        f"- Total paper trades   : {progress.total_paper_trades}",
        f"- Regime-labeled       : {progress.regime_labeled_samples}/{TARGET_REGIME_LABELED}",
        f"- Unknown regime       : {progress.unknown_regime_samples}",
        f"- Symbols evaluated    : {progress.distinct_symbols_evaluated}",
        f"- Symbols scanned      : {progress.distinct_symbols_scanned}",
        f"- Forward runs         : {progress.successful_run_count}/{progress.forward_run_count} successful",
        f"- Forward days         : {progress.forward_days_observed}/{TARGET_FORWARD_DAYS}",
    ]

    if progress.first_run_utc or progress.last_run_utc:
        lines.extend([
            f"- First run UTC        : {progress.first_run_utc or 'NONE'}",
            f"- Last run UTC         : {progress.last_run_utc or 'NONE'}",
        ])

    if progress.notes:
        lines.append("\nNotes:")
        for note in progress.notes:
            lines.append(f"✓ {note}")

    if progress.blockers:
        lines.append("\nBlockers:")
        for blocker in progress.blockers:
            lines.append(f"⛔ {blocker}")

    if progress.next_actions:
        lines.append("\nNext Actions:")
        seen = set()
        for action in progress.next_actions:
            if action in seen:
                continue
            seen.add(action)
            lines.append(f"→ {action}")

    lines.extend([
        "",
        "Safe cycle command:",
        "python forward_test_dashboard.py --cycle --validate",
        "",
        "Windows scheduled-task/batch friendly command:",
        "python forward_test_dashboard.py --cycle --validate --continue-on-error",
        "=" * 110,
    ])
    return "\n".join(lines)


def format_forward_run_console(result: ForwardRunResult) -> str:
    lines = [
        "=" * 110,
        f"🧭 Freakto Forward Test Run {VERSION}",
        "=" * 110,
        f"Run ID       : {result.run_id}",
        f"Mode         : {result.mode}",
        f"OK           : {result.ok}",
        f"Started UTC  : {result.started_utc}",
        f"Finished UTC : {result.finished_utc}",
        f"Duration     : {result.duration_seconds}s",
        "",
        "Tasks:",
    ]
    for task in result.tasks:
        status = "OK" if task.ok else "FAILED"
        lines.append(f"- {task.name}: {status} | rc={task.return_code} | {task.duration_seconds}s")
        lines.append(f"  Command: {task.command}")
        if task.stdout_tail:
            tail = task.stdout_tail.replace("\n", " | ")[:500]
            lines.append(f"  Out: {tail}")
        if task.stderr_tail:
            tail = task.stderr_tail.replace("\n", " | ")[:500]
            lines.append(f"  Err: {tail}")

    if result.blockers:
        lines.append("\nRun Blockers:")
        for blocker in result.blockers:
            lines.append(f"⛔ {blocker}")

    if result.report_file:
        lines.append(f"\nReport saved: {result.report_file}")

    lines.append("=" * 110)
    return "\n".join(lines)


def save_forward_progress(progress: Optional[ForwardProgress] = None) -> tuple[Path, Path]:
    progress = progress or build_forward_progress()
    FORWARD_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _utc_stamp()
    json_path = FORWARD_DIR / f"forward_test_status_{stamp}.json"
    report_path = FORWARD_DIR / f"forward_test_status_{stamp}.md"
    json_path.write_text(json.dumps(asdict(progress), ensure_ascii=False, indent=2), encoding="utf-8")
    report_path.write_text(format_forward_progress_console(progress), encoding="utf-8")
    return json_path, report_path


def save_forward_run_report(result: ForwardRunResult, *, progress: Optional[ForwardProgress] = None) -> Path:
    FORWARD_DIR.mkdir(parents=True, exist_ok=True)
    path = FORWARD_DIR / f"{result.run_id}_report.md"
    progress_text = format_forward_progress_console(progress or build_forward_progress())
    text = format_forward_run_console(result) + "\n\n" + progress_text
    path.write_text(text, encoding="utf-8")
    return path


def write_windows_batch_files() -> List[Path]:
    """Create local helper .bat files for Windows users."""
    files: List[Path] = []
    cycle = Path("run_forward_test_cycle.bat")
    cycle.write_text(
        "@echo off\r\n"
        "cd /d %~dp0\r\n"
        "python forward_test_dashboard.py --cycle --validate --continue-on-error\r\n"
        "pause\r\n",
        encoding="utf-8",
    )
    files.append(cycle)

    status = Path("run_forward_test_status.bat")
    status.write_text(
        "@echo off\r\n"
        "cd /d %~dp0\r\n"
        "python forward_test_dashboard.py --status\r\n"
        "pause\r\n",
        encoding="utf-8",
    )
    files.append(status)

    return files
