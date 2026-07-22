"""
engine.metric_definitions

Freakto v4.7.1 Metric Definition Clarity

Central glossary for validation metrics so dashboards do not use ambiguous
phrases such as generic "Win Rate" when different modules measure different
things.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List

LOGS_DIR = Path("logs")
METRIC_DIR = LOGS_DIR / "metric_definitions"


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    short_label: str
    source: str
    formula: str
    meaning: str
    used_in: str


METRIC_DEFINITIONS: List[MetricDefinition] = [
    MetricDefinition(
        name="Directional Win Rate",
        short_label="Dir Win",
        source="decision_evaluations.csv",
        formula="count(return_after_24h_pct > 0) / count(valid evaluated returns)",
        meaning="درصد تصمیم‌هایی که بازده ارزیابی‌شده آن‌ها مثبت شده است. اگر 24h هنوز موجود نباشد، ماژول‌های ارزیابی ممکن است به 12h یا 4h fallback کنند.",
        used_in="Edge Validation, Walk-Forward, Live Readiness notes",
    ),
    MetricDefinition(
        name="Target 1 Hit Rate",
        short_label="T1 Hit",
        source="decision_evaluations.csv",
        formula="count(target_1_hit == True) / count(COMPLETE evaluations)",
        meaning="درصد تصمیم‌هایی که تارگت اول را زده‌اند. این با مثبت بودن بازده یکی نیست؛ ممکن است بازده مثبت باشد ولی T1 نخورده باشد.",
        used_in="Strategy Lab, Regime Matrix, historical target validation",
    ),
    MetricDefinition(
        name="Paper Trade Win Rate",
        short_label="Paper Win",
        source="paper_trade_evaluations.csv",
        formula="count(closed paper trades with positive R or WIN result) / count(closed paper trades)",
        meaning="درصد معاملات فرضی بسته‌شده که بر اساس R Multiple یا نتیجه ثبت‌شده سودده بوده‌اند.",
        used_in="Paper Trading, Live Readiness",
    ),
    MetricDefinition(
        name="Expectancy",
        short_label="Expectancy",
        source="decision_evaluations.csv / paper_trade_evaluations.csv",
        formula="average(return_after_24h_pct) for decisions OR average(r_multiple) for paper trades",
        meaning="میانگین سود/زیان مورد انتظار در نمونه‌های موجود. برای تصمیم‌ها درصدی و برای Paper Trade بر حسب R است.",
        used_in="Edge Validation, Live Readiness, Strategy Lab",
    ),
    MetricDefinition(
        name="Profit Factor",
        short_label="PF",
        source="evaluated returns",
        formula="gross positive returns / abs(gross negative returns)",
        meaning="نسبت مجموع سودها به مجموع زیان‌ها. در نمونه‌های خیلی کم یا بدون زیان می‌تواند بزرگ و ناپایدار باشد.",
        used_in="Edge Validation, Regime Matrix, Live Readiness",
    ),
]


def format_metric_definitions_console() -> str:
    lines = []
    lines.append("=" * 110)
    lines.append("📘 Freakto Metric Definitions v4.7.1")
    lines.append("=" * 110)
    lines.append("هدف: حذف ابهام بین Directional Win Rate، Target Hit Rate و Paper Trade Win Rate.")
    lines.append("")
    for item in METRIC_DEFINITIONS:
        lines.append("-" * 110)
        lines.append(f"Metric    : {item.name}")
        lines.append(f"Label     : {item.short_label}")
        lines.append(f"Source    : {item.source}")
        lines.append(f"Formula   : {item.formula}")
        lines.append(f"Meaning   : {item.meaning}")
        lines.append(f"Used In   : {item.used_in}")
    lines.append("=" * 110)
    return "\n".join(lines)


def save_metric_definitions_report() -> Path:
    METRIC_DIR.mkdir(parents=True, exist_ok=True)
    path = METRIC_DIR / f"metric_definitions_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    lines = ["# Freakto Metric Definitions v4.7.1", "", f"Created UTC: {datetime.now(timezone.utc).isoformat()}", ""]
    for item in METRIC_DEFINITIONS:
        lines.append(f"## {item.name}")
        lines.append(f"- Label: {item.short_label}")
        lines.append(f"- Source: {item.source}")
        lines.append(f"- Formula: `{item.formula}`")
        lines.append(f"- Meaning: {item.meaning}")
        lines.append(f"- Used in: {item.used_in}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
