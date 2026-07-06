"""
compare_all_models.py - مقایسهی:
  1. مدل قدیمی (فقط momentum/trend)
  2. مدل جدید (با advanced features)
  3. Ensemble (چند مدل + voting)
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
from feature_selector import FeatureSelector
from ensemble_models import EnsemblePredictor


def train_and_evaluate(X_train, y_train, X_test, y_test, model_type='rf'):
    """آموزش و ارزیابی مدل"""
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    if model_type == 'rf':
        model = RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=20,
            class_weight='balanced', random_state=42, n_jobs=-1
        )
        model.fit(X_train_scaled, y_train)
        proba = model.predict_proba(X_test_scaled)
    elif model_type == 'ensemble':
        model = EnsemblePredictor(voting='soft')
        model.fit(X_train_scaled, y_train)
        proba = model.predict_proba(X_test_scaled)
    
    return proba


def compute_auc_multiclass(y_true, proba):
    """محاسبهی AUC برای چند کلاسی"""
    y_up = (y_true == 1).astype(int)
    y_down = (y_true == -1).astype(int)
    
    auc_up = np.nan
    auc_down = np.nan
    
    if 0 < y_up.sum() < len(y_up) and proba.shape[1] > 1:
        auc_up = roc_auc_score(y_up, proba[:, 1])
    if 0 < y_down.sum() < len(y_down):
        if proba.shape[1] > 2:
            auc_down = roc_auc_score(y_down, proba[:, 0])
        else:
            auc_down = roc_auc_score(y_down, 1 - proba[:, 1])
    
    return auc_up, auc_down


def run_comparison():
    """مقایسهی کامل تمام مدلها"""
    
    print("=" * 100)
    print("🏆 مقایسهی تمام مدلها")
    print("=" * 100)
    
    # ۱. آماده‌سازی داده
    print("\n📥 دریافت و آماده‌سازی داده...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    
    dataset_old = build_dataset(raw, for_training=True).reset_index(drop=True)
    dataset_new = build_integrated_dataset(raw, for_training=True, use_advanced=True).reset_index(drop=True)
    
    print(f"✓ داده قدیمی: {len(dataset_old)} ردیف")
    print(f"✓ داده جدید: {len(dataset_new)} ردیف")
    
    # تقسیم داده
    split_idx = int(len(dataset_old) * 0.8)
    
    # قدیمی
    X_train_old = dataset_old.iloc[:split_idx][FEATURE_COLUMNS].values
    y_train_old = dataset_old.iloc[:split_idx]['label'].values
    X_test_old = dataset_old.iloc[split_idx:][FEATURE_COLUMNS].values
    y_test_old = dataset_old.iloc[split_idx:]['label'].values
    
    # جدید
    all_features = get_all_feature_columns(use_advanced=True)
    X_train_new = dataset_new.iloc[:split_idx][all_features].values
    y_train_new = dataset_new.iloc[:split_idx]['label'].values
    X_test_new = dataset_new.iloc[split_idx:][all_features].values
    y_test_new = dataset_new.iloc[split_idx:]['label'].values
    
    # انتخاب فیچرها
    print("\n🔍 انتخاب بهترین فیچرها...")
    selector = FeatureSelector(max_features=25, method='permutation')
    selected = selector.fit(X_train_new, y_train_new, all_features, X_test_new, y_test_new)
    
    feat_idx = [all_features.index(f) for f in selected]
    X_train_selected = X_train_new[:, feat_idx]
    X_test_selected = X_test_new[:, feat_idx]
    
    print(f"✓ {len(selected)} فیچر انتخاب‌شده")
    
    # ۲. آموزش مدلها
    print("\n" + "=" * 100)
    print("🧠 آموزش مدلها...")
    print("=" * 100)
    
    results = {}
    
    # مدل ۱: قدیمی
    print("\n1️⃣ مدل قدیمی (Momentum/Trend فقط)...")
    proba_old = train_and_evaluate(X_train_old, y_train_old, X_test_old, y_test_old, 'rf')
    auc_up_old, auc_down_old = compute_auc_multiclass(y_test_old, proba_old)
    results['old'] = {'auc_up': auc_up_old, 'auc_down': auc_down_old}
    
    # مدل ۲: جدید (تمام فیچرها)
    print("2️⃣ مدل جدید (با Advanced Features)...")
    proba_new_all = train_and_evaluate(X_train_new, y_train_new, X_test_new, y_test_new, 'rf')
    auc_up_new_all, auc_down_new_all = compute_auc_multiclass(y_test_new, proba_new_all)
    results['new_all'] = {'auc_up': auc_up_new_all, 'auc_down': auc_down_new_all}
    
    # مدل ۳: جدید (فیچرهای انتخاب‌شده)
    print("3️⃣ مدل جدید (فیچرهای انتخاب‌شده)...")
    proba_new_selected = train_and_evaluate(X_train_selected, y_train_selected, 
                                            X_test_selected, y_test_selected, 'rf')
    auc_up_new_sel, auc_down_new_sel = compute_auc_multiclass(y_test_selected, proba_new_selected)
    results['new_selected'] = {'auc_up': auc_up_new_sel, 'auc_down': auc_down_new_sel}
    
    # مدل ۴: Ensemble
    print("4️⃣ Ensemble مدل (بدون فیچر انتخاب)...")
    proba_ensemble = train_and_evaluate(X_train_new, y_train_new, X_test_new, y_test_new, 'ensemble')
    auc_up_ens, auc_down_ens = compute_auc_multiclass(y_test_new, proba_ensemble)
    results['ensemble'] = {'auc_up': auc_up_ens, 'auc_down': auc_down_ens}
    
    # ۳. نمایش نتایج
    print("\n" + "=" * 100)
    print("📊 نتایج مقایسه")
    print("=" * 100)
    
    models = [
        ('قدیمی (Momentum)', 'old'),
        ('جدید (تمام)', 'new_all'),
        ('جدید (انتخاب‌شده)', 'new_selected'),
        ('Ensemble', 'ensemble'),
    ]
    
    print(f"\n{'نام مدل':<30} {'AUC خرید':<15} {'AUC فروش':<15} {'میانگین':<15}")
    print("-" * 75)
    
    best_model = None
    best_score = 0
    
    for name, key in models:
        auc_up = results[key]['auc_up']
        auc_down = results[key]['auc_down']
        avg = (auc_up + auc_down) / 2
        
        print(f"{name:<30} {auc_up:.4f}{'':<10} {auc_down:.4f}{'':<10} {avg:.4f}")
        
        if avg > best_score:
            best_score = avg
            best_model = name
    
    print("\n" + "=" * 100)
    print("🏆 نتیجه‌گیری")
    print("=" * 100)
    print(f"\n✅ بهترین مدل: {best_model} (امتیاز: {best_score:.4f})")
    
    # بهبودهای نسبی
    improvement_new_all = ((results['new_all']['auc_up'] + results['new_all']['auc_down']) / 2) - \
                          ((results['old']['auc_up'] + results['old']['auc_down']) / 2)
    improvement_ensemble = ((results['ensemble']['auc_up'] + results['ensemble']['auc_down']) / 2) - \
                          ((results['old']['auc_up'] + results['old']['auc_down']) / 2)
    
    print(f"\n📈 بهبود نسبی:")
    print(f"   جدید (تمام) → قدیمی: {improvement_new_all:+.4f}")
    print(f"   Ensemble → قدیمی: {improvement_ensemble:+.4f}")
    
    if best_score <= 0.51:
        print("\n⚠️ تمام مدلها تقریباً در حد شانس هستند (AUC ≈ 0.50)")
        print("نیاز به:")
        print("  • بازبینی روش لیبلگذاری (شاید لیبلها خوب تعریف نشده‌اند)")
        print("  • فیچرهای بیشتر/بهتر")
        print("  • دادهی بیشتر")


if __name__ == '__main__':
    run_comparison()
