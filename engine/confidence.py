from dataclasses import dataclass, field
from typing import List


@dataclass
class ConfidenceResult:
    value: int
    label: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    explanation: List[str] = field(default_factory=list)


def _component_ratio(opportunity, name: str) -> float:
    for component in opportunity.components:
        if component.name == name and component.max_points > 0:
            return max(0.0, component.points / component.max_points)
    return 0.0


def confidence_label(value: int) -> str:
    if value >= 80:
        return "High"
    if value >= 60:
        return "Medium"
    if value >= 40:
        return "Low-Medium"
    return "Low"


def calculate_confidence(opportunity) -> ConfidenceResult:
    trend = _component_ratio(opportunity, "Trend")
    momentum = _component_ratio(opportunity, "Momentum")
    volume = _component_ratio(opportunity, "Volume")
    structure = _component_ratio(opportunity, "Structure")

    regime_confidence = opportunity.raw.get("regime_confidence", 0) or 0
    regime_score = min(1.0, max(0.0, regime_confidence / 100))

    base = (
        trend * 30
        + momentum * 25
        + structure * 20
        + volume * 15
        + regime_score * 10
    )

    penalty = 0

    risk_penalty = abs(opportunity.component_points("Risk Penalty"))
    penalty += min(15, risk_penalty)

    quality_failures = opportunity.quality_gate_failures
    penalty += min(20, len(quality_failures) * 6)

    value = int(max(0, min(100, base - penalty)))

    strengths = []
    weaknesses = []
    explanation = []

    if trend >= 0.75:
        strengths.append("Trend")
    elif trend < 0.4:
        weaknesses.append("Trend")

    if momentum >= 0.7:
        strengths.append("Momentum")
    elif momentum < 0.45:
        weaknesses.append("Momentum")

    if structure >= 0.7:
        strengths.append("Structure")
    elif structure < 0.45:
        weaknesses.append("Structure")

    if volume >= 0.6:
        strengths.append("Volume")
    elif volume < 0.35:
        weaknesses.append("Volume")

    if regime_score >= 0.7:
        strengths.append("Market Regime")
    elif regime_score < 0.4:
        weaknesses.append("Market Regime")

    if value >= 80:
        explanation.append("اعتماد بالا است چون چند مؤلفه اصلی بازار هم‌زمان هم‌راستا هستند.")
    elif value >= 60:
        explanation.append("اعتماد متوسط است؛ جهت بازار مشخص است اما همه تأییدها کامل نیستند.")
    else:
        explanation.append("اعتماد پایین‌تر است چون چند مؤلفه کلیدی هنوز کامل تأیید نشده‌اند.")

    if quality_failures:
        explanation.append("Quality Gate هنوز کامل پاس نشده و همین باعث کاهش Confidence شده است.")

    if risk_penalty > 0:
        explanation.append(f"ریسک‌ها حدود {risk_penalty} امتیاز از کیفیت تصمیم کم کرده‌اند.")

    return ConfidenceResult(
        value=value,
        label=confidence_label(value),
        strengths=strengths,
        weaknesses=weaknesses,
        explanation=explanation,
    )