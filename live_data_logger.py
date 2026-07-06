"""
ثبت زنده‌ی داده‌هایی که آرشیو تاریخی رایگان طولانی ندارند:
Open Interest، Long/Short Ratio، و امتیاز احساسات اخبار.

چرا این فایل لازم است؟
بایننس فقط ~۳۰ روز تاریخچه‌ی OI و Long/Short را رایگان می‌دهد، و آرشیو
تاریخی معتبر رایگان برای اخبار عملاً وجود ندارد. پس نمی‌توانیم این‌ها را
مثل قیمت/Funding Rate چند سال به عقب بک‌تست کنیم. راه‌حل: از همین امروز
هر بار که این اسکریپت اجرا می‌شود (پیشنهاد: هر ساعت، هماهنگ با CHECK_INTERVAL_MINUTES)
یک ردیف جدید ثبت می‌کند. بعد از گذشت چند هفته/ماه، این تاریخچه‌ی جمع‌شده
با اسکریپت‌های تحلیلی (مثل edge_diagnostic.py) قابل تست آماری واقعی می‌شود.

اجرا (پیشنهاد: با schedule یا cron هر ساعت):
    python live_data_logger.py
"""

import os
from datetime import datetime, timezone

import pandas as pd

from futures_data_fetcher import fetch_open_interest_history, fetch_long_short_ratio_history
from news_sentiment import get_current_sentiment

LOG_PATH = "live_enriched_data_log.csv"


def log_current_snapshot():
    now = datetime.now(timezone.utc)
    row = {"logged_at": now}

    try:
        oi = fetch_open_interest_history(limit=1)
        if not oi.empty:
            row["open_interest"] = oi["open_interest"].iloc[-1]
            row["open_interest_value"] = oi["open_interest_value"].iloc[-1]
    except Exception as e:
        print(f"خطا در دریافت Open Interest: {e}")

    try:
        ls = fetch_long_short_ratio_history(limit=1)
        if not ls.empty:
            row["long_short_ratio"] = ls["long_short_ratio"].iloc[-1]
            row["long_account_pct"] = ls["long_account_pct"].iloc[-1]
    except Exception as e:
        print(f"خطا در دریافت Long/Short Ratio: {e}")

    try:
        sentiment = get_current_sentiment()
        row["news_sentiment_score"] = sentiment["score"]
        row["news_sentiment_summary"] = sentiment["summary"]
    except Exception as e:
        print(f"خطا در دریافت احساسات اخبار: {e}")

    df_new = pd.DataFrame([row])

    if os.path.exists(LOG_PATH):
        df_old = pd.read_csv(LOG_PATH, parse_dates=["logged_at"], encoding="utf-8-sig")
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(LOG_PATH, index=False, encoding="utf-8-sig")
    print(f"[{now}] یک ردیف جدید ثبت شد. مجموع ردیف‌های تاریخچه تا الان: {len(df_all)}")
    return row


if __name__ == "__main__":
    log_current_snapshot()