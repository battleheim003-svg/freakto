"""
قوانین هشدار بازار — رویکرد صادقانه به‌جای «پیش‌بینی هوش مصنوعی»

بعد از تست آماری دقیق (AUC ~0.50 با فیچرهای تکنیکال معمولی)، مشخص شد که
این‌ها به‌تنهایی سیگنال جهت قابل‌اعتمادی برای BTC/USDT ندارند. به‌جای ادعای
دروغین «پیش‌بینی»، این ماژول فقط **شرایط قابل‌توجه و قابل‌توضیح بازار** را
تشخیص می‌دهد و گزارش می‌کند - بدون این‌که بگوید قیمت حتماً بالا یا پایین می‌رود.

هر قانون یک شرط ساده و شفاف است که هرکسی می‌تونه منطقش رو بفهمه، برخلاف
یک مدل جعبه‌سیاه که فقط یک عدد احتمال بی‌توضیح می‌داد.

مهم: این هشدارها "توصیه‌ی خرید/فروش" نیستند، فقط می‌گویند
"این اتفاق نادر/قابل‌توجه در بازار افتاده، خودت بررسی کن".
"""

import pandas as pd


def check_rsi_extreme(row, oversold=30, overbought=70):
    """RSI در منطقه‌ی اشباع خرید یا فروش"""
    rsi = row.get("rsi_14")
    if rsi is None or pd.isna(rsi):
        return None
    if rsi <= oversold:
        return {
            "name": "RSI اشباع فروش",
            "detail": f"RSI = {rsi:.1f} (زیر {oversold}) — تاریخچه‌ی نزول قیمت شدید بوده",
            "type": "neutral_info",
        }
    if rsi >= overbought:
        return {
            "name": "RSI اشباع خرید",
            "detail": f"RSI = {rsi:.1f} (بالای {overbought}) — تاریخچه‌ی صعود قیمت شدید بوده",
            "type": "neutral_info",
        }
    return None


def check_bollinger_touch(row):
    """قیمت به باند بالا/پایین بولینگر برخورد کرده"""
    close = row.get("close")
    bb_high = row.get("bb_high")
    bb_low = row.get("bb_low")
    if any(v is None or pd.isna(v) for v in [close, bb_high, bb_low]):
        return None
    if close >= bb_high:
        return {
            "name": "برخورد به باند بالای بولینگر",
            "detail": f"قیمت ({close:.2f}) به یا بالاتر از باند بالا ({bb_high:.2f}) رسیده",
            "type": "neutral_info",
        }
    if close <= bb_low:
        return {
            "name": "برخورد به باند پایین بولینگر",
            "detail": f"قیمت ({close:.2f}) به یا پایین‌تر از باند پایین ({bb_low:.2f}) رسیده",
            "type": "neutral_info",
        }
    return None


def check_macd_crossover(prev_row, row):
    """کراس‌اوور خط MACD با خط سیگنال"""
    prev_diff = prev_row.get("macd_diff")
    curr_diff = row.get("macd_diff")
    if any(v is None or pd.isna(v) for v in [prev_diff, curr_diff]):
        return None
    if prev_diff <= 0 and curr_diff > 0:
        return {
            "name": "کراس صعودی MACD",
            "detail": "خط MACD از پایین به بالای خط سیگنال عبور کرد",
            "type": "neutral_info",
        }
    if prev_diff >= 0 and curr_diff < 0:
        return {
            "name": "کراس نزولی MACD",
            "detail": "خط MACD از بالا به پایین خط سیگنال عبور کرد",
            "type": "neutral_info",
        }
    return None


def check_volume_spike(row, threshold=2.0):
    """جهش غیرعادی حجم معاملات نسبت به کندل قبل"""
    vol_change = row.get("volume_change")
    if vol_change is None or pd.isna(vol_change):
        return None
    if vol_change >= threshold:
        return {
            "name": "جهش حجم معاملات",
            "detail": f"حجم این کندل نسبت به کندل قبل {vol_change * 100:.0f}٪ بیشتر شده",
            "type": "neutral_info",
        }
    return None


def check_ma_crossover(prev_row, row):
    """کراس‌اوور میانگین متحرک کوتاه‌مدت و بلندمدت (طلایی/مرگ)"""
    prev_dist = prev_row.get("sma_10") - prev_row.get("sma_30") if not any(
        pd.isna(prev_row.get(k)) for k in ["sma_10", "sma_30"]
    ) else None
    curr_dist = row.get("sma_10") - row.get("sma_30") if not any(
        pd.isna(row.get(k)) for k in ["sma_10", "sma_30"]
    ) else None
    if prev_dist is None or curr_dist is None:
        return None
    if prev_dist <= 0 and curr_dist > 0:
        return {
            "name": "کراس طلایی (Golden Cross کوتاه‌مدت)",
            "detail": "میانگین متحرک ۱۰ از پایین به بالای میانگین متحرک ۳۰ عبور کرد",
            "type": "neutral_info",
        }
    if prev_dist >= 0 and curr_dist < 0:
        return {
            "name": "کراس مرگ (Death Cross کوتاه‌مدت)",
            "detail": "میانگین متحرک ۱۰ از بالا به پایین میانگین متحرک ۳۰ عبور کرد",
            "type": "neutral_info",
        }
    return None


def check_volatility_spike(row, threshold_multiplier=2.0, rolling_median=None):
    """نوسان (ATR) به‌طور غیرعادی بالا رفته نسبت به میانه‌ی اخیر"""
    atr_pct = row.get("atr_pct")
    if atr_pct is None or pd.isna(atr_pct) or rolling_median is None or pd.isna(rolling_median):
        return None
    if atr_pct >= rolling_median * threshold_multiplier:
        return {
            "name": "افزایش شدید نوسان بازار",
            "detail": f"ATR فعلی ({atr_pct * 100:.2f}٪) حدود {atr_pct / rolling_median:.1f} برابر میانه‌ی اخیر است",
            "type": "neutral_info",
        }
    return None


ALL_RULES_DESCRIPTION = """
قوانین فعال در این نسخه:
  1. RSI اشباع خرید/فروش (زیر 30 یا بالای 70)
  2. برخورد قیمت به باندهای بولینگر
  3. کراس‌اوور MACD
  4. جهش غیرعادی حجم معاملات (۲ برابر یا بیشتر نسبت به کندل قبل)
  5. کراس‌اوور میانگین متحرک کوتاه/بلندمدت
  6. افزایش شدید نوسان بازار (ATR) نسبت به میانه‌ی اخیر

هیچ‌کدام از این‌ها ادعای پیش‌بینی جهت آینده ندارند - فقط شرایط قابل‌توجه
و از نظر آماری قابل‌توضیح در بازار را گزارش می‌کنند.
"""


def evaluate_all_rules(prev_row, row, atr_rolling_median=None):
    """
    تمام قوانین را روی یک ردیف (کندل) بررسی می‌کند و لیست هشدارهای فعال‌شده را برمی‌گرداند.
    """
    alerts = []

    checks_without_prev = [
        check_rsi_extreme(row),
        check_bollinger_touch(row),
        check_volume_spike(row),
        check_volatility_spike(row, rolling_median=atr_rolling_median),
    ]
    for result in checks_without_prev:
        if result:
            alerts.append(result)

    if prev_row is not None:
        checks_with_prev = [
            check_macd_crossover(prev_row, row),
            check_ma_crossover(prev_row, row),
        ]
        for result in checks_with_prev:
            if result:
                alerts.append(result)

    return alerts
