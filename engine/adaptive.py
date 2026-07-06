"""
engine/adaptive.py

Adaptive Scoring Engine

این ماژول بر اساس Market Regime وزن تصمیم را تنظیم می‌کند.
هدف این است که Score فقط جمع ساده اندیکاتورها نباشد، بلکه با شرایط بازار تطبیق پیدا کند.
"""

from .common import ScoreComponent


def _points(components, name: str) -> int:
    for component in components:
        if component.name == name:
            return component.points
    return 0


def score_adaptive_adjustment(components, regime, side: str) -> ScoreComponent:
    points = 0
    reasons = []
    warnings = []

    trend = _points(components, "Trend")
    momentum = _points(components, "Momentum")
    volume = _points(components, "Volume")
    structure = _points(components, "Structure")
    risk = _points(components, "Risk Penalty")

    label = getattr(regime, "label", "UNKNOWN")

    if label == "TRENDING_BULL":
        if side == "LONG":
            if trend >= 24 and structure >= 8:
                points += 4
                reasons.append("Adaptive: در رژیم صعودی، Trend و Structure قوی وزن بیشتری می‌گیرند.")

            if momentum >= 22:
                points += 2
                reasons.append("Adaptive: مومنتوم در جهت رژیم صعودی تأیید شده است.")

            if volume < 5:
                points -= 3
                warnings.append("Adaptive: با وجود رژیم صعودی، حجم هنوز تأیید کافی نداده است.")

        elif side == "SHORT":
            points -= 8
            warnings.append("Adaptive: شورت گرفتن خلاف رژیم TRENDING_BULL است.")

    elif label == "TRENDING_BEAR":
        if side == "SHORT":
            if trend >= 24 and structure >= 8:
                points += 4
                reasons.append("Adaptive: در رژیم نزولی، Trend و Structure قوی وزن بیشتری می‌گیرند.")

            if momentum >= 22:
                points += 2
                reasons.append("Adaptive: مومنتوم در جهت رژیم نزولی تأیید شده است.")

            if volume < 5:
                points -= 3
                warnings.append("Adaptive: با وجود رژیم نزولی، حجم هنوز تأیید کافی نداده است.")

        elif side == "LONG":
            points -= 8
            warnings.append("Adaptive: لانگ گرفتن خلاف رژیم TRENDING_BEAR است.")

    elif label == "SIDEWAYS":
        points -= 5
        warnings.append("Adaptive: بازار رنج است؛ سیگنال‌های جهت‌دار سخت‌گیرانه‌تر ارزیابی می‌شوند.")

        if volume >= 8 and structure >= 8:
            points += 3
            reasons.append("Adaptive: در بازار رنج، حجم و ساختار خوب کمی از جریمه را جبران می‌کنند.")

    elif label == "VOLATILE":
        points -= 4
        warnings.append("Adaptive: بازار پرنوسان است؛ ریسک شکست فیک و نوسان شدید بیشتر است.")

        if risk <= -8:
            points -= 3
            warnings.append("Adaptive: ریسک هم‌زمان با نوسان بالا زیاد شده است.")

    elif label == "QUIET":
        points -= 2
        warnings.append("Adaptive: بازار کم‌نوسان است؛ احتمال کمبود انرژی حرکت وجود دارد.")

        if volume >= 10:
            points += 3
            reasons.append("Adaptive: در بازار کم‌نوسان، ورود حجم می‌تواند نشانه شروع حرکت باشد.")

    else:
        warnings.append("Adaptive: Market Regime نامشخص است؛ تنظیم خاصی اعمال نشد.")

    points = max(-10, min(10, points))

    return ScoreComponent(
        name="Adaptive Adjustment",
        points=points,
        max_points=10,
        reasons=reasons,
        warnings=warnings,
    )