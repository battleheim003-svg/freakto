from .common import ScoreComponent, safe_float


def _safe_mean(series):
    try:
        return float(series.dropna().mean())
    except Exception:
        return 0.0


def _safe_median(series):
    try:
        return float(series.dropna().median())
    except Exception:
        return 0.0


def _safe_max(series):
    try:
        return float(series.dropna().max())
    except Exception:
        return 0.0


def score_volume(row, recent_df, side: str) -> ScoreComponent:
    """
    Volume Engine v2

    امتیاز کل: 20

    بررسی می‌کند:
    - حجم فعلی نسبت به میانگین
    - حجم فعلی نسبت به کندل قبل
    - تأیید حجم برای کندل هم‌جهت
    - Breakout volume
    - ضعف حجم در حرکت قیمت
    - Climax volume
    """

    points = 0
    reasons = []
    warnings = []

    current_volume = safe_float(row.get("volume"), 0.0) or 0.0
    current_close = safe_float(row.get("close"), 0.0) or 0.0
    current_open = safe_float(row.get("open"), 0.0) or 0.0
    current_high = safe_float(row.get("high"), 0.0) or 0.0
    current_low = safe_float(row.get("low"), 0.0) or 0.0

    if recent_df is None or len(recent_df) < 25:
        return ScoreComponent(
            name="Volume",
            points=0,
            max_points=20,
            reasons=[],
            warnings=["داده کافی برای تحلیل حجم وجود ندارد."],
        )

    recent_volume = recent_df["volume"].tail(30)
    previous_volume = safe_float(recent_df.iloc[-2].get("volume"), 0.0) or 0.0

    avg_volume = _safe_mean(recent_volume)
    median_volume = _safe_median(recent_volume)
    max_volume = _safe_max(recent_volume)

    if avg_volume <= 0 or current_volume <= 0:
        return ScoreComponent(
            name="Volume",
            points=0,
            max_points=20,
            reasons=[],
            warnings=["حجم معتبر برای تحلیل وجود ندارد."],
        )

    volume_vs_avg = current_volume / avg_volume
    volume_vs_median = current_volume / median_volume if median_volume > 0 else 0
    volume_vs_prev = current_volume / previous_volume if previous_volume > 0 else 0

    candle_body = abs(current_close - current_open)
    candle_range = current_high - current_low
    body_ratio = candle_body / candle_range if candle_range > 0 else 0

    bullish_candle = current_close > current_open
    bearish_candle = current_close < current_open

    is_directional_candle = (
        (side == "LONG" and bullish_candle)
        or (side == "SHORT" and bearish_candle)
    )

    # 1) حجم نسبت به میانگین
    if volume_vs_avg >= 2.0:
        points += 7
        reasons.append(
            f"حجم فعلی بسیار بالاتر از میانگین اخیر است: {volume_vs_avg:.1f}x"
        )
    elif volume_vs_avg >= 1.35:
        points += 5
        reasons.append(
            f"حجم فعلی بالاتر از میانگین اخیر است: {volume_vs_avg:.1f}x"
        )
    elif volume_vs_avg >= 1.0:
        points += 3
        reasons.append("حجم فعلی حداقل هم‌سطح میانگین اخیر است.")
    else:
        warnings.append(
            "حجم فعلی ضعیف‌تر از میانگین اخیر است؛ احتمال شکست فیک بیشتر می‌شود."
        )

    # 2) رشد حجم نسبت به کندل قبل
    if volume_vs_prev >= 1.8:
        points += 4
        reasons.append(
            f"حجم نسبت به کندل قبل جهش قابل‌توجهی دارد: {volume_vs_prev:.1f}x"
        )
    elif volume_vs_prev >= 1.25:
        points += 2
        reasons.append(
            f"حجم نسبت به کندل قبل افزایش دارد: {volume_vs_prev:.1f}x"
        )

    # 3) کندل جهت‌دار همراه با حجم
    if is_directional_candle and body_ratio >= 0.55 and volume_vs_avg >= 1.0:
        points += 4
        reasons.append("کندل فعلی جهت‌دار است و با حجم قابل قبول همراه شده است.")
    elif is_directional_candle and body_ratio >= 0.45 and volume_vs_avg < 1.0:
        warnings.append("کندل هم‌جهت است اما حجم برای تأیید حرکت کافی نیست.")

    # 4) Breakout volume confirmation
    recent_high = safe_float(recent_df["high"].tail(20).max(), 0.0) or 0.0
    recent_low = safe_float(recent_df["low"].tail(20).min(), 0.0) or 0.0

    if side == "LONG" and current_close >= recent_high and volume_vs_avg >= 1.2:
        points += 3
        reasons.append("شکست سقف اخیر با حجم بهتر از میانگین همراه شده است.")

    elif side == "LONG" and current_close >= recent_high and volume_vs_avg < 1.0:
        warnings.append("قیمت سقف اخیر را لمس/شکسته اما حجم شکست ضعیف است.")

    if side == "SHORT" and current_close <= recent_low and volume_vs_avg >= 1.2:
        points += 3
        reasons.append("شکست کف اخیر با حجم بهتر از میانگین همراه شده است.")

    elif side == "SHORT" and current_close <= recent_low and volume_vs_avg < 1.0:
        warnings.append("قیمت کف اخیر را لمس/شکسته اما حجم شکست ضعیف است.")

    # 5) Climax volume warning
    if max_volume > 0 and current_volume >= max_volume * 0.95 and body_ratio < 0.35:
        warnings.append(
            "حجم بسیار بالا همراه با بدنه ضعیف دیده می‌شود؛ احتمال جذب نقدینگی یا خستگی حرکت وجود دارد."
        )

    # 6) حرکت کم با حجم پایین
    if volume_vs_avg < 0.75 and body_ratio < 0.35:
        warnings.append("هم حجم پایین است و هم بدنه کندل ضعیف؛ بازار هنوز مشارکت جدی ندارد.")

    points = max(0, min(20, points))

    return ScoreComponent(
        name="Volume",
        points=points,
        max_points=20,
        reasons=reasons,
        warnings=warnings,
    )