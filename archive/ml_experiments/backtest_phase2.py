"""
بکتست با فیچرهای پیشرفته
"""

import joblib
import numpy as np
import pandas as pd

from config import MODEL_PATH, TRAINING_CANDLES, MIN_CONFIDENCE, LOOKAHEAD_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features_integrated import build_integrated_dataset, get_all_feature_columns

FEE_RATE = 0.001


def backtest():
    print("=" * 80)
    print("بکتست با فیچرهای پیشرفته (Advanced Features)")
    print("=" * 80)

    bundle = joblib.load(MODEL_PATH)
    model = bundle['model']
    scaler = bundle['scaler']
    feature_cols = bundle.get('feature_columns', get_all_feature_columns())
    use_advanced = bundle.get('use_advanced', False)
    train_end_timestamp = bundle.get('train_end_timestamp')

    print(f"✓ مدل بارگذاری شد")
    print(f"✓ تعداد فیچرها: {len(feature_cols)}")
    print(f"✓ فیچرهای پیشرفته: {'بله' if use_advanced else 'نه'}")

    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    dataset = build_integrated_dataset(raw, for_training=True, use_advanced=use_advanced)

    if train_end_timestamp is not None:
        before = len(dataset)
        dataset = dataset[dataset.index > train_end_timestamp]
        print(f"\n✓ فقط داده بعد از {train_end_timestamp} بررسی میشود")
        print(f"  ({before} → {len(dataset)} کندل)")

    if len(dataset) < 30:
        print("⚠️ دادهی کافی برای بکتست وجود ندارد")
        return

    X = scaler.transform(dataset[feature_cols].values)
    proba = model.predict_proba(X)
    classes = model.classes_

    dataset_copy = dataset.copy()
    for i, c in enumerate(classes):
        dataset_copy[f'proba_{c}'] = proba[:, i]

    # تشخیص سیگنال
    def decide(row):
        if row.get('proba_1', 0) >= MIN_CONFIDENCE:
            return 1
        if row.get('proba_-1', 0) >= MIN_CONFIDENCE:
            return -1
        return 0

    dataset_copy['signal'] = dataset_copy.apply(decide, axis=1)

    trades = dataset_copy[dataset_copy['signal'] != 0].copy()
    trades['strategy_return'] = trades['signal'] * trades['future_return'] - FEE_RATE

    total_trades = len(trades)
    win_rate = (trades['strategy_return'] > 0).mean() if total_trades > 0 else 0
    avg_return = trades['strategy_return'].mean() if total_trades > 0 else 0
    cumulative = (1 + trades['strategy_return']).prod() - 1 if total_trades > 0 else 0

    print("\n" + "=" * 80)
    print("📊 نتایج بکتست")
    print("=" * 80)
    print(f"کندلهای بررسی‌شده: {len(dataset_copy)}")
    print(f"سیگنالها: {total_trades}")
    print(f"Win Rate: {win_rate * 100:.2f}%")
    print(f"میانگین بازده: {avg_return * 100:.3f}%")
    print(f"بازده تجمعی: {cumulative * 100:.2f}%")

    if cumulative > 0:
        print("\n✅ نتیجهی مثبت!")
    else:
        print("\n⚠️ نتیجهی منفی - بهتر است فیچرها یا پارامترها را بررسی کنی")


if __name__ == '__main__':
    backtest()
