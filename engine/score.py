from dataclasses import dataclass, field
from typing import Any, Dict, List

import pandas as pd

from .common import ScoreComponent, safe_float, fmt_price
from .trend import score_trend
from .momentum import score_momentum
from .volume import score_volume
from .structure import score_structure
from .risk import score_risk, risk_label
from .explain import explain_component, explain_decision
from .confidence import calculate_confidence
from .similarity import find_similar_snapshots, format_similarity_for_telegram
from .trade_quality import build_trade_intelligence_card, format_trade_card_lines
from .intelligence import build_intelligence_report, format_intelligence_telegram


@dataclass
class OpportunityV2:
    symbol: str
    timeframe: str
    side: str
    score: int
    confidence_label: str
    risk_label: str
    entry_zone: str
    stop_zone: str
    targets: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    components: List[ScoreComponent] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def component_points(self, name: str) -> int:
        for component in self.components:
            if component.name == name:
                return component.points
        return 0

    @property
    def confidence(self):
        return calculate_confidence(self)

    @property
    def quality_gate_failures(self) -> List[str]:
        failures = []

        trend = self.component_points("Trend")
        momentum = self.component_points("Momentum")
        volume = self.component_points("Volume")
        structure = self.component_points("Structure")
        risk = self.component_points("Risk Penalty")
        regime = self.raw.get("regime_label", "UNKNOWN")

        if self.side not in {"LONG", "SHORT"}:
            failures.append("Bias مشخص و قابل معامله نیست.")

        if self.score < 70:
            failures.append("Score هنوز به حداقل 70 نرسیده است.")

        if trend < 20:
            failures.append("Trend تأیید کافی ندارد.")

        if momentum < 18:
            failures.append("Momentum تأیید کافی ندارد.")

        if structure < 6:
            failures.append("Structure تأیید کافی ندارد.")

        if volume < 5:
            failures.append("Volume هنوز شکست/حرکت را تأیید نکرده است.")

        if risk <= -10:
            failures.append("Risk Penalty بیش از حد بالاست.")

        if regime == "SIDEWAYS":
            failures.append("Market Regime رنج است و کیفیت سیگنال جهت‌دار کاهش دارد.")

        return failures

    @property
    def high_quality_gate_failures(self) -> List[str]:
        failures = []

        trend = self.component_points("Trend")
        momentum = self.component_points("Momentum")
        volume = self.component_points("Volume")
        structure = self.component_points("Structure")
        risk = self.component_points("Risk Penalty")
        regime = self.raw.get("regime_label", "UNKNOWN")

        if self.score < 85:
            failures.append("Score برای High Actionability کافی نیست.")

        if trend < 26:
            failures.append("Trend برای فرصت درجه‌یک کافی نیست.")

        if momentum < 24:
            failures.append("Momentum برای فرصت درجه‌یک کافی نیست.")

        if structure < 10:
            failures.append("Structure برای فرصت درجه‌یک کافی نیست.")

        if volume < 12:
            failures.append("Volume برای فرصت درجه‌یک کافی نیست.")

        if risk <= -5:
            failures.append("Risk Penalty برای فرصت درجه‌یک زیاد است.")

        if regime not in {"TRENDING_BULL", "TRENDING_BEAR"}:
            failures.append("Market Regime برای فرصت درجه‌یک هم‌راستا نیست.")

        return failures

    @property
    def is_actionable(self) -> bool:
        return self.side in {"LONG", "SHORT"} and len(self.quality_gate_failures) == 0

    @property
    def actionability_label(self) -> str:
        if self.side == "NEUTRAL":
            return "MONITOR_ONLY"

        if len(self.high_quality_gate_failures) == 0:
            return "HIGH_ACTIONABILITY"

        if len(self.quality_gate_failures) == 0:
            return "ACTIONABLE"

        if self.score >= 55:
            return "WATCHLIST"

        return "NOT_ACTIONABLE"

    @property
    def actionability_fa(self) -> str:
        labels = {
            "HIGH_ACTIONABILITY": "قابل توجه / کیفیت بالا",
            "ACTIONABLE": "قابل بررسی",
            "WATCHLIST": "واچ‌لیست؛ ارزش زیرنظر گرفتن دارد",
            "NOT_ACTIONABLE": "غیرقابل اقدام",
            "MONITOR_ONLY": "فقط مانیتور",
        }
        return labels.get(self.actionability_label, "نامشخص")


def confidence_label(score: int) -> str:
    if score >= 85:
        return "High"
    if score >= 70:
        return "Medium-High"
    if score >= 55:
        return "Medium"
    return "Low"


def _dedupe_text(items: List[str]) -> List[str]:
    seen = set()
    result = []

    for item in items:
        key = str(item).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)

    return result


def _zones(row, side: str) -> tuple[str, str, list[str]]:
    close = safe_float(row.get("close"))
    atr_pct = safe_float(row.get("atr_pct"), 0.0) or 0.0

    if not close or not atr_pct:
        return "نامشخص", "نامشخص", []

    atr_abs = close * atr_pct

    if side == "LONG":
        entry_low = close - atr_abs * 0.25
        entry_high = close + atr_abs * 0.15
        stop = close - atr_abs * 1.2
        targets = [
            close + atr_abs * 1.0,
            close + atr_abs * 1.8,
            close + atr_abs * 2.6,
        ]

    elif side == "SHORT":
        entry_low = close - atr_abs * 0.15
        entry_high = close + atr_abs * 0.25
        stop = close + atr_abs * 1.2
        targets = [
            close - atr_abs * 1.0,
            close - atr_abs * 1.8,
            close - atr_abs * 2.6,
        ]

    else:
        return "نامشخص", "نامشخص", []

    return (
        f"{fmt_price(entry_low)} - {fmt_price(entry_high)}",
        fmt_price(stop),
        [fmt_price(target) for target in targets],
    )


def _format_actionability(opportunity: OpportunityV2) -> List[str]:
    lines = [
        "*Actionability:*",
        f"- Status: *{opportunity.actionability_label}*",
        f"- توضیح: {opportunity.actionability_fa}",
    ]

    if opportunity.actionability_label == "NOT_ACTIONABLE":
        lines.append("- نتیجه: این وضعیت هنوز سیگنال ورود جدی نیست.")
    elif opportunity.actionability_label == "WATCHLIST":
        lines.append("- نتیجه: بازار ارزش زیرنظر گرفتن دارد، اما Quality Gate هنوز کامل پاس نشده است.")
    elif opportunity.actionability_label == "MONITOR_ONLY":
        lines.append("- نتیجه: فعلاً فقط باید بازار مانیتور شود.")
    elif opportunity.actionability_label == "ACTIONABLE":
        lines.append("- نتیجه: قابل بررسی است، اما نیاز به مدیریت ریسک دارد.")
    elif opportunity.actionability_label == "HIGH_ACTIONABILITY":
        lines.append("- نتیجه: شرایط از نظر موتور قوی است، اما همچنان بدون تضمین.")

    return lines


def _format_confidence(opportunity: OpportunityV2) -> List[str]:
    confidence = opportunity.confidence

    lines = [
        "*Confidence Engine:*",
        f"- Overall Confidence: *{confidence.value}%* ({confidence.label})",
    ]

    if confidence.strengths:
        lines.append(f"- نقاط قوت: {', '.join(confidence.strengths)}")

    if confidence.weaknesses:
        lines.append(f"- نقاط ضعف: {', '.join(confidence.weaknesses)}")

    if confidence.explanation:
        lines.append("- توضیح:")
        for item in confidence.explanation[:4]:
            lines.append(f"  • {item}")

    return lines


def _format_trade_intelligence(opportunity: OpportunityV2) -> List[str]:
    card = build_trade_intelligence_card(opportunity)
    return format_trade_card_lines(card)




def _format_intelligence_layer(opportunity: OpportunityV2) -> List[str]:
    report = build_intelligence_report(opportunity)
    return format_intelligence_telegram(report)

def _format_market_regime(opportunity: OpportunityV2) -> List[str]:
    label = opportunity.raw.get("regime_label")
    confidence = opportunity.raw.get("regime_confidence")
    adjustment = opportunity.raw.get("regime_adjustment")
    reasons = opportunity.raw.get("regime_reasons", [])
    warnings = opportunity.raw.get("regime_warnings", [])

    if not label:
        return []

    lines = [
        "*Market Regime:*",
        f"- Regime: *{label}*",
        f"- Confidence: *{confidence}%*",
        f"- Score Impact: `{adjustment}`",
    ]

    if reasons:
        lines.append("- دلایل:")
        for reason in reasons[:3]:
            lines.append(f"  ✓ {reason}")

    if warnings:
        lines.append("- هشدارها:")
        for warning in warnings[:3]:
            lines.append(f"  ⚠️ {warning}")

    return lines


def _format_quality_gate(opportunity: OpportunityV2) -> List[str]:
    lines = ["*Quality Gate:*"]
    failures = opportunity.quality_gate_failures

    if not failures:
        lines.append("- ✅ همه شرط‌های حداقلی کیفیت پاس شده‌اند.")
        return lines

    lines.append("- ❌ هنوز همه شرط‌های کیفیت پاس نشده‌اند.")
    lines.append("- دلیل عدم ارتقا:")

    for failure in failures[:6]:
        lines.append(f"  ⚠️ {failure}")

    return lines


def _weak_components(opportunity: OpportunityV2) -> List[str]:
    weak = []

    for component in opportunity.components:
        if component.name in {"Risk Penalty", "Regime Adjustment"}:
            continue

        if component.points <= 0:
            weak.append(component.name)

    return weak


def _strong_components(opportunity: OpportunityV2) -> List[str]:
    strong = []

    for component in opportunity.components:
        if component.name in {"Risk Penalty", "Regime Adjustment"}:
            continue

        if component.max_points > 0 and component.points / component.max_points >= 0.65:
            strong.append(component.name)

    return strong


def _format_watchlist_summary(opportunity: OpportunityV2) -> List[str]:
    if opportunity.actionability_label != "WATCHLIST":
        return []

    weak = _weak_components(opportunity)
    strong = _strong_components(opportunity)

    lines = [
        "*Watchlist Summary:*",
        "- این وضعیت هنوز سیگنال ورود جدی نیست، اما ارزش زیرنظر گرفتن دارد.",
    ]

    if strong:
        lines.append(f"- عوامل مثبت: {', '.join(strong)}")

    if weak:
        lines.append(f"- عامل‌های ناقص اصلی: {', '.join(weak)}")

    if opportunity.quality_gate_failures:
        lines.append("- مانع اصلی ارتقا:")
        for failure in opportunity.quality_gate_failures[:3]:
            lines.append(f"  ⚠️ {failure}")

    return lines


def _format_score_breakdown(opportunity: OpportunityV2) -> List[str]:
    lines = ["*Score Breakdown:*"]

    for component in opportunity.components:
        sign = "+" if component.points > 0 else ""
        lines.append(
            f"- {component.name}: `{sign}{component.points}` / {component.max_points}"
        )

    return lines


def _format_decision_explanation(opportunity: OpportunityV2) -> List[str]:
    lines = ["*Decision Explanation:*"]

    explanation_lines = explain_decision(
        side=opportunity.side,
        score=opportunity.score,
        components=opportunity.components,
    )

    for line in explanation_lines:
        lines.append(f"- {line}")

    return lines


def _format_component_explanations(opportunity: OpportunityV2) -> List[str]:
    lines = ["*Component Explanations:*"]

    for component in opportunity.components:
        lines.extend(explain_component(component))
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    return lines


def format_opportunity_v2_message(opportunity: OpportunityV2) -> str:
    icon = (
        "🟢" if opportunity.side == "LONG"
        else "🔴" if opportunity.side == "SHORT"
        else "⚪"
    )

    title = "Freakto Market Bias v4"
    if opportunity.is_actionable:
        title = "Freakto Opportunity Engine v4"

    lines = [
        f"{icon} *{title}*",
        f"Symbol: {opportunity.symbol} | TF: {opportunity.timeframe}",
        f"Market Bias: *{opportunity.side}*",
        f"Score: *{opportunity.score}/100* ({opportunity.confidence_label})",
        f"Risk: *{opportunity.risk_label}*",
        "",
    ]

    lines.extend(_format_actionability(opportunity))

    lines.append("")
    lines.extend(_format_confidence(opportunity))

    similarity = find_similar_snapshots(opportunity)
    lines.append("")
    lines.extend(format_similarity_for_telegram(similarity))

    lines.append("")
    lines.extend(_format_trade_intelligence(opportunity))

    lines.append("")
    lines.extend(_format_intelligence_layer(opportunity))

    market_regime = _format_market_regime(opportunity)
    if market_regime:
        lines.append("")
        lines.extend(market_regime)

    lines.append("")
    lines.extend(_format_quality_gate(opportunity))

    watchlist_summary = _format_watchlist_summary(opportunity)
    if watchlist_summary:
        lines.append("")
        lines.extend(watchlist_summary)

    lines.append("")
    lines.extend(_format_score_breakdown(opportunity))

    if opportunity.is_actionable:
        lines.extend([
            "",
            f"Entry Zone: `{opportunity.entry_zone}`",
            f"Stop Zone: `{opportunity.stop_zone}`",
        ])

        if opportunity.targets:
            lines.append("Targets:")
            for index, target in enumerate(opportunity.targets, start=1):
                lines.append(f"  T{index}: `{target}`")
    else:
        lines.extend([
            "",
            "Entry Zone: `نمایش داده نمی‌شود چون Quality Gate کامل پاس نشده است`",
            "Stop Zone: `نمایش داده نمی‌شود چون Quality Gate کامل پاس نشده است`",
        ])

    lines.append("")
    lines.extend(_format_decision_explanation(opportunity))

    lines.append("")
    lines.extend(_format_component_explanations(opportunity))

    deduped_warnings = _dedupe_text(opportunity.warnings)
    if deduped_warnings:
        lines.append("")
        lines.append("*هشدارهای ریسک:*")
        for warning in deduped_warnings[:6]:
            lines.append(f"⚠️ {warning}")

    lines.append("")
    lines.append(
        "این خروجی توصیه مالی یا دستور خرید/فروش نیست؛ فقط امتیازدهی شفاف به شرایط فعلی بازار است."
    )

    return "\n".join(lines)


def analyze_opportunity_v2(df: pd.DataFrame, symbol: str, timeframe: str) -> OpportunityV2:
    raise RuntimeError(
        "analyze_opportunity_v2 دیگر مسیر اصلی نیست. از DecisionEngine در engine/decision.py استفاده کن."
    )