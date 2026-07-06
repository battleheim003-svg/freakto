"""
engine.performance

Freakto Performance & Learning Engine - v3.0.0

این ماژول لاگ‌های تصمیم، ارزیابی تصمیم‌ها، اسکن پورتفو و گزارش‌های روزانه را می‌خواند
و یک داشبورد متنی/Markdown از عملکرد سیستم می‌سازد.

وابستگی به داده بیرونی ندارد و اگر بعضی فایل‌های لاگ هنوز وجود نداشته باشند،
به شکل امن با داده‌های موجود گزارش می‌سازد.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


LOGS_DIR = Path("logs")
REPORTS_DIR = LOGS_DIR / "reports"
PERFORMANCE_DIR = LOGS_DIR / "performance"

DECISIONS_FILE = LOGS_DIR / "decisions.csv"
EVALUATIONS_FILE = LOGS_DIR / "decision_evaluations.csv"
PORTFOLIO_FILE = LOGS_DIR / "portfolio_scans.csv"


@dataclass
class MetricBlock:
    title: str
    lines: List[str] = field(default_factory=list)


@dataclass
class PerformanceReport:
    created_at_utc: str
    title: str
    summary: List[str] = field(default_factory=list)
    blocks: List[MetricBlock] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    markdown: str = ""


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except Exception:
        return default


def _pct(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return part / total * 100


def _fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def _fmt_num(value: float) -> str:
    return f"{value:.2f}"


def _latest_rows(df: pd.DataFrame, count: int = 5) -> pd.DataFrame:
    if df.empty:
        return df
    return df.tail(count)


def _value_counts_lines(df: pd.DataFrame, column: str, title: str) -> List[str]:
    if df.empty or column not in df.columns:
        return [f"{title}: داده‌ای موجود نیست."]

    counts = df[column].fillna("UNKNOWN").astype(str).value_counts()
    total = int(counts.sum())

    lines = [f"{title}:"]
    for name, value in counts.items():
        lines.append(f"- {name}: {value} ({_fmt_pct(_pct(int(value), total))})")

    return lines


def _build_decision_block(decisions: pd.DataFrame) -> MetricBlock:
    block = MetricBlock(title="Decision Log")

    if decisions.empty:
        block.lines.append("هنوز لاگ تصمیمی وجود ندارد.")
        return block

    total = len(decisions)
    block.lines.append(f"تعداد کل تصمیم‌های ثبت‌شده: {total}")

    if "score" in decisions.columns:
        scores = pd.to_numeric(decisions["score"], errors="coerce").dropna()
        if not scores.empty:
            block.lines.append(f"میانگین Score: {_fmt_num(float(scores.mean()))}")
            block.lines.append(f"بیشترین Score: {_fmt_num(float(scores.max()))}")
            block.lines.append(f"کمترین Score: {_fmt_num(float(scores.min()))}")

    if "side" in decisions.columns:
        block.lines.extend(_value_counts_lines(decisions, "side", "توزیع Bias"))

    if "actionability" in decisions.columns:
        block.lines.extend(_value_counts_lines(decisions, "actionability", "توزیع Actionability"))

    if "provider" in decisions.columns:
        block.lines.extend(_value_counts_lines(decisions, "provider", "توزیع Provider"))

    return block


def _build_evaluation_block(evaluations: pd.DataFrame) -> MetricBlock:
    block = MetricBlock(title="Decision Evaluation")

    if evaluations.empty:
        block.lines.append("هنوز فایل decision_evaluations.csv وجود ندارد یا داده‌ای داخل آن نیست.")
        block.lines.append("برای فعال شدن این بخش اجرا کن: python decision_evaluator.py")
        return block

    total = len(evaluations)
    block.lines.append(f"تعداد تصمیم‌های ارزیابی‌شده: {total}")

    status_col = "evaluation_status"
    if status_col in evaluations.columns:
        block.lines.extend(_value_counts_lines(evaluations, status_col, "وضعیت ارزیابی"))

    complete = evaluations
    if status_col in evaluations.columns:
        complete = evaluations[evaluations[status_col].astype(str).str.upper() == "COMPLETE"]

    if complete.empty:
        block.lines.append("هنوز ارزیابی کامل کافی وجود ندارد.")
        return block

    block.lines.append(f"تصمیم‌های COMPLETE: {len(complete)}")

    for col, label in [
        ("return_after_4h_pct", "میانگین بازده 4h"),
        ("return_after_12h_pct", "میانگین بازده 12h"),
        ("return_after_24h_pct", "میانگین بازده 24h"),
        ("mfe_pct", "میانگین MFE"),
        ("mae_pct", "میانگین MAE"),
    ]:
        if col in complete.columns:
            values = pd.to_numeric(complete[col], errors="coerce").dropna()
            if not values.empty:
                block.lines.append(f"{label}: {_fmt_num(float(values.mean()))}%")

    for col, label in [
        ("target_1_hit", "T1 Hit Rate"),
        ("target_2_hit", "T2 Hit Rate"),
        ("target_3_hit", "T3 Hit Rate"),
        ("stop_hit", "Stop Hit Rate"),
    ]:
        if col in complete.columns:
            hits = complete[col].astype(str).str.lower().isin(["true", "1", "yes"])
            block.lines.append(f"{label}: {_fmt_pct(_pct(int(hits.sum()), len(complete)))}")

    if "side" in complete.columns:
        block.lines.extend(_value_counts_lines(complete, "side", "ارزیابی بر اساس Side"))

    return block


def _build_portfolio_block(portfolio: pd.DataFrame) -> MetricBlock:
    block = MetricBlock(title="Portfolio Scanner")

    if portfolio.empty:
        block.lines.append("هنوز portfolio_scans.csv وجود ندارد یا داده‌ای داخل آن نیست.")
        block.lines.append("برای فعال شدن این بخش اجرا کن: python portfolio_scanner.py")
        return block

    total = len(portfolio)
    block.lines.append(f"تعداد ردیف‌های اسکن پورتفو: {total}")

    if "symbol" in portfolio.columns:
        symbols = portfolio["symbol"].dropna().astype(str).nunique()
        block.lines.append(f"تعداد نمادهای یکتا: {symbols}")

    for col, label in [
        ("opportunity_score", "میانگین Opportunity Score"),
        ("score", "میانگین Decision Score"),
        ("confidence", "میانگین Confidence"),
        ("rr", "میانگین R:R"),
        ("breadth_strength", "میانگین Market Agreement (legacy breadth_strength)"),
        ("breadth_avg_opportunity", "میانگین Breadth Opportunity"),
    ]:
        if col in portfolio.columns:
            values = pd.to_numeric(portfolio[col], errors="coerce").dropna()
            if not values.empty:
                suffix = "%" if "confidence" in col else ""
                block.lines.append(f"{label}: {_fmt_num(float(values.mean()))}{suffix}")

    for col, title in [
        ("recommendation", "توزیع Recommendation"),
        ("trade_grade", "توزیع Trade Grade"),
        ("quality_label", "توزیع Quality"),
        ("breadth_mode", "توزیع Market Mode"),
        ("breadth_risk_tone", "توزیع Risk Tone"),
    ]:
        if col in portfolio.columns:
            block.lines.extend(_value_counts_lines(portfolio, col, title))

    latest = _latest_rows(portfolio, 6)
    if not latest.empty and {"symbol", "opportunity_score", "recommendation"}.issubset(set(latest.columns)):
        block.lines.append("آخرین کاندیداهای ثبت‌شده:")
        for _, row in latest.iterrows():
            symbol = row.get("symbol", "-")
            opp = _safe_float(row.get("opportunity_score"), 0.0)
            rec = row.get("recommendation", "-")
            side = row.get("side", "-")
            block.lines.append(f"- {symbol}: {side} | Opp {_fmt_num(opp)} | {rec}")

    return block


def _build_reports_block() -> MetricBlock:
    block = MetricBlock(title="Daily Reports")

    if not REPORTS_DIR.exists():
        block.lines.append("هنوز پوشه گزارش‌های روزانه ساخته نشده است.")
        return block

    reports = sorted(REPORTS_DIR.glob("daily_report_*.md"))
    block.lines.append(f"تعداد گزارش‌های روزانه ذخیره‌شده: {len(reports)}")

    if reports:
        latest = reports[-1]
        block.lines.append(f"آخرین گزارش: {latest}")

    return block


def _build_learning_recommendations(decisions, evaluations, portfolio) -> List[str]:
    recs = []

    if decisions.empty:
        recs.append("اولویت: جمع‌آوری داده بیشتر؛ هنوز تصمیم کافی برای تحلیل عملکرد وجود ندارد.")
    else:
        if "actionability" in decisions.columns:
            actionable = decisions[decisions["actionability"].astype(str).isin(["ACTIONABLE", "HIGH_ACTIONABILITY"])]
            if len(actionable) == 0:
                recs.append("موتور فعلاً بسیار محافظه‌کار است؛ قبل از شل کردن فیلترها، چند روز داده بیشتر جمع‌آوری شود.")

    if evaluations.empty:
        recs.append("برای فعال شدن یادگیری عملکرد، decision_evaluator.py را بعد از تشکیل کندل‌های جدید اجرا کن.")
    else:
        if "stop_hit" in evaluations.columns:
            stops = evaluations["stop_hit"].astype(str).str.lower().isin(["true", "1", "yes"])
            if len(stops) > 0 and _pct(int(stops.sum()), len(stops)) > 50:
                recs.append("Stop Hit Rate بالا دیده می‌شود؛ پیشنهاد: Quality Gate حجم و ساختار سخت‌گیرتر بررسی شود.")

        if "return_after_24h_pct" in evaluations.columns:
            returns = pd.to_numeric(evaluations["return_after_24h_pct"], errors="coerce").dropna()
            if not returns.empty and returns.mean() < 0:
                recs.append("میانگین بازده 24h منفی است؛ پیشنهاد: Historical Edge و MTF روی ورودهای جهت‌دار وزن بیشتری بگیرند.")

    if not portfolio.empty:
        rec_col = "recommendation"
        if rec_col in portfolio.columns:
            actionable = portfolio[portfolio[rec_col].astype(str).isin(["ELITE", "ACTIONABLE", "WATCHLIST"])]
            if actionable.empty:
                recs.append("اسکن پورتفو هیچ فرصت جدی نداده؛ این رفتار سالم است، اما برای فرصت‌یابی بیشتر می‌توان تعداد نمادها را افزایش داد.")

    if not recs:
        recs.append("وضعیت داده‌ها طبیعی است؛ مرحله بعد می‌تواند بهینه‌سازی پارامترها یا افزایش نمادهای پورتفو باشد.")

    return recs


def build_performance_report() -> PerformanceReport:
    decisions = _read_csv(DECISIONS_FILE)
    evaluations = _read_csv(EVALUATIONS_FILE)
    portfolio = _read_csv(PORTFOLIO_FILE)

    created = datetime.now(timezone.utc).isoformat()
    report = PerformanceReport(
        created_at_utc=created,
        title="Freakto Performance & Learning Dashboard v3.0",
    )

    report.blocks = [
        _build_decision_block(decisions),
        _build_evaluation_block(evaluations),
        _build_portfolio_block(portfolio),
        _build_reports_block(),
    ]

    report.summary.append("داشبورد عملکرد بر اساس لاگ‌های موجود ساخته شد.")
    report.summary.append(f"Decisions: {len(decisions)} | Evaluations: {len(evaluations)} | Portfolio rows: {len(portfolio)}")

    if evaluations.empty:
        report.warnings.append("فایل decision_evaluations.csv موجود نیست یا خالی است؛ بخش عملکرد واقعی هنوز کامل نیست.")

    if portfolio.empty:
        report.warnings.append("فایل portfolio_scans.csv موجود نیست یا خالی است؛ بخش پورتفو هنوز کامل نیست.")

    report.recommendations = _build_learning_recommendations(decisions, evaluations, portfolio)
    report.markdown = format_performance_markdown(report)

    return report


def format_performance_console(report: PerformanceReport) -> str:
    lines = []
    lines.append("=" * 110)
    lines.append(f"📈 {report.title}")
    lines.append("=" * 110)
    lines.append(f"Created UTC: {report.created_at_utc}")
    lines.append("")

    lines.append("Summary:")
    for item in report.summary:
        lines.append(f"- {item}")

    for block in report.blocks:
        lines.append("")
        lines.append("-" * 110)
        lines.append(block.title)
        lines.append("-" * 110)
        for item in block.lines:
            lines.append(str(item))

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for item in report.warnings:
            lines.append(f"⚠️ {item}")

    if report.recommendations:
        lines.append("")
        lines.append("Learning Recommendations:")
        for item in report.recommendations:
            lines.append(f"✓ {item}")

    lines.append("=" * 110)
    return "\n".join(lines)


def format_performance_telegram(report: PerformanceReport) -> str:
    lines = []
    lines.append("📈 *Freakto Performance Dashboard v3.0*")
    lines.append(f"Created UTC: `{report.created_at_utc}`")
    lines.append("")

    for item in report.summary[:3]:
        lines.append(f"- {item}")

    for block in report.blocks[:3]:
        lines.append("")
        lines.append(f"*{block.title}:*")
        for item in block.lines[:8]:
            lines.append(f"- {item}")

    if report.recommendations:
        lines.append("")
        lines.append("*Learning Recommendations:*")
        for item in report.recommendations[:5]:
            lines.append(f"- {item}")

    return "\n".join(lines)


def format_performance_markdown(report: PerformanceReport) -> str:
    lines = []
    lines.append(f"# {report.title}")
    lines.append("")
    lines.append(f"Created UTC: `{report.created_at_utc}`")
    lines.append("")

    lines.append("## Summary")
    for item in report.summary:
        lines.append(f"- {item}")
    lines.append("")

    for block in report.blocks:
        lines.append(f"## {block.title}")
        for item in block.lines:
            lines.append(f"- {item}")
        lines.append("")

    if report.warnings:
        lines.append("## Warnings")
        for item in report.warnings:
            lines.append(f"- ⚠️ {item}")
        lines.append("")

    if report.recommendations:
        lines.append("## Learning Recommendations")
        for item in report.recommendations:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("---")
    lines.append("این گزارش توصیه مالی نیست؛ فقط داشبورد عملکرد و یادگیری موتور Freakto است.")
    lines.append("")

    return "\n".join(lines)


def save_performance_report(report: PerformanceReport) -> Path:
    PERFORMANCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = PERFORMANCE_DIR / f"performance_report_{timestamp}.md"
    path.write_text(report.markdown, encoding="utf-8")
    return path
