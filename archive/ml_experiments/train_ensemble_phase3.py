"""
آموزش مدل Ensemble با Feature Selection

مراحل:
1. ساخت دیتاست جدید
2. انتخاب بهترین فیچرها
3. آموزش Ensemble
4. ذخیرهی مدل
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from config import MODEL_PATH, TRAINING_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features_integrated import build_integrated_dataset, get_all_feature_columns
from feature_selector import FeatureSelector
from ensemble_models import EnsemblePredictor


def train_ensemble():
    """آموزش مدل Ensemble کامل"""
    
    print("=" * 80)
    print("🚀 آموزش Ensemble مدل (فاز سوم)")
    print("=" * 80)
    
    # ۱. دریافت داده
    print("\n📥 دریافت داده...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    
    # ۲. ساخت فیچرها
    print("🔨 ساخت فیچرها (قدیمی + جدید)...")
    dataset = build_integrated_dataset(raw, for_training=True, use_advanced=True)
    all_feature_cols = get_all_feature_columns(use_advanced=True)
    
    print(f"✓ {len(dataset)} ردیف داده")
    print(f"✓ {len(all_feature_cols)} فیچر کاندید")
    
    # ۳. تقسیم داده
    split_idx = int(len(dataset) * 0.7)
    val_idx = int(len(dataset) * 0.85)
    
    train_data = dataset.iloc[:split_idx]
    val_data = dataset.iloc[split_idx:val_idx]
    test_data = dataset.iloc[val_idx:]
    
    print(f"\n📊 تقسیم داده:")
    print(f"   Train: {len(train_data)}")
    print(f"   Validation: {len(val_data)}")
    print(f"   Test: {len(test_data)}")
    
    # ۴. انتخاب فیچرها
    print("\n" + "=" * 80)
    print("🔍 مرحلهی ۱: انتخاب بهترین فیچرها")
    print("=" * 80)
    
    X_train = train_data[all_feature_cols].values
    y_train = train_data['label'].values
    X_val = val_data[all_feature_cols].values
    y_val = val_data['label'].values
    X_test = test_data[all_feature_cols].values
    y_test = test_data['label'].values
    
    selector = FeatureSelector(max_features=25, method='permutation')
    selected_features = selector.fit(
        X_train, y_train, all_feature_cols,
        X_test, y_test
    )
    selector.print_summary()
    
    # فیلتر کردن فیچرها
    feature_idx = [all_feature_cols.index(f) for f in selected_features]
    X_train_selected = X_train[:, feature_idx]
    X_val_selected = X_val[:, feature_idx]
    X_test_selected = X_test[:, feature_idx]
    
    # ۵. آموزش Ensemble
    print("\n" + "=" * 80)
    print("🚀 مرحلهی ۲: آموزش Ensemble مدل")
    print("=" * 80)
    
    # سعی کن XGBoost و LightGBM را استفاده کنی (اگر موجود باشند)
    ensemble = EnsemblePredictor(
        use_xgboost=False,  # در بسته نیست
        use_lightgbm=False,  # در بسته نیست
        use_catboost=False,  # در بسته نیست
        voting='soft'  # میانگین احتمالات
    )
    
    ensemble.fit(X_train_selected, y_train, X_val_selected, y_val)
    
    # ۶. ارزیابی روی Test
    print("\n" + "=" * 80)
    print("📊 مرحلهی ۳: ارزیابی نتایج")
    print("=" * 80)
    
    y_pred = ensemble.predict(X_test_selected)
    y_pred_proba = ensemble.predict_proba(X_test_selected)
    
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
    
    acc = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {acc:.4f}")
    
    # AUC برای هر کلاس
    y_up = (y_test == 1).astype(int)
    y_down = (y_test == -1).astype(int)
    
    if y_up.sum() > 0 and y_up.sum() < len(y_up):
        auc_up = roc_auc_score(y_up, y_pred_proba[:, 1] if y_pred_proba.shape[1] > 1 else y_pred_proba[:, 0])
        print(f"AUC خرید (1): {auc_up:.4f}")
    
    if y_down.sum() > 0 and y_down.sum() < len(y_down):
        auc_down = roc_auc_score(y_down, y_pred_proba[:, 0] if y_pred_proba.shape[1] > 2 else 1 - y_pred_proba[:, 1])
        print(f"AUC فروش (-1): {auc_down:.4f}")
    
    # ۷. ذخیره مدل
    print("\n" + "=" * 80)
    print("💾 ذخیرهی مدل")
    print("=" * 80)
    
    model_bundle = {
        'ensemble': ensemble,
        'feature_selector': selector,
        'selected_features': selected_features,
        'all_features': all_feature_cols,
        'feature_indices': feature_idx,
        'use_advanced': True,
        'train_end_timestamp': dataset.index[split_idx - 1],
    }
    
    ensemble_model_path = MODEL_PATH.replace('.joblib', '_ensemble.joblib')
    joblib.dump(model_bundle, ensemble_model_path)
    print(f"✅ مدل Ensemble ذخیره شد: {ensemble_model_path}")
    
    return model_bundle


if __name__ == '__main__':
    bundle = train_ensemble()
