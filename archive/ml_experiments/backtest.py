"""
بک‌تست ساده: شبیه‌سازی می‌کند که اگر طبق سیگنال‌های مدل معامله می‌کردیم،
نتیجه چه می‌شد. این مرحله را هرگز رد نکن - قبل از استفاده‌ی واقعی حتما اینجا را اجرا کن.

محدودیت‌ها (مهم):
- این بک‌تست ساده است و کارمزد صرافی، اسپرد، و slippage را به طور کامل مدل نمی‌کند.
- نتیجه‌ی خوب در بک‌تست تضمینی برای آینده نیست (overfitting همیشه یک خطر است).
"""

import joblib
import numpy as np
import pandas as pd

from config import MODEL_PATH, TRAINING_CANDLES, MIN_CONFIDENCE, LOOKAHEAD_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import build_dataset, FEATURE_COLUMNS

FEE_RATE = 0.001  # کارمزد فرضی هر معامله (0.1٪) - برای واقعی‌تر کردن نتیجه


def backtest():
    bundle = joblib.load(MODEL_PATH)
    model, scaler = bundle["model"], bundle["scaler"]
    train_end_timestamp = bundle.get("train_end_timestamp")

    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    dataset = build_dataset(raw, for_training=True)

    if train_end_timestamp is not None:
        before = len(dataset)
        dataset = dataset[dataset.index > train_end_timestamp]
        print(f"فقط داده‌ی بعد از {train_end_timestamp} بررسی می‌شود "
              f"(از {before} کندل، {len(dataset)} کندل واقعاً دیده‌نشده باقی ماند).")
    else:
        print("هشدار: مرز آموزش/تست در مدل ذخیره نشده؛ ممکن است نتیجه شامل داده‌ی آموزشی باشد.")

    if len(dataset) < 30:
        print("داده‌ی کافی برای بک‌تست معتبر باقی نمانده. مدل را با CANDLES_LIMIT بیشتر دوباره آموزش بده "
              "یا کمی صبر کن تا کندل‌های جدید بیشتری شکل بگیرند.")
        return

    X = scaler.transform(dataset[FEATURE_COLUMNS].values)
    proba = model.predict_proba(X)
    classes = model.classes_  # مثلا [-1, 0, 1]

    dataset = dataset.copy()
    for i, c in enumerate(classes):
        dataset[f"proba_{c}"] = proba[:, i]

    # --- تشخیص: توزیع اطمینان مدل، صرف‌نظر از آستانه‌ی فعلی ---
    max_signal_proba = dataset[["proba_1", "proba_-1"]].max(axis=1) if "proba_-1" in dataset.columns else dataset["proba_1"]
    print("\n=== توزیع اطمینان مدل (تشخیصی) ===")
    print(f"میانگین بالاترین احتمال خرید/فروش: {max_signal_proba.mean():.3f}")
    print(f"میانه: {max_signal_proba.median():.3f}  |  حداکثر: {max_signal_proba.max():.3f}")
    for threshold in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65]:
        count = (max_signal_proba >= threshold).sum()
        print(f"  تعداد کندل‌هایی که اطمینان مدل >= {threshold:.2f} بود: {count}")
    print("(این بخش فقط برای تشخیص است؛ نشان می‌دهد آیا MIN_CONFIDENCE خیلی سخت‌گیرانه است یا مدل واقعاً بی‌نظر است)\n")

    # سیگنال فقط وقتی صادر می‌شود که احتمال مدل از حد آستانه بیشتر باشد
    def decide(row):
        if row.get("proba_1", 0) >= MIN_CONFIDENCE:
            return 1
        if row.get("proba_-1", 0) >= MIN_CONFIDENCE:
            return -1
        return 0

    dataset["signal"] = dataset.apply(decide, axis=1)

    # بازده واقعی بعد از LOOKAHEAD_CANDLES کندل (از قبل در future_return داریم)
    trades = dataset[dataset["signal"] != 0].copy()
    trades["strategy_return"] = trades["signal"] * trades["future_return"] - FEE_RATE

    total_trades = len(trades)
    win_rate = (trades["strategy_return"] > 0).mean() if total_trades > 0 else 0
    avg_return = trades["strategy_return"].mean() if total_trades > 0 else 0
    cumulative_return = (1 + trades["strategy_return"]).prod() - 1 if total_trades > 0 else 0

    print("=== نتیجه بک‌تست ===")
    print(f"تعداد کل کندل‌های بررسی‌شده: {len(dataset)}")
    print(f"تعداد سیگنال‌های صادرشده: {total_trades}")
    print(f"درصد برد (Win rate): {win_rate * 100:.2f}%")
    print(f"میانگین بازده هر معامله: {avg_return * 100:.3f}%")
    print(f"بازده تجمعی فرضی (compound): {cumulative_return * 100:.2f}%")
    print("\nهشدار: این نتیجه فرضی است و شامل slippage واقعی بازار نمی‌شود.")


if __name__ == "__main__":
    backtest()