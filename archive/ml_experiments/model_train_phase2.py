"""
آموزش مدل با فیچرهای پیشرفته

نسبت به نسخهی قدیمی:
  - از features_integrated.py استفاده میکند
  - تمام فیچرهای جدید شامل میشود
  - Feature Importance رو هم ذخیره میکند
"""

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler

from config import MODEL_PATH, TRAINING_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features_integrated import build_integrated_dataset, get_all_feature_columns


def train():
    print(f"در حال دریافت {TRAINING_CANDLES} کندل تاریخی...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    print(f"دریافت کامل: {len(raw)} کندل\n")

    print("در حال ساخت فیچرها (قدیمی + جدید)...")
    dataset = build_integrated_dataset(raw, for_training=True, use_advanced=True)
    feature_cols = get_all_feature_columns(use_advanced=True)
    
    print(f"✅ {len(feature_cols)} فیچر در کل موجود است\n")

    X = dataset[feature_cols].values
    y = dataset['label'].values

    # تقسیم زمانی: 80% آموزش، 20% تست
    split_idx = int(len(dataset) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    print(f"تقسیم داده: {len(X_train)} آموزش، {len(X_test)} تست")

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("\nدر حال آموزش مدل...")
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=20,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)

    print("\n--- نتیجه روی داده تست ---")
    y_pred = model.predict(X_test_scaled)
    print(classification_report(y_test, y_pred, zero_division=0))

    # Feature Importance
    print("\n--- ۱۰ فیچر برتر ---")
    feature_importance = dict(zip(feature_cols, model.feature_importances_))
    top_10 = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (feat, imp) in enumerate(top_10, 1):
        print(f"{i:2d}. {feat:<35} {imp:.4f}")

    train_end_timestamp = dataset.index[split_idx - 1]

    # ذخیره مدل
    model_bundle = {
        'model': model,
        'scaler': scaler,
        'feature_columns': feature_cols,
        'feature_importance': feature_importance,
        'train_end_timestamp': train_end_timestamp,
        'use_advanced': True,
    }
    
    joblib.dump(model_bundle, MODEL_PATH)
    print(f"\n✅ مدل ذخیره شد: {MODEL_PATH}")
    print(f"مرز آموزش/تست: {train_end_timestamp}")


if __name__ == '__main__':
    train()
