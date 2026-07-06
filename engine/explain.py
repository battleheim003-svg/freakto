from typing import List

from .common import ScoreComponent


def component_strength(component: ScoreComponent) -> str:
    """
    قدرت هر بخش را نسبت به حداکثر امتیاز خودش توضیح می‌دهد.
    """
    if component.max_points <= 0:
        return "نامشخص"

    ratio = component.points / component.max_points

    if component.name == "Risk Penalty":
        penalty = abs(component.points)
        if penalty >= 16:
            return "ریسک بالا"
        if penalty >= 6:
            return "ریسک متوسط"
        return "ریسک پایین"

    if ratio >= 0.75:
        return "قوی"
    if ratio >= 0.40:
        return "متوسط"
    if ratio > 0:
        return "ضعیف"
    return "بدون تأیید"


def explain_component(component: ScoreComponent) -> List[str]:
    """
    برای هر بخش، یک توضیح قابل‌فهم تولید می‌کند.
    """
    lines = []
    strength = component_strength(component)

    if component.name == "Trend":
        lines.append(f"🧭 Trend: {strength} ({component.points}/{component.max_points})")
    elif component.name == "Momentum":
        lines.append(f"⚡ Momentum: {strength} ({component.points}/{component.max_points})")
    elif component.name == "Volume":
        lines.append(f"📊 Volume: {strength} ({component.points}/{component.max_points})")
    elif component.name == "Structure":
        lines.append(f"🏗 Structure: {strength} ({component.points}/{component.max_points})")
    elif component.name == "Risk Penalty":
        lines.append(f"🛡 Risk: {strength} ({component.points})")
    else:
        lines.append(f"{component.name}: {strength} ({component.points}/{component.max_points})")

    if component.reasons:
        for reason in component.reasons[:3]:
            lines.append(f"  ✓ {reason}")

    if component.warnings:
        for warning in component.warnings[:2]:
            lines.append(f"  ⚠️ {warning}")

    if not component.reasons and not component.warnings:
        lines.append("  - سیگنال مشخصی از این بخش دریافت نشد.")

    return lines


def explain_confidence(score: int, components: List[ScoreComponent]) -> List[str]:
    """
    توضیح می‌دهد چرا Confidence نهایی در این سطح قرار گرفته است.
    """
    lines = []

    positive_components = [
        c for c in components
        if c.name != "Risk Penalty" and c.points > 0
    ]

    weak_components = [
        c for c in components
        if c.name != "Risk Penalty" and c.points <= 0
    ]

    risk_component = next(
        (c for c in components if c.name == "Risk Penalty"),
        None,
    )

    if score >= 85:
        lines.append("Confidence بسیار بالاست چون چند بخش اصلی بازار هم‌زمان تأیید شده‌اند.")
    elif score >= 70:
        lines.append("Confidence خوب است، اما هنوز چند عامل می‌توانند کیفیت فرصت را محدود کنند.")
    elif score >= 55:
        lines.append("Confidence متوسط است؛ بعضی عوامل مثبت هستند اما هنوز تأیید کامل وجود ندارد.")
    else:
        lines.append("Confidence پایین است؛ هم‌راستایی کافی بین بخش‌های اصلی بازار دیده نمی‌شود.")

    if positive_components:
        names = "، ".join(c.name for c in positive_components[:4])
        lines.append(f"بخش‌های مثبت اصلی: {names}")

    if weak_components:
        names = "، ".join(c.name for c in weak_components[:4])
        lines.append(f"بخش‌هایی که هنوز تأیید کافی نداده‌اند: {names}")

    if risk_component and risk_component.points < 0:
        lines.append(f"ریسک‌ها {abs(risk_component.points)} امتیاز از نتیجه کم کرده‌اند.")
    elif risk_component:
        lines.append("فعلاً جریمه ریسک مهمی روی این فرصت اعمال نشده است.")

    return lines


def explain_decision(side: str, score: int, components: List[ScoreComponent]) -> List[str]:
    """
    خلاصه انسانی تصمیم نهایی موتور.
    """
    lines = []

    if side == "LONG":
        lines.append("Bias فعلی بازار به سمت LONG است.")
    elif side == "SHORT":
        lines.append("Bias فعلی بازار به سمت SHORT است.")
    else:
        lines.append("بازار فعلاً Bias قابل‌اعتماد و قابل اقدام ندارد.")

    lines.extend(explain_confidence(score, components))

    return lines