"""
دریافت داده‌ی بازار فیوچرز بایننس (بدون نیاز به API Key).
"""

import time
import requests
import pandas as pd

BASE_URL = "https://fapi.binance.com"


def _get(path: str, params: dict) -> list:
    url = BASE_URL + path
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_funding_rate_history(symbol: str = "BTCUSDT", start_time_ms: int = None,
                                end_time_ms: int = None, limit: int = 1000) -> pd.DataFrame:
    all_rows = []
    params = {"symbol": symbol, "limit": limit}
    if start_time_ms:
        params["startTime"] = start_time_ms
    if end_time_ms:
        params["endTime"] = end_time_ms

    while True:
        batch = _get("/fapi/v1/fundingRate", params)
        if not batch:
            break
        all_rows.extend(batch)
        last_time = batch[-1]["fundingTime"]
        if len(batch) < limit:
            break
        params["startTime"] = last_time + 1
        time.sleep(0.2)

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["fundingTime"], unit="ms")
    df["funding_rate"] = df["fundingRate"].astype(float)
    df = df[["timestamp", "funding_rate"]].set_index("timestamp").sort_index()
    return df


def fetch_open_interest_history(symbol: str = "BTCUSDT", period: str = "1h",
                                 limit: int = 500) -> pd.DataFrame:
    params = {"symbol": symbol, "period": period, "limit": limit}
    data = _get("/futures/data/openInterestHist", params)
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["open_interest"] = df["sumOpenInterest"].astype(float)
    df["open_interest_value"] = df["sumOpenInterestValue"].astype(float)
    df = df[["timestamp", "open_interest", "open_interest_value"]].set_index("timestamp").sort_index()
    return df


def fetch_long_short_ratio_history(symbol: str = "BTCUSDT", period: str = "1h",
                                    limit: int = 500) -> pd.DataFrame:
    params = {"symbol": symbol, "period": period, "limit": limit}
    data = _get("/futures/data/globalLongShortAccountRatio", params)
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["long_short_ratio"] = df["longShortRatio"].astype(float)
    df["long_account_pct"] = df["longAccount"].astype(float)
    df["short_account_pct"] = df["shortAccount"].astype(float)
    df = df[["timestamp", "long_short_ratio", "long_account_pct", "short_account_pct"]]
    df = df.set_index("timestamp").sort_index()
    return df


if __name__ == "__main__":
    print("تست دریافت Funding Rate (چند ردیف آخر):")
    fr = fetch_funding_rate_history(limit=10)
    print(fr.tail())

    print("\nتست دریافت Open Interest (چند ردیف آخر):")
    oi = fetch_open_interest_history(limit=10)
    print(oi.tail())

    print("\nتست دریافت Long/Short Ratio (چند ردیف آخر):")
    ls = fetch_long_short_ratio_history(limit=10)
    print(ls.tail())