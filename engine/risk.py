from .common import ScoreComponent, safe_float


def risk_label(component: ScoreComponent) -> str:
    penalty = abs(component.points)

    if penalty >= 16:
        return "High"
    if penalty >= 7:
        return "Medium"
    return "Low"


def score_risk(row, side: str) -> ScoreComponent:
    """
    Risk Engine v2

    خروجی این ماژول امتیاز منفی است.

    ریسک‌هایی که بررسی می‌کند:
    - RSI نزدیک اشباع
    - ATR بالا / نوسان غیرعادی
    - کندل با بدنه ضعیف
    - فاصله زیاد قیمت از EMA10
    - جهت کندل مخالف Bias
    - نبود حجم تأییدی در حرکت
    """

    points = 0
    reasons = []
    warnings = []

    close = safe_float(row.get("close"), 0.0) or 0.0
    open_ = safe_float(row.get("open"), 0.0) or 0.0
    high = safe_float(row.get("high"), 0.0) or 0.0
    low = safe_float(row.get("low"), 0.0) or 0.0
    ema_10 = safe_float(row.get("ema_10"), 0.0) or 0.0
    rsi = safe_float(row.get("rsi_14"), 50.0) or 50.0
    atr_pct = safe_float(row.get("atr_pct"), 0.0) or 0.0

    volume = safe_float(row.get("volume"), 0.0) or 0.0
    volume_sma = safe_float(row.get("volume_sma_20"), 0.0) or 0.0

    candle_range = high - low
    candle_body = abs(close - open_)
    body_ratio = candle_body / candle_range if candle_range > 0 else 0

    bullish_candle = close > open_
    bearish_candle = close < open_

    # 1) RSI Risk
    if side == "LONG":
        if rsi >= 78:
            points -= 7
            warnings.append(f"RSI بسیار بالا است ({rsi:.1f})؛ ریسک ورود دیرهنگام وجود دارد.")
        elif rsi >= 70:
            points -= 4
            warnings.append(f"RSI وارد محدوده اشباع خرید شده است ({rsi:.1f}).")

    elif side == "SHORT":
        if rsi <= 22:
            points -= 7
            warnings.append(f"RSI بسیار پایین است ({rsi:.1f})؛ ریسک ورود دیرهنگام وجود دارد.")
        elif rsi <= 30:
            points -= 4
            warnings.append(f"RSI وارد محدوده اشباع فروش شده است ({rsi:.1f}).")

    # 2) ATR / Volatility Risk
    if atr_pct >= 0.035:
        points -= 7
        warnings.append(f"نوسان بازار بسیار بالا است؛ ATR حدود {atr_pct * 100:.2f}% قیمت است.")
    elif atr_pct >= 0.025:
        points -= 4
        warnings.append(f"نوسان بازار بالاتر از حالت عادی است؛ ATR حدود {atr_pct * 100:.2f}% قیمت است.")

    # 3) Weak Candle Risk
    if body_ratio < 0.25:
        points -= 4
        warnings.append("بدنه کندل نسبت به دامنه ضعیف است؛ احتمال عدم قطعیت یا جذب نقدینگی وجود دارد.")
    elif body_ratio < 0.40:
        points -= 2
        warnings.append("بدنه کندل متوسط/ضعیف است؛ قدرت حرکت هنوز کامل نیست.")

    # 4) Price extension from EMA10
    if close > 0 and ema_10 > 0:
        distance_from_ema = abs(close - ema_10) / close

        if distance_from_ema >= 0.025:
            points -= 5
            warnings.append(
                f"قیمت از EMA10 فاصله زیادی گرفته است ({distance_from_ema * 100:.2f}%)؛ ریسک پولبک بیشتر است."
            )
        elif distance_from_ema >= 0.015:
            points -= 2
            warnings.append(
                f"قیمت کمی از EMA10 فاصله گرفته است ({distance_from_ema * 100:.2f}%)."
            )

    # 5) Candle direction against bias
    if side == "LONG" and bearish_candle:
        points -= 5
        warnings.append("کندل فعلی با سناریوی LONG هم‌راستا نیست.")

    elif side == "SHORT" and bullish_candle:
        points -= 5
        warnings.append("کندل فعلی با سناریوی SHORT هم‌راستا نیست.")

    # 6) Volume confirmation risk
    if volume_sma > 0 and volume > 0:
        volume_ratio = volume / volume_sma

        if volume_ratio < 0.65:
            points -= 4
            warnings.append("حجم فعلی بسیار کمتر از میانگین ۲۰ کندل است؛ تأیید مشارکت ضعیف است.")
        elif volume_ratio < 0.90:
            points -= 2
            warnings.append("حجم فعلی کمتر از میانگین ۲۰ کندل است؛ تأیید حرکت کامل نیست.")

    points = max(-25, min(0, points))

    return ScoreComponent(
        name="Risk Penalty",
        points=points,
        max_points=25,
        reasons=reasons,
        warnings=warnings,
    )