"""
engine.self_learning

Freakto Self-Learning Engine - v3.1.0

این ماژول از لاگ‌های واقعی Freakto یاد می‌گیرد و پیشنهادهای محافظه‌کارانه
برای بهینه‌سازی وزن‌ها و Quality Gate ارائه می‌دهد.

نکته مهم:
- این ماژول فعلاً هیچ وزن یا قانون اجرایی را خودکار تغییر نمی‌دهد.
- فقط گزارش و توصیه تولید می‌کند تا قبل از اعمال تغییر، قابل بررسی باشد.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json

import pandas as pd


LOGS_DIR = Path("logs")
LEARNING_DIR = LOGS_DIR / "learning"

DECISIONS_FILE = LOGS_DIR / "decisions.csv"
EVALUATIONS_FILE = LOGS_DIR / "decision_evaluations.csv"
PORTFOLIO_FILE = LOGS_DIR / "portfolio_scans.csv"


@dataclass
class LearningSignal:
    name: str
    status: str
    evidence: str
    recommendation: str
    severity: str = "INFO"


@dataclass
class LearningReport:
    created_at_utc: str
    title: str
    sample_size: int = 0
    complete_evaluations: int = 0
    summary: List[str] = field(default_factory=list)
    signals: List[LearningSignal] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    markdown: str = ""
    recommendations_json: Dict = field(default_factory=dict)


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


def _safe_bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes", "y"])


def _fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def _fmt_num(value: float) -> str:
    return f"{value:.2f}"


def _merge_decisions_and_evaluations() -> pd.DataFrame:
    decisions = _read_csv(DECISIONS_FILE)
    evaluations = _read_csv(EVALUATIONS_FILE)

    if evaluations.empty:
        return pd.DataFrame()

    if decisions.empty or "decision_id" not in decisions.columns or "decision_id" not in evaluations.columns:
        return evaluations.copy()

    # suffixes keep evaluation fields as the primary truth where duplicated.
    merged = evaluations.merge(
        decisions,
        on="decision_id",
        how="left",
        suffixes=("", "_decision"),
    )

    return merged


def _complete_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "evaluation_status" not in df.columns:
        return df

    return df[df["evaluation_status"].astype(str).str.upper() == "COMPLETE"].copy()


def _win_rate(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0

    if "target_1_hit" in df.columns:
        hits = _safe_bool_series(df["target_1_hit"])
        return float(hits.mean() * 100)

    if "return_after_24h_pct" in df.columns:
        returns = pd.to_numeric(df["return_after_24h_pct"], errors="coerce").dropna()
        if returns.empty:
            return 0.0
        return float((returns > 0).mean() * 100)

    return 0.0


def _stop_rate(df: pd.DataFrame) -> float:
    if df.empty or "stop_hit" not in df.columns:
        return 0.0
    return float(_safe_bool_series(df["stop_hit"]).mean() * 100)


def _avg_return(df: pd.DataFrame, col: str = "return_after_24h_pct") -> float:
    if df.empty or col not in df.columns:
        return 0.0
    values = pd.to_numeric(df[col], errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float(values.mean())


def _component_column(df: pd.DataFrame, name: str) -> Optional[str]:
    candidates = [name, f"{name}_decision"]
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _score_bucket(value: float) -> str:
    if value >= 80:
        return "80+"
    if value >= 70:
        return "70-79"
    if value >= 60:
        return "60-69"
    if value >= 50:
        return "50-59"
    return "<50"


def _analyze_overall(complete: pd.DataFrame) -> List[LearningSignal]:
    signals: List[LearningSignal] = []

    if complete.empty:
        return signals

    wr = _win_rate(complete)
    sr = _stop_rate(complete)
    avg24 = _avg_return(complete)
    avg4 = _avg_return(complete, "return_after_4h_pct")

    if wr >= 60 and avg24 > 0:
        signals.append(
            LearningSignal(
                name="Overall Edge",
                status="POSITIVE",
                evidence=f"Win Rate={_fmt_pct(wr)} | Avg 24h={_fmt_num(avg24)}% | Stop={_fmt_pct(sr)}",
                recommendation="هسته تصمیم‌گیری فعلاً Edge مثبت نشان می‌دهد؛ تغییرات وزن باید محافظه‌کارانه و کوچک باشد.",
                severity="INFO",
            )
        )
    elif wr < 45 or avg24 < 0:
        signals.append(
            LearningSignal(
                name="Overall Edge",
                status="WEAK",
                evidence=f"Win Rate={_fmt_pct(wr)} | Avg 24h={_fmt_num(avg24)}% | Avg 4h={_fmt_num(avg4)}%",
                recommendation="تا جمع‌آوری داده بیشتر، Quality Gate سخت‌گیرانه‌تر شود و وزن Volume/MTF افزایش یابد.",
                severity="WARNING",
            )
        )
    else:
        signals.append(
            LearningSignal(
                name="Overall Edge",
                status="MIXED",
                evidence=f"Win Rate={_fmt_pct(wr)} | Avg 24h={_fmt_num(avg24)}% | Stop={_fmt_pct(sr)}",
                recommendation="نتایج هنوز مخلوط است؛ قبل از تغییر وزن‌ها، نمونه‌های COMPLETE بیشتری جمع‌آوری شود.",
                severity="INFO",
            )
        )

    return signals


def _analyze_score_buckets(complete: pd.DataFrame) -> List[LearningSignal]:
    signals: List[LearningSignal] = []

    score_col = _component_column(complete, "score")
    if complete.empty or not score_col:
        return signals

    work = complete.copy()
    work["_score_num"] = pd.to_numeric(work[score_col], errors="coerce")
    work = work.dropna(subset=["_score_num"])

    if work.empty:
        return signals

    work["_bucket"] = work["_score_num"].apply(_score_bucket)

    for bucket, group in work.groupby("_bucket"):
        if len(group) < 3:
            continue

        wr = _win_rate(group)
        avg24 = _avg_return(group)
        sr = _stop_rate(group)

        if bucket in {"70-79", "80+"} and avg24 <= 0:
            signals.append(
                LearningSignal(
                    name=f"Score Bucket {bucket}",
                    status="OVERVALUED",
                    evidence=f"Samples={len(group)} | Win={_fmt_pct(wr)} | Avg 24h={_fmt_num(avg24)}% | Stop={_fmt_pct(sr)}",
                    recommendation="امتیازهای بالا هنوز بازده کافی نداده‌اند؛ برای ACTIONABLE شدن، Volume یا MTF تأیید بیشتری لازم شود.",
                    severity="WARNING",
                )
            )
        elif bucket in {"60-69", "70-79", "80+"} and avg24 > 0 and wr >= 55:
            signals.append(
                LearningSignal(
                    name=f"Score Bucket {bucket}",
                    status="VALIDATED",
                    evidence=f"Samples={len(group)} | Win={_fmt_pct(wr)} | Avg 24h={_fmt_num(avg24)}%",
                    recommendation="این بازه امتیازی رفتار قابل قبول دارد؛ فعلاً کاهش وزن لازم نیست.",
                    severity="INFO",
                )
            )

    return signals


def _analyze_components(complete: pd.DataFrame) -> List[LearningSignal]:
    signals: List[LearningSignal] = []

    component_map = {
        "trend_score": "Trend",
        "momentum_score": "Momentum",
        "volume_score": "Volume",
        "structure_score": "Structure",
        "risk_penalty": "Risk",
    }

    for col, label in component_map.items():
        real_col = _component_column(complete, col)
        if not real_col:
            continue

        work = complete.copy()
        work["_component"] = pd.to_numeric(work[real_col], errors="coerce")
        work = work.dropna(subset=["_component"])

        if len(work) < 5:
            continue

        median_value = float(work["_component"].median())
        high = work[work["_component"] >= median_value]
        low = work[work["_component"] < median_value]

        if len(high) < 3 or len(low) < 3:
            continue

        high_return = _avg_return(high)
        low_return = _avg_return(low)
        spread = high_return - low_return

        if spread >= 0.4:
            signals.append(
                LearningSignal(
                    name=f"Component Weight: {label}",
                    status="SUPPORTIVE",
                    evidence=f"High {label} Avg24={_fmt_num(high_return)}% vs Low Avg24={_fmt_num(low_return)}%",
                    recommendation=f"{label} در داده فعلی اثر مثبت دارد؛ کاهش وزن آن پیشنهاد نمی‌شود.",
                    severity="INFO",
                )
            )
        elif spread <= -0.4:
            signals.append(
                LearningSignal(
                    name=f"Component Weight: {label}",
                    status="QUESTIONABLE",
                    evidence=f"High {label} Avg24={_fmt_num(high_return)}% vs Low Avg24={_fmt_num(low_return)}%",
                    recommendation=f"اثر {label} در داده فعلی ضعیف/معکوس است؛ بعد از افزایش نمونه‌ها کاهش وزن آزمایشی بررسی شود.",
                    severity="WARNING",
                )
            )

    return signals


def _analyze_actionability(complete: pd.DataFrame) -> List[LearningSignal]:
    signals: List[LearningSignal] = []
    action_col = _component_column(complete, "actionability")

    if complete.empty or not action_col:
        return signals

    for action, group in complete.groupby(action_col):
        if len(group) < 3:
            continue

        avg24 = _avg_return(group)
        wr = _win_rate(group)

        if str(action).upper() in {"WATCHLIST", "ACTIONABLE", "HIGH_ACTIONABILITY"}:
            if avg24 < 0:
                signals.append(
                    LearningSignal(
                        name=f"Actionability: {action}",
                        status="TOO_LOOSE",
                        evidence=f"Samples={len(group)} | Win={_fmt_pct(wr)} | Avg 24h={_fmt_num(avg24)}%",
                        recommendation="برای ارتقا به Watchlist/Actionable، شرط Volume یا MTF سخت‌گیرانه‌تر شود.",
                        severity="WARNING",
                    )
                )
            elif wr >= 55:
                signals.append(
                    LearningSignal(
                        name=f"Actionability: {action}",
                        status="OK",
                        evidence=f"Samples={len(group)} | Win={_fmt_pct(wr)} | Avg 24h={_fmt_num(avg24)}%",
                        recommendation="این سطح Actionability فعلاً رفتار قابل قبول دارد.",
                        severity="INFO",
                    )
                )

    return signals


def _build_recommendations_json(report: LearningReport) -> Dict:
    warnings = [s for s in report.signals if s.severity.upper() == "WARNING"]

    suggested_actions = []
    for signal in warnings:
        suggested_actions.append({
            "name": signal.name,
            "status": signal.status,
            "recommendation": signal.recommendation,
            "evidence": signal.evidence,
        })

    return {
        "version": "3.1.0",
        "created_at_utc": report.created_at_utc,
        "sample_size": report.sample_size,
        "complete_evaluations": report.complete_evaluations,
        "mode": "advisory_only",
        "auto_apply": False,
        "suggested_actions": suggested_actions,
    }


def _build_markdown(report: LearningReport) -> str:
    lines = []
    lines.append(f"# {report.title}")
    lines.append("")
    lines.append(f"Created UTC: {report.created_at_utc}")
    lines.append("")
    lines.append("## Summary")
    for line in report.summary:
        lines.append(f"- {line}")

    if report.warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in report.warnings:
            lines.append(f"- ⚠️ {warning}")

    lines.append("")
    lines.append("## Learning Signals")

    if not report.signals:
        lines.append("- هنوز سیگنال یادگیری کافی وجود ندارد.")
    else:
        for signal in report.signals:
            icon = "⚠️" if signal.severity.upper() == "WARNING" else "✅"
            lines.append(f"### {icon} {signal.name}")
            lines.append(f"- Status: {signal.status}")
            lines.append(f"- Evidence: {signal.evidence}")
            lines.append(f"- Recommendation: {signal.recommendation}")
            lines.append("")

    lines.append("## Policy")
    lines.append("- این موتور فعلاً فقط توصیه می‌دهد و هیچ وزن یا قانون اجرایی را خودکار تغییر نمی‌دهد.")
    lines.append("- برای اعمال خودکار وزن‌ها، ابتدا باید تعداد نمونه‌های COMPLETE بیشتر شود.")

    return "\n".join(lines).strip() + "\n"


def build_self_learning_report() -> LearningReport:
    created = datetime.now(timezone.utc).isoformat()
    merged = _merge_decisions_and_evaluations()
    complete = _complete_rows(merged)

    report = LearningReport(
        created_at_utc=created,
        title="Freakto Self-Learning Report v3.1",
        sample_size=len(merged),
        complete_evaluations=len(complete),
    )

    report.summary.append(f"Evaluation rows: {len(merged)}")
    report.summary.append(f"Complete evaluations: {len(complete)}")

    if merged.empty:
        report.warnings.append("هیچ فایل ارزیابی معتبری پیدا نشد. اول python decision_evaluator.py را اجرا کن.")
    elif len(complete) < 10:
        report.warnings.append("تعداد ارزیابی‌های کامل کمتر از 10 است؛ توصیه‌ها فقط جهت مشاهده هستند.")
    elif len(complete) < 30:
        report.warnings.append("نمونه‌های COMPLETE هنوز کم هستند؛ تغییر وزن‌ها باید محافظه‌کارانه باشد.")

    if not complete.empty:
        report.summary.append(f"Overall Win Rate: {_fmt_pct(_win_rate(complete))}")
        report.summary.append(f"Avg 24h Return: {_fmt_num(_avg_return(complete))}%")
        report.summary.append(f"Stop Rate: {_fmt_pct(_stop_rate(complete))}")

        report.signals.extend(_analyze_overall(complete))
        report.signals.extend(_analyze_score_buckets(complete))
        report.signals.extend(_analyze_components(complete))
        report.signals.extend(_analyze_actionability(complete))

    if not report.signals:
        report.signals.append(
            LearningSignal(
                name="Data Readiness",
                status="WAITING",
                evidence=f"Complete evaluations={len(complete)}",
                recommendation="برای یادگیری قابل اتکا، مانیتور و decision_evaluator را در چند کندل آینده ادامه بده.",
                severity="INFO",
            )
        )

    report.recommendations_json = _build_recommendations_json(report)
    report.markdown = _build_markdown(report)
    return report


def format_self_learning_console(report: LearningReport) -> str:
    lines = []
    lines.append("=" * 110)
    lines.append("🧠 Freakto Self-Learning Engine v3.1")
    lines.append("=" * 110)
    lines.append(f"Created UTC: {report.created_at_utc}")
    lines.append("")
    lines.append("Summary:")
    for line in report.summary:
        lines.append(f"- {line}")

    if report.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in report.warnings:
            lines.append(f"⚠️ {warning}")

    lines.append("")
    lines.append("Learning Signals:")
    for signal in report.signals:
        icon = "⚠️" if signal.severity.upper() == "WARNING" else "✅"
        lines.append("-" * 110)
        lines.append(f"{icon} {signal.name} | {signal.status}")
        lines.append(f"Evidence      : {signal.evidence}")
        lines.append(f"Recommendation: {signal.recommendation}")

    lines.append("=" * 110)
    return "\n".join(lines)


def format_self_learning_telegram(report: LearningReport) -> str:
    lines = []
    lines.append("🧠 *Freakto Self-Learning v3.1*")
    lines.append(f"Complete evaluations: `{report.complete_evaluations}`")

    for line in report.summary[:4]:
        lines.append(f"- {line}")

    warning_signals = [s for s in report.signals if s.severity.upper() == "WARNING"]
    info_signals = [s for s in report.signals if s.severity.upper() != "WARNING"]
    selected = warning_signals[:3] if warning_signals else info_signals[:3]

    if selected:
        lines.append("")
        lines.append("*Top Learning Signals:*")
        for signal in selected:
            lines.append(f"• {signal.name}: {signal.status}")
            lines.append(f"  {signal.recommendation}")

    lines.append("")
    lines.append("Auto-apply: OFF")
    return "\n".join(lines)


def save_self_learning_report(report: LearningReport) -> Path:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = LEARNING_DIR / f"self_learning_report_{stamp}.md"
    path.write_text(report.markdown, encoding="utf-8")
    return path


def save_recommendations_json(report: LearningReport) -> Path:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    path = LEARNING_DIR / "self_learning_recommendations.json"
    path.write_text(
        json.dumps(report.recommendations_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
