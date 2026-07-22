from .common import ScoreComponent, safe_float


def _recent_swing_highs_lows(recent_df, left=2, right=2):
    swing_highs = []
    swing_lows = []

    if len(recent_df) < left + right + 5:
        return swing_highs, swing_lows

    highs = recent_df["high"].tolist()
    lows = recent_df["low"].tolist()

    for i in range(left, len(recent_df) - right):
        current_high = highs[i]
        current_low = lows[i]

        left_highs = highs[i - left:i]
        right_highs = highs[i + 1:i + right + 1]

        left_lows = lows[i - left:i]
        right_lows = lows[i + 1:i + right + 1]

        if current_high > max(left_highs) and current_high > max(right_highs):
            swing_highs.append({
                "index": i,
                "price": float(current_high),
            })

        if current_low < min(left_lows) and current_low < min(right_lows):
            swing_lows.append({
                "index": i,
                "price": float(current_low),
            })

    return swing_highs, swing_lows


def _is_higher_high(swing_highs):
    if len(swing_highs) < 2:
        return False

    return swing_highs[-1]["price"] > swing_highs[-2]["price"]


def _is_higher_low(swing_lows):
    if len(swing_lows) < 2:
        return False

    return swing_lows[-1]["price"] > swing_lows[-2]["price"]


def _is_lower_high(swing_highs):
    if len(swing_highs) < 2:
        return False

    return swing_highs[-1]["price"] < swing_highs[-2]["price"]


def _is_lower_low(swing_lows):
    if len(swing_lows) < 2:
        return False

    return swing_lows[-1]["price"] < swing_lows[-2]["price"]


def _breaks_recent_high(close, swing_highs):
    if not swing_highs:
        return False, None

    recent_high = swing_highs[-1]["price"]
    return close > recent_high, recent_high


def _breaks_recent_low(close, swing_lows):
    if not swing_lows:
        return False, None

    recent_low = swing_lows[-1]["price"]
    return close < recent_low, recent_low


def _near_level(price, level, atr_pct):
    if not price or not level or not atr_pct:
        return False

    atr_abs = price * atr_pct
    distance = abs(price - level)

    return distance <= atr_abs * 0.6


def score_structure(row, recent_df, side: str) -> ScoreComponent:
    """
    Market Structure Engine v1

    امتیاز کل: 12

    LONG:
    - Higher High
    - Higher Low
    - شکست آخرین Swing High
    - قیمت نزدیک حمایت ساختاری

    SHORT:
    - Lower High
    - Lower Low
    - شکست آخرین Swing Low
    - قیمت نزدیک مقاومت ساختاری
    """

    points = 0
    reasons = []
    warnings = []

    close = safe_float(row.get("close"))
    atr_pct = safe_float(row.get("atr_pct"), 0.0) or 0.0

    swing_highs, swing_lows = _recent_swing_highs_lows(recent_df)

    if len(swing_highs) < 2 or len(swing_lows) < 2:
        return ScoreComponent(
            name="Structure",
            points=0,
            max_points=12,
            reasons=[],
            warnings=[
                "ساختار بازار هنوز Swingهای کافی برای تحلیل قابل‌اعتماد ندارد."
            ],
        )

    hh = _is_higher_high(swing_highs)
    hl = _is_higher_low(swing_lows)
    lh = _is_lower_high(swing_highs)
    ll = _is_lower_low(swing_lows)

    broke_high, recent_high = _breaks_recent_high(close, swing_highs)
    broke_low, recent_low = _breaks_recent_low(close, swing_lows)

    last_support = swing_lows[-1]["price"]
    last_resistance = swing_highs[-1]["price"]

    if side == "LONG":
        if hh:
            points += 3
            reasons.append("ساختار Higher High دیده می‌شود؛ سقف جدید بالاتر از سقف قبلی است.")

        if hl:
            points += 3
            reasons.append("ساختار Higher Low دیده می‌شود؛ کف جدید بالاتر از کف قبلی است.")

        if broke_high:
            points += 4
            reasons.append(
                f"قیمت آخرین Swing High را شکسته است؛ شکست مقاومت ساختاری حوالی {recent_high:.2f}."
            )

        elif _near_level(close, last_support, atr_pct):
            points += 2
            reasons.append(
                f"قیمت نزدیک حمایت ساختاری حوالی {last_support:.2f} قرار دارد."
            )

        if ll:
            warnings.append("با وجود Bias لانگ، یک Lower Low اخیر دیده می‌شود؛ ساختار کاملاً تمیز نیست.")

        if lh and not broke_high:
            warnings.append("هنوز Lower High قبلی با قدرت شکسته نشده است.")

    elif side == "SHORT":
        if lh:
            points += 3
            reasons.append("ساختار Lower High دیده می‌شود؛ سقف جدید پایین‌تر از سقف قبلی است.")

        if ll:
            points += 3
            reasons.append("ساختار Lower Low دیده می‌شود؛ کف جدید پایین‌تر از کف قبلی است.")

        if broke_low:
            points += 4
            reasons.append(
                f"قیمت آخرین Swing Low را شکسته است؛ شکست حمایت ساختاری حوالی {recent_low:.2f}."
            )

        elif _near_level(close, last_resistance, atr_pct):
            points += 2
            reasons.append(
                f"قیمت نزدیک مقاومت ساختاری حوالی {last_resistance:.2f} قرار دارد."
            )

        if hh:
            warnings.append("با وجود Bias شورت، یک Higher High اخیر دیده می‌شود؛ ساختار کاملاً نزولی نیست.")

        if hl and not broke_low:
            warnings.append("هنوز Higher Low قبلی با قدرت شکسته نشده است.")

    points = max(0, min(12, points))

    return ScoreComponent(
        name="Structure",
        points=points,
        max_points=12,
        reasons=reasons,
        warnings=warnings,
    )