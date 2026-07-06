"""
main.py - Live Trading با Paper Trading (WunderTrading)
اجرا: python main.py
"""

import time
import schedule
import joblib
import pandas as pd
from datetime import datetime

from config import (
    MODEL_PATH, SYMBOL, TIMEFRAME, MIN_CONFIDENCE, 
    CHECK_INTERVAL_MINUTES, PAPER_TRADING_SOURCE, PAPER_TRADING_ENABLED,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, EXCHANGE_ID
)
from data_fetcher import fetch_ohlcv
from features import build_dataset, FEATURE_COLUMNS
from paper_trader import PaperTrader

try:
    from telegram_notifier import send_telegram_message
    HAS_TELEGRAM = True
except:
    HAS_TELEGRAM = False
    print("⚠️ Telegram notifier یافت نشد")

_last_signal_timestamp = None
_trader = None


def check_and_signal():
    """بررسی سیگنال و ارسال اطلاع"""
    global _last_signal_timestamp, _trader

    try:
        bundle = joblib.load(MODEL_PATH)
    except FileNotFoundError:
        print("❌ مدل پیدا نشد! ابتدا python model_train_final_Version2.py را اجرا کن")
        return

    model = bundle["model"]
    scaler = bundle["scaler"]
    feature_cols = bundle.get("feature_columns", FEATURE_COLUMNS)

    try:
        raw = fetch_ohlcv(limit=200)
    except Exception as e:
        print(f"❌ خطا در دریافت داده: {e}")
        return

    dataset = build_dataset(raw, for_training=False)

    if dataset.empty:
        print("⚠️ داده کافی برای محاسبه فیچرها وجود ندارد")
        return

    latest = dataset.iloc[[-1]]
    latest_timestamp = latest.index[-1]

    if latest_timestamp == _last_signal_timestamp:
        return

    X = scaler.transform(latest[feature_cols].values)
    proba = model.predict_proba(X)[0]
    classes = model.classes_

    proba_dict = dict(zip(classes, proba))
    price = latest["close"].values[0]

    signal = None
    confidence = 0.0
    
    if proba_dict.get(1, 0) >= MIN_CONFIDENCE:
        signal, confidence = "خرید (BUY)", proba_dict[1]
    elif proba_dict.get(-1, 0) >= MIN_CONFIDENCE:
        signal, confidence = "فروش (SELL)", proba_dict[-1]

    print(f"[{latest_timestamp}] {SYMBOL} @ ${price:.2f} | {signal or 'No Signal'} ({confidence*100:.1f}%)")

    # Paper Trading
    if signal and PAPER_TRADING_ENABLED and _trader:
        if "خرید" in signal or "BUY" in signal:
            _trader.open_position(SYMBOL, "long", price, 0.1, latest_timestamp)
        elif "فروش" in signal or "SELL" in signal:
            _trader.close_position(SYMBOL, price, latest_timestamp)

    # Telegram
    if signal and HAS_TELEGRAM:
        message = (
            f"🔔 *سیگنال جدید*\n"
            f"صرافی: WunderTrading\n"
            f"نماد: {SYMBOL}\n"
            f"جهت: {signal}\n"
            f"اطمینان: {confidence * 100:.1f}%\n"
            f"قیمت: ${price:.2f}\n"
            f"زمان: {latest_timestamp}\n\n"
            f"⚠️ فقط برای اطلاع"
        )
        
        try:
            send_telegram_message(message)
        except Exception as e:
            print(f"⚠️ خطا در ارسال Telegram: {e}")
        
        _last_signal_timestamp = latest_timestamp


def main():
    """حلقهی اصلی"""
    global _trader
    
    if PAPER_TRADING_ENABLED:
        _trader = PaperTrader(exchange=PAPER_TRADING_SOURCE)
    
    print("=" * 70)
    print("🚀 Live Trading شروع شد (WunderTrading)")
    print("=" * 70)
    print(f"Exchange: {EXCHANGE_ID.upper()}")
    print(f"Symbol: {SYMBOL}")
    print(f"Timeframe: {TIMEFRAME}")
    print(f"Min Confidence: {MIN_CONFIDENCE}")
    print(f"Paper Trading: {'✅ فعال' if PAPER_TRADING_ENABLED else '❌ غیرفعال'}")
    print(f"Telegram: {'✅ فعال' if HAS_TELEGRAM else '❌ غیرفعال'}")
    print("=" * 70)
    print()
    
    check_and_signal()
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_and_signal)

    try:
        while True:
            schedule.run_pending()
            time.sleep(15)
    except KeyboardInterrupt:
        print("\n\n⛔ Live Trading متوقف شد")
        if _trader:
            _trader.print_stats()


if __name__ == "__main__":
    main()