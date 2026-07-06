"""
آموزش مدل طبقه‌بندی (Classification) برای پیش‌بینی جهت قیمت.
خروجی: یک فایل model.joblib که بعداً برای پیش‌بینی زنده استفاده می‌شود.

نکته‌ی مهم: داده‌های مالی سری زمانی هستند، پس shuffle کردن داده‌ها هنگام
تقسیم train/test اشتباه است. ما تقسیم را بر اساس زمان انجام می‌دهیم.
"""

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler

from config import MODEL_PATH, TRAINING_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import build_dataset, FEATURE_COLUMNS


def train():
    print(f"در حال دریافت {TRAINING_CANDLES} کندل تاریخی (ممکن است کمی طول بکشد)...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    print(f"دریافت کامل شد: {len(raw)} کندل از {raw.index[0]} تا {raw.index[-1]}")

    print("در حال ساخت فیچرها و لیبل‌ها...")
    dataset = build_dataset(raw, for_training=True)

    X = dataset[FEATURE_COLUMNS].values
    y = dataset["label"].values

    # تقسیم زمانی: 80٪ اول برای آموزش، 20٪ آخر برای تست
    split_idx = int(len(dataset) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("در حال آموزش مدل...")
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=20,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)

    print("\n--- نتیجه روی داده تست (out-of-sample) ---")
    y_pred = model.predict(X_test_scaled)
    print(classification_report(y_test, y_pred, zero_division=0))

    # زمان آخرین کندل آموزشی را ذخیره می‌کنیم تا backtest.py فقط روی
    # داده‌ی واقعاً دیده‌نشده (بعد از این زمان) تست انجام دهد، نه روی
    # داده‌هایی که مدل از قبل دیده (که نتیجه را به‌طور کاذب خوب نشان می‌دهد).
    train_end_timestamp = dataset.index[split_idx - 1]

    joblib.dump(
        {"model": model, "scaler": scaler, "train_end_timestamp": train_end_timestamp},
        MODEL_PATH,
    )
    print(f"\nمدل ذخیره شد در: {MODEL_PATH}")
    print(f"مرز آموزش/تست: {train_end_timestamp} (بک‌تست فقط بعد از این زمان را بررسی می‌کند)")


if __name__ == "__main__":
    train()