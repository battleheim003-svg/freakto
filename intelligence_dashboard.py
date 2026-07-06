"""
intelligence_dashboard.py

Freakto Intelligence Dashboard - v4.6.1

اجرای مستقیم لایه Intelligence برای نماد/تایم‌فریم فعلی.

Usage:
    python intelligence_dashboard.py
    python intelligence_dashboard.py --symbol BTC/USDT --timeframe 4h
    python intelligence_dashboard.py --send
"""

import argparse
from pathlib import Path
from datetime import datetime, timezone

from config import SYMBOL, TIMEFRAME
from data_fetcher import fetch_ohlcv
from features import add_features
from opportunity_engine import analyze_opportunity
from telegram_notifier import send_telegram_message
from engine.intelligence import (
    build_intelligence_report,
    format_intelligence_console,
    format_intelligence_telegram,
)

REPORT_DIR = Path("logs") / "intelligence"


def _prepare_df(symbol: str, timeframe: str, limit: int):
    raw = fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    if raw is None or raw.empty:
        raise RuntimeError(f"داده‌ای برای {symbol} | {timeframe} دریافت نشد.")

    df = add_features(raw)
    required = ["rsi_14", "bb_high", "bb_low", "macd_diff", "sma_10", "sma_30", "ema_10", "atr_pct"]
    df = df.dropna(subset=required)
    if len(df) < 35:
        raise RuntimeError("داده کافی برای ساخت Intelligence Report وجود ندارد.")
    return df


def _save_report(text: str) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = REPORT_DIR / f"intelligence_report_{stamp}.md"
    path.write_text(text, encoding="utf-8")
    return path


def run(symbol: str, timeframe: str, limit: int, send: bool = False):
    print("=" * 110)
    print("🧠 Freakto Intelligence Dashboard v4.6.1")
    print("=" * 110)
    print(f"Symbol: {symbol} | TF: {timeframe}")

    df = _prepare_df(symbol, timeframe, limit)
    opportunity = analyze_opportunity(df, symbol=symbol, timeframe=timeframe)
    report = build_intelligence_report(opportunity)
    text = format_intelligence_console(report)

    print(text)
    path = _save_report(text)
    print(f"🧠 Intelligence report ذخیره شد: {path}")

    if send:
        message = "\n".join(format_intelligence_telegram(report))
        sent = send_telegram_message(message)
        if sent:
            print("✅ پیام Intelligence ارسال شد")
        else:
            print("⚠️ پیام Intelligence ارسال نشد")

    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default=SYMBOL)
    parser.add_argument("--timeframe", default=TIMEFRAME)
    parser.add_argument("--limit", type=int, default=220)
    parser.add_argument("--send", action="store_true")
    args = parser.parse_args()

    run(args.symbol, args.timeframe, args.limit, send=args.send)


if __name__ == "__main__":
    main()
