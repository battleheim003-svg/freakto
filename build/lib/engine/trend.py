from .common import ScoreComponent, safe_float


def score_trend(row, side: str) -> ScoreComponent:
    close = safe_float(row.get("close"))
    sma_10 = safe_float(row.get("sma_10"))
    sma_30 = safe_float(row.get("sma_30"))
    ema_10 = safe_float(row.get("ema_10"))

    points = 0
    reasons = []
    warnings = []

    if side == "LONG":
        if close and sma_10 and sma_30 and close > sma_10 > sma_30:
            points += 22
            reasons.append("روند کوتاه‌مدت صعودی و هم‌راستاست؛ قیمت بالای میانگین‌های مهم قرار دارد.")
        elif close and sma_30 and close > sma_30:
            points += 11
            reasons.append("قیمت بالای میانگین ۳۰ کندلی است؛ فشار روند بیشتر به سمت خریداران است.")
        else:
            warnings.append("ساختار روند برای لانگ کاملاً تأیید نشده است.")

        if close and ema_10 and close > ema_10:
            points += 6
            reasons.append("قیمت بالای EMA10 است؛ مومنتوم کوتاه‌مدت هنوز حفظ شده است.")

    elif side == "SHORT":
        if close and sma_10 and sma_30 and close < sma_10 < sma_30:
            points += 22
            reasons.append("روند کوتاه‌مدت نزولی و هم‌راستاست؛ قیمت زیر میانگین‌های مهم قرار دارد.")
        elif close and sma_30 and close < sma_30:
            points += 11
            reasons.append("قیمت زیر میانگین ۳۰ کندلی است؛ فشار روند بیشتر به سمت فروشندگان است.")
        else:
            warnings.append("ساختار روند برای شورت کاملاً تأیید نشده است.")

        if close and ema_10 and close < ema_10:
            points += 6
            reasons.append("قیمت زیر EMA10 است؛ مومنتوم کوتاه‌مدت نزولی حفظ شده است.")

    return ScoreComponent("Trend", min(points, 28), 28, side, reasons, warnings)
