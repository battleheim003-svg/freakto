"""
دریافت داده از Coinalyze API (رایگان، نیاز به کلید API رایگان از coinalyze.net).

برخلاف endpoint های رایگان بایننس که فقط ~۳۰ روز تاریخچه‌ی OI/Long-Short می‌دهند،
Coinalyze برای تایم‌فریم‌های intraday (تا ۱۲ ساعت) حدود ۱۵۰۰-۲۰۰۰ کندل نگه می‌دارد.
برای تایم‌فریم ۴ساعته یعنی تقریباً ۸ تا ۱۱ ماه تاریخچه - بسیار بیشتر از بایننس.

ثبت‌نام رایگان: https://coinalyze.net
گرفتن کلید API: https://coinalyze.net/account/api-key/
"""

import time
from datetime import datetime, timezone

import requests
import pandas as pd

from config import COINALYZE_API_KEY, SYMBOL, TIMEFRAME

BASE_URL = "https://api.coinalyze.net/v1"

# نگاشت TIMEFRAME پروژه به فرمت مورد قبول Coinalyze
TIMEFRAME_MAP = {
    "1m": "1min", "5m": "5min", "15m": "15min", "30m": "30min",
    "1h": "1hour", "2h": "2hour", "4h": "4hour", "6h": "6hour",
    "12h": "12hour", "1d": "daily",
}


def _get(endpoint: str, params: dict) -> list:
    params = dict(params)
    params["api_key"] = COINALYZE_API_KEY
    resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=20)
    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", "5"))
        print(f"محدودیت نرخ درخواست - {retry_after} ثانیه صبر می‌کنیم...")
        time.sleep(retry_after)
        resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def find_binance_perp_symbol(base_asset: str = "BTC", quote_asset: str = "USDT") -> str:
    """
    پیدا کردن کد نماد صحیح برای BTCUSDT پرپچوال روی بایننس در فرمت Coinalyze
    (مثلاً "BTCUSDT_PERP.A"). چون کد اختصاصی صرافی ممکن است تغییر کند، این تابع
    به‌جای هاردکد کردن، خودش از API استعلام می‌گیرد.
    """
    markets = _get("future-markets", {})
    for m in markets:
        if (m.get("base_asset") == base_asset and m.get("quote_asset") == quote_asset
                and m.get("is_perpetual") and "binance" in m.get("exchange", "").lower()):
            return m["symbol"]
    raise ValueError(f"نماد پرپچوال {base_asset}{quote_asset} برای بایننس در Coinalyze پیدا نشد.")


def _history_to_df(raw: list, value_keys: dict) -> pd.DataFrame:
    """
    تبدیل خروجی خام Coinalyze (لیست کندل با کلیدهای کوتاه مثل t, o, h, l, c)
    به یک DataFrame با index زمانی. value_keys نگاشت کلید خام به اسم ستون است.
    """
    if not raw or not raw[0].get("history"):
        return pd.DataFrame()

    history = raw[0]["history"]
    df = pd.DataFrame(history)
    df["timestamp"] = pd.to_datetime(df["t"], unit="s", utc=True)
    df = df.set_index("timestamp").sort_index()
    df = df.rename(columns=value_keys)
    return df[list(value_keys.values())]


def fetch_oi_history_coinalyze(days_back: int = 300, symbol: str = None) -> pd.DataFrame:
    symbol = symbol or find_binance_perp_symbol()
    interval = TIMEFRAME_MAP.get(TIMEFRAME, "4hour")
    to_ts = int(datetime.now(timezone.utc).timestamp())
    from_ts = to_ts - days_back * 86400

    raw = _get("open-interest-history", {
        "symbols": symbol, "interval": interval, "from": from_ts, "to": to_ts,
    })
    df = _history_to_df(raw, {"c": "open_interest"})  # از قیمت پایانی هر کندل OI استفاده می‌کنیم
    return df


def fetch_long_short_ratio_history_coinalyze(days_back: int = 300, symbol: str = None) -> pd.DataFrame:
    symbol = symbol or find_binance_perp_symbol()
    interval = TIMEFRAME_MAP.get(TIMEFRAME, "4hour")
    to_ts = int(datetime.now(timezone.utc).timestamp())
    from_ts = to_ts - days_back * 86400

    raw = _get("long-short-ratio-history", {
        "symbols": symbol, "interval": interval, "from": from_ts, "to": to_ts,
    })
    df = _history_to_df(raw, {"r": "long_short_ratio"})
    return df


def fetch_funding_rate_history_coinalyze(days_back: int = 300, symbol: str = None) -> pd.DataFrame:
    symbol = symbol or find_binance_perp_symbol()
    interval = TIMEFRAME_MAP.get(TIMEFRAME, "4hour")
    to_ts = int(datetime.now(timezone.utc).timestamp())
    from_ts = to_ts - days_back * 86400

    raw = _get("funding-rate-history", {
        "symbols": symbol, "interval": interval, "from": from_ts, "to": to_ts,
    })
    df = _history_to_df(raw, {"c": "funding_rate"})
    return df


def fetch_liquidation_history_coinalyze(days_back: int = 300, symbol: str = None) -> pd.DataFrame:
    """مجموع لیکوییدشدن‌ها - می‌تواند نشانه‌ی نقاط پرفشار بازار باشد (فیچر جدید و جالب)."""
    symbol = symbol or find_binance_perp_symbol()
    interval = TIMEFRAME_MAP.get(TIMEFRAME, "4hour")
    to_ts = int(datetime.now(timezone.utc).timestamp())
    from_ts = to_ts - days_back * 86400

    raw = _get("liquidation-history", {
        "symbols": symbol, "interval": interval, "from": from_ts, "to": to_ts,
    })
    df = _history_to_df(raw, {"l": "liquidations_long", "s": "liquidations_short"})
    return df


if __name__ == "__main__":
    symbol = find_binance_perp_symbol()
    print(f"نماد پیدا‌شده برای BTCUSDT پرپچوال بایننس در Coinalyze: {symbol}\n")

    print("در حال دریافت تاریخچه‌ی Open Interest...")
    oi = fetch_oi_history_coinalyze()
    print(f"تعداد رکورد: {len(oi)}" + (f" | از {oi.index[0]} تا {oi.index[-1]}" if not oi.empty else ""))

    print("\nدر حال دریافت تاریخچه‌ی Long/Short Ratio...")
    ls = fetch_long_short_ratio_history_coinalyze()
    print(f"تعداد رکورد: {len(ls)}" + (f" | از {ls.index[0]} تا {ls.index[-1]}" if not ls.empty else ""))

    print("\nدر حال دریافت تاریخچه‌ی لیکوییدشدن‌ها...")
    liq = fetch_liquidation_history_coinalyze()
    print(f"تعداد رکورد: {len(liq)}" + (f" | از {liq.index[0]} تا {liq.index[-1]}" if not liq.empty else ""))
