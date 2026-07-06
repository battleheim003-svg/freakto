"""
تست: آیا فیچرهای جدید واقعاً AUC رو بهتر میکنند؟

این اسکریپت مقایسه میکند:
  1. مدل فقط با فیچرهای قدیمی (momentum/trend)
  2. مدل با فیچرهای قدیمی + جدید
  
اگر AUC بهتر شد (حداقل 0.02-0.03 واحد)، فیچرهای جدید ارزش دارند.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import warnings
warnings.filterwarnings('ignore')

from config import TRAINING_CANDLES, TRAIN_WINDOW_CANDLES, RETRAIN_STEP_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import build_dataset, FEATURE_COLUMNS
from features_integrated import build_integrated_dataset, get_all_feature_columns


def train_and_predict_folds(dataset: pd.DataFrame, feature_cols: list):
    """آموزش walk-forward و برگرداندن پیشبینی‌های out-of-sample"""
    n = len(dataset)
    all_preds = []
    start = TRAIN_WINDOW_CANDLES

    fold_num = 0
    while start + RETRAIN_STEP_CANDLES <= n:
        fold_num += 1
        train_slice = dataset.iloc[start - TRAIN_WINDOW_CANDLES:start]
        test_slice = dataset.iloc[start:start + RETRAIN_STEP_CANDLES].copy()

        X_train = train_slice[feature_cols].values
        y_train = train_slice['label'].values
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        model = RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=20,
            class_weight='balanced', random_state=42, n_jobs=-1,
        )
        model.fit(X_train_scaled, y_train)

        X_test = scaler.transform(test_slice[feature_cols].values)
        proba = model.predict_proba(X_test)
        classes = list(model.classes_)

        for i, c in enumerate(classes):
            test_slice[f'proba_{c}'] = proba[:, i]
        
        if 'proba_1' not in test_slice.columns:
            test_slice['proba_1'] = 0.0
        if 'proba_-1' not in test_slice.columns:
            test_slice['proba_-1'] = 0.0

        all_preds.append(test_slice[['label', 'proba_1', 'proba_-1']])
        print(f"  ✓ Fold {fold_num}")
        start += RETRAIN_STEP_CANDLES

    return pd.concat(all_preds, ignore_index=True) if all_preds else pd.DataFrame()


def compute_auc(oos: pd.DataFrame):
    """محاسبهی AUC برای خرید و فروش"""
    y_true = oos['label'].values
    y_up = (y_true == 1).astype(int)
    y_down = (y_true == -1).astype(int)
    
    auc_up = np.nan
    auc_down = np.nan
    
    if 0 < y_up.sum() < len(y_up):
        auc_up = roc_auc_score(y_up, oos['proba_1'].values)
    if 0 < y_down.sum() < len(y_down):
        auc_down = roc_auc_score(y_down, oos['proba_-1'].values)
    
    return auc_up, auc_down


def run():
    print("=" * 80)
    print("آزمایش: تأثیر فیچرهای پیشرفته بر قوت مدل")
    print("=" * 80)

    print("\n📥 دریافت داده...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)

    print("🔨 ساخت دیتاست فقط با فیچرهای قدیمی...")
    dataset_old = build_dataset(raw, for_training=True)
    dataset_old = dataset_old.reset_index(drop=True)

    print("🔨 ساخت دیتاست با فیچرهای جدید...")
    dataset_new = build_integrated_dataset(raw, for_training=True, use_advanced=True)
    dataset_new = dataset_new.reset_index(drop=True)

    print(f"\nدیتاست قدیمی: {len(dataset_old)} ردیف")
    print(f"دیتاست جدید: {len(dataset_new)} ردیف")
    print(f"فیچرهای اضافه‌شده: {len(dataset_new.columns) - len(dataset_old.columns)}")

    if len(dataset_old) < TRAIN_WINDOW_CANDLES + RETRAIN_STEP_CANDLES:
        print("\n⚠️ دادهی کافی برای walk-forward وجود ندارد")
        return

    # تست دیتاست قدیمی
    print("\n" + "=" * 80)
    print("🧪 آزمایش مدل قدیمی (فقط Momentum/Trend)...")
    print("=" * 80)
    oos_old = train_and_predict_folds(dataset_old, FEATURE_COLUMNS)
    auc_up_old, auc_down_old = compute_auc(oos_old)

    # تست دیتاست جدید
    print("\n" + "=" * 80)
    print("🧪 آزمایش مدل جدید (+ Market Microstructure)...")
    print("=" * 80)
    new_feature_cols = get_all_feature_columns(use_advanced=True)
    oos_new = train_and_predict_folds(dataset_new, new_feature_cols)
    auc_up_new, auc_down_new = compute_auc(oos_new)

    # مقایسه
    print("\n" + "=" * 80)
    print("📊 نتایج مقایسه")
    print("=" * 80)
    print(f"\n{'معیار':<30} {'مدل قدیمی':<20} {'مدل جدید':<20} {'تفاوت':<15}")
    print("-" * 85)
    print(f"{'AUC خرید (1)':<30} {auc_up_old:.4f}{'':<15} {auc_up_new:.4f}{'':<15} {auc_up_new - auc_up_old:+.4f}")
    print(f"{'AUC فروش (-1)':<30} {auc_down_old:.4f}{'':<15} {auc_down_new:.4f}{'':<15} {auc_down_new - auc_down_old:+.4f}")

    improvement_up = auc_up_new - auc_up_old
    improvement_down = auc_down_new - auc_down_old
    max_improvement = max(improvement_up, improvement_down)

    print("\n" + "=" * 80)
    print("💬 نتیجه‌گیری")
    print("=" * 80)
    
    if max_improvement >= 0.03:
        print("✅ بهبود قابل توجه! فیچرهای جدید سیگنال معنیداری اضافه کردند.")
        print(f"   بهترین بهبود: {max_improvement:.4f} واحد AUC")
    elif max_improvement > 0:
        print("〰️ بهبود جزئی. فیچرهای جدید کمکی میکنند ولی محدود.")
        print(f"   بهبود: {max_improvement:.4f} واحد AUC")
    else:
        print("⚠️ بدون بهبود یا بدتر شدن!")
        print("   فیچرهای جدید در این حالت کمک خاصی نکردند.")

    return {
        'auc_up_old': auc_up_old,
        'auc_down_old': auc_down_old,
        'auc_up_new': auc_up_new,
        'auc_down_new': auc_down_new,
    }


if __name__ == '__main__':
    run()
