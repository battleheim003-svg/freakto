from dataclasses import dataclass, field
from typing import List

from .common import safe_float
from .structure import _recent_swing_highs_lows


@dataclass
class MarketRegime:
    label: str
    confidence: int
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    adjustment: int = 0


def _slope_pct(series, periods=10):
    if series is None or len(series) <= periods:
        return 0.0

    current = safe_float(series.iloc[-1], 0.0) or 0.0
    previous = safe_float(series.iloc[-periods], 0.0) or 0.0

    if previous <= 0:
        return 0.0

    return ((current - previous) / previous) * 100


def _bb_width(row):
    high = safe_float(row.get("bb_high"), 0.0) or 0.0
    low = safe_float(row.get("bb_low"), 0.0) or 0.0
    close = safe_float(row.get("close"), 0.0) or 0.0

    if close <= 0:
        return 0.0

    return ((high - low) / close) * 100


def detect_market_regime(recent_df) -> MarketRegime:
    """
    Market Regime Engine v1

    تشخیص می‌دهد بازار فعلاً بیشتر شبیه کدام حالت است:
    - TRENDING_BULL
    - TRENDING_BEAR
    - SIDEWAYS
    - VOLATILE
    - QUIET
    """

    if recent_df is None or len(recent_df) < 50:
        return MarketRegime(
            label="UNKNOWN",
            confidence=0,
            warnings=["داده کافی برای تشخیص Market Regime وجود ندارد."],
            adjustment=0,
        )

    row = recent_df.iloc[-1]

    close = safe_float(row.get("close"), 0.0) or 0.0
    atr_pct = safe_float(row.get("atr_pct"), 0.0) or 0.0
    rsi = safe_float(row.get("rsi_14"), 50.0) or 50.0

    sma_10 = safe_float(row.get("sma_10"), 0.0) or 0.0
    sma_30 = safe_float(row.get("sma_30"), 0.0) or 0.0

    atr_median = safe_float(recent_df["atr_pct"].tail(40).median(), 0.0) or 0.0
    atr_ratio = atr_pct / atr_median if atr_median > 0 else 1.0

    bb_width = _bb_width(row)
    sma30_slope = _slope_pct(recent_df["sma_30"], periods=10)

    swing_highs, swing_lows = _recent_swing_highs_lows(recent_df.tail(60))

    hh = False
    hl = False
    lh = False
    ll = False

    if len(swing_highs) >= 2:
        hh = swing_highs[-1]["price"] > swing_highs[-2]["price"]
        lh = swing_highs[-1]["price"] < swing_highs[-2]["price"]

    if len(swing_lows) >= 2:
        hl = swing_lows[-1]["price"] > swing_lows[-2]["price"]
        ll = swing_lows[-1]["price"] < swing_lows[-2]["price"]

    bull_points = 0
    bear_points = 0
    sideways_points = 0
    volatile_points = 0
    quiet_points = 0

    reasons = []
    warnings = []

    if close > sma_10 > sma_30:
        bull_points += 3
        reasons.append("قیمت بالای SMA10 و SMA30 است؛ ساختار میانگین‌ها صعودی است.")

    if close < sma_10 < sma_30:
        bear_points += 3
        reasons.append("قیمت زیر SMA10 و SMA30 است؛ ساختار میانگین‌ها نزولی است.")

    if sma30_slope > 0.4:
        bull_points += 2
        reasons.append(f"SMA30 شیب صعودی دارد: {sma30_slope:.2f}%")

    elif sma30_slope < -0.4:
        bear_points += 2
        reasons.append(f"SMA30 شیب نزولی دارد: {sma30_slope:.2f}%")

    else:
        sideways_points += 2
        reasons.append("شیب SMA30 ضعیف است؛ بازار می‌تواند وارد حالت رنج/خنثی باشد.")

    if hh and hl:
        bull_points += 3
        reasons.append("ساختار Swingها صعودی است: Higher High + Higher Low")

    if lh and ll:
        bear_points += 3
        reasons.append("ساختار Swingها نزولی است: Lower High + Lower Low")

    if not (hh and hl) and not (lh and ll):
        sideways_points += 2
        warnings.append("Swingها جهت واضح و تمیز نشان نمی‌دهند.")

    if atr_ratio >= 1.5 or atr_pct >= 0.03:
        volatile_points += 4
        warnings.append(f"نوسان بالاتر از حالت عادی است؛ ATR Ratio حدود {atr_ratio:.2f} است.")

    elif atr_ratio <= 0.75:
        quiet_points += 4
        reasons.append(f"نوسان پایین‌تر از میانگین اخیر است؛ ATR Ratio حدود {atr_ratio:.2f} است.")

    if bb_width >= 5:
        volatile_points += 2
        warnings.append(f"عرض Bollinger Bands زیاد است: {bb_width:.2f}%")

    elif bb_width <= 2:
        quiet_points += 2
        reasons.append(f"عرض Bollinger Bands کم است: {bb_width:.2f}%")

    if 45 <= rsi <= 55:
        sideways_points += 1
        reasons.append("RSI نزدیک محدوده خنثی است.")

    scores = {
        "TRENDING_BULL": bull_points,
        "TRENDING_BEAR": bear_points,
        "SIDEWAYS": sideways_points,
        "VOLATILE": volatile_points,
        "QUIET": quiet_points,
    }

    label = max(scores, key=scores.get)
    top_score = scores[label]

    confidence = min(100, int((top_score / 8) * 100))

    if top_score <= 2:
        label = "UNKNOWN"
        confidence = 25

    adjustment = 0

    if label in {"TRENDING_BULL", "TRENDING_BEAR"}:
        adjustment = 5
    elif label == "SIDEWAYS":
        adjustment = -5
    elif label == "VOLATILE":
        adjustment = -4
    elif label == "QUIET":
        adjustment = -2

    return MarketRegime(
        label=label,
        confidence=confidence,
        reasons=reasons[:5],
        warnings=warnings[:5],
        adjustment=adjustment,
    )