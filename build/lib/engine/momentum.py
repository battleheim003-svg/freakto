from .common import ScoreComponent, safe_float


def _price_momentum(row):
    close = safe_float(row.get("close"), 0.0) or 0.0
    open_ = safe_float(row.get("open"), 0.0) or 0.0
    high = safe_float(row.get("high"), 0.0) or 0.0
    low = safe_float(row.get("low"), 0.0) or 0.0

    candle_range = high - low
    candle_body = abs(close - open_)
    body_ratio = candle_body / candle_range if candle_range > 0 else 0.0

    return close, open_, body_ratio


def score_momentum(prev_row, row, side: str) -> ScoreComponent:
    """
    Momentum Engine v2

    امتیاز کل: 30

    بررسی می‌کند:
    - RSI سالم / داغ / ضعیف
    - جهت تغییر RSI نسبت به کندل قبل
    - MACD مثبت/منفی
    - تغییر MACD نسبت به کندل قبل
    - جهت کندل فعلی
    - قدرت بدنه کندل
    - فاصله قیمت نسبت به EMA10
    """

    points = 0
    reasons = []
    warnings = []

    rsi = safe_float(row.get("rsi_14"), 50.0) or 50.0
    prev_rsi = safe_float(prev_row.get("rsi_14"), 50.0) or 50.0

    macd = safe_float(row.get("macd_diff"), 0.0) or 0.0
    prev_macd = safe_float(prev_row.get("macd_diff"), 0.0) or 0.0

    ema_10 = safe_float(row.get("ema_10"), 0.0) or 0.0
    close, open_, body_ratio = _price_momentum(row)

    bullish_candle = close > open_
    bearish_candle = close < open_

    rsi_change = rsi - prev_rsi
    macd_change = macd - prev_macd

    if side == "LONG":
        # RSI condition
        if 50 <= rsi <= 65:
            points += 8
            reasons.append(f"RSI در محدوده سالم مومنتوم صعودی است: {rsi:.1f}")
        elif 65 < rsi <= 72:
            points += 5
            reasons.append(f"RSI صعودی است ولی کمی داغ شده: {rsi:.1f}")
            warnings.append("RSI بالاست؛ احتمال پولبک کوتاه‌مدت وجود دارد.")
        elif 45 <= rsi < 50:
            points += 2
            warnings.append(f"RSI هنوز کاملاً صعودی نیست: {rsi:.1f}")
        elif rsi > 72:
            points += 2
            warnings.append(f"RSI بیش از حد داغ است: {rsi:.1f}")
        else:
            warnings.append(f"RSI مومنتوم صعودی را تأیید نمی‌کند: {rsi:.1f}")

        # RSI slope
        if rsi_change >= 3:
            points += 3
            reasons.append(f"RSI نسبت به کندل قبل با قدرت افزایش یافته است: +{rsi_change:.1f}")
        elif rsi_change > 0:
            points += 1
            reasons.append(f"RSI نسبت به کندل قبل کمی افزایش یافته است: +{rsi_change:.1f}")
        elif rsi_change <= -4:
            warnings.append(f"RSI نسبت به کندل قبل افت قابل توجهی داشته است: {rsi_change:.1f}")

        # MACD condition
        if macd > 0:
            points += 6
            reasons.append("MACD در ناحیه مثبت است.")
        else:
            warnings.append("MACD هنوز ناحیه مثبت را تأیید نکرده است.")

        # MACD slope
        if macd_change > 0:
            points += 3
            reasons.append("MACD نسبت به کندل قبل در حال بهبود است.")
        elif macd_change < 0:
            warnings.append("MACD نسبت به کندل قبل ضعیف‌تر شده است.")

        # Candle direction and body
        if bullish_candle:
            points += 4
            reasons.append("کندل فعلی مثبت بسته شده است.")

            if body_ratio >= 0.60:
                points += 3
                reasons.append("بدنه کندل قوی است و فشار خرید واضح‌تر دیده می‌شود.")
            elif body_ratio >= 0.40:
                points += 1
                reasons.append("بدنه کندل قابل قبول است.")
            else:
                warnings.append("کندل مثبت است اما بدنه آن ضعیف است.")
        elif bearish_candle:
            warnings.append("کندل فعلی با سناریوی LONG هم‌راستا نیست.")

        # EMA10 relationship
        if close > ema_10 > 0:
            points += 3
            reasons.append("قیمت بالای EMA10 است؛ مومنتوم کوتاه‌مدت هنوز حفظ شده است.")
        else:
            warnings.append("قیمت زیر EMA10 است؛ مومنتوم کوتاه‌مدت ضعیف‌تر شده است.")

    elif side == "SHORT":
        # RSI condition
        if 35 <= rsi <= 50:
            points += 8
            reasons.append(f"RSI در محدوده سالم مومنتوم نزولی است: {rsi:.1f}")
        elif 28 <= rsi < 35:
            points += 5
            reasons.append(f"RSI نزولی است ولی کمی بیش‌فروش شده: {rsi:.1f}")
            warnings.append("RSI پایین است؛ احتمال پولبک کوتاه‌مدت وجود دارد.")
        elif 50 < rsi <= 55:
            points += 2
            warnings.append(f"RSI هنوز کاملاً نزولی نیست: {rsi:.1f}")
        elif rsi < 28:
            points += 2
            warnings.append(f"RSI بیش از حد پایین است: {rsi:.1f}")
        else:
            warnings.append(f"RSI مومنتوم نزولی را تأیید نمی‌کند: {rsi:.1f}")

        # RSI slope
        if rsi_change <= -3:
            points += 3
            reasons.append(f"RSI نسبت به کندل قبل با قدرت کاهش یافته است: {rsi_change:.1f}")
        elif rsi_change < 0:
            points += 1
            reasons.append(f"RSI نسبت به کندل قبل کمی کاهش یافته است: {rsi_change:.1f}")
        elif rsi_change >= 4:
            warnings.append(f"RSI نسبت به کندل قبل افزایش قابل توجهی داشته است: +{rsi_change:.1f}")

        # MACD condition
        if macd < 0:
            points += 6
            reasons.append("MACD در ناحیه منفی است.")
        else:
            warnings.append("MACD هنوز ناحیه منفی را تأیید نکرده است.")

        # MACD slope
        if macd_change < 0:
            points += 3
            reasons.append("MACD نسبت به کندل قبل در حال تضعیف است.")
        elif macd_change > 0:
            warnings.append("MACD نسبت به کندل قبل بهتر شده و فشار فروش ضعیف‌تر است.")

        # Candle direction and body
        if bearish_candle:
            points += 4
            reasons.append("کندل فعلی منفی بسته شده است.")

            if body_ratio >= 0.60:
                points += 3
                reasons.append("بدنه کندل قوی است و فشار فروش واضح‌تر دیده می‌شود.")
            elif body_ratio >= 0.40:
                points += 1
                reasons.append("بدنه کندل قابل قبول است.")
            else:
                warnings.append("کندل منفی است اما بدنه آن ضعیف است.")
        elif bullish_candle:
            warnings.append("کندل فعلی با سناریوی SHORT هم‌راستا نیست.")

        # EMA10 relationship
        if close < ema_10 and ema_10 > 0:
            points += 3
            reasons.append("قیمت زیر EMA10 است؛ مومنتوم نزولی کوتاه‌مدت هنوز حفظ شده است.")
        else:
            warnings.append("قیمت بالای EMA10 است؛ مومنتوم نزولی کوتاه‌مدت ضعیف‌تر شده است.")

    points = max(0, min(30, points))

    return ScoreComponent(
        name="Momentum",
        points=points,
        max_points=30,
        reasons=reasons,
        warnings=warnings,
    )