"""
بکتست مدل Ensemble
"""

import joblib
import numpy as np
import pandas as pd

from config import TRAINING_CANDLES, MIN_CONFIDENCE, LOOKAHEAD_CANDLES, MODEL_PATH
from data_fetcher import fetch_ohlcv_extended
from features_integrated import build_integrated_dataset

FEE_RATE = 0.001


def backtest_ensemble():
    """بکتست مدل Ensemble"""
    
    print("=" * 80)
    print("📊 بکتست Ensemble مدل")
    print("=" * 80)
    
    # بارگذاری مدل Ensemble
    ensemble_model_path = MODEL_PATH.replace('.joblib', '_ensemble.joblib')
    try:
        bundle = joblib.load(ensemble_model_path)
        print(f"✅ مدل Ensemble بارگذاری شد: {ensemble_model_path}")
    except FileNotFoundError:
        print(f"❌ مدل یافت نشد: {ensemble_model_path}")
        print("ابتدا train_ensemble_phase3.py را اجرا کن")
        return
    
    ensemble = bundle['ensemble']
    selector = bundle['feature_selector']
    selected_features = bundle['selected_features']
    feature_indices = bundle['feature_indices']
    train_end_timestamp = bundle.get('train_end_timestamp')
    
    print(f"✓ تعداد فیچرهای انتخاب‌شده: {len(selected_features)}")
    
    # دریافت داده
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    dataset = build_integrated_dataset(raw, for_training=True, use_advanced=True)
    
    if train_end_timestamp is not None:
        dataset = dataset[dataset.index > train_end_timestamp]
        print(f"✓ فقط داده بعد از {train_end_timestamp}")
    
    if len(dataset) < 30:
        print("⚠️ دادهی کافی برای بکتست وجود ندارد")
        return
    
    # پیشبینی
    all_features = bundle['all_features']
    X = dataset[all_features].values
    X_selected = X[:, feature_indices]
    
    proba = ensemble.predict_proba(X_selected)
    dataset_copy = dataset.copy()
    
    # برای Ensemble multiclass
    # پیشفرض: کلاس ۰ (neutral)، ۱ (buy)، ۲ (sell)
    # یا -1، 0، 1 (حسب نوع encoding)
    
    classes = ensemble.ensemble.classes_
    print(f"✓ کلاسهای مدل: {classes}")
    
    for i, c in enumerate(classes):
        dataset_copy[f'proba_{c}'] = proba[:, i]
    
    # تشخیص سیگنال
    def decide(row):
        if len(classes) == 3:  # -1, 0, 1
            proba_up = row.get('proba_1', 0)
            proba_down = row.get('proba_-1', 0)
        else:
            # فرض کن ترتیب مختلف باشد
            proba_up = max([row.get(f'proba_{c}', 0) for c in classes if c > 0])
            proba_down = max([row.get(f'proba_{c}', 0) for c in classes if c < 0])
        
        if proba_up >= MIN_CONFIDENCE:
            return 1
        if proba_down >= MIN_CONFIDENCE:
            return -1
        return 0
    
    dataset_copy['signal'] = dataset_copy.apply(decide, axis=1)
    
    # محاسبهی معاملات
    trades = dataset_copy[dataset_copy['signal'] != 0].copy()
    trades['strategy_return'] = trades['signal'] * trades['future_return'] - FEE_RATE
    
    total_trades = len(trades)
    win_rate = (trades['strategy_return'] > 0).mean() if total_trades > 0 else 0
    avg_return = trades['strategy_return'].mean() if total_trades > 0 else 0
    cumulative = (1 + trades['strategy_return']).prod() - 1 if total_trades > 0 else 0
    
    print("\n" + "=" * 80)
    print("📈 نتایج بکتست")
    print("=" * 80)
    print(f"کندلهای بررسی‌شده: {len(dataset_copy)}")
    print(f"سیگنالها: {total_trades}")
    print(f"Win Rate: {win_rate * 100:.2f}%")
    print(f"میانگین بازده: {avg_return * 100:.3f}%")
    print(f"بازده تجمعی: {cumulative * 100:.2f}%")
    
    if cumulative > 0:
        print("\n✅ نتیجهی مثبت!")
    else:
        print("\n⚠️ نتیجهی منفی")


if __name__ == '__main__':
    backtest_ensemble()
