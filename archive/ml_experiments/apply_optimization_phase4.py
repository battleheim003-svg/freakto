"""
apply_optimization_phase4.py - اعمال تغییرات بهینه‌سازی شده

مراحل:
1. تشخیص مشکل
2. اعمال تغییرات مقدماتی
3. بکتست
4. اگر بهتر شد → بهینه‌سازی بیشتر
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

from config import MODEL_PATH, TRAINING_CANDLES, TRAIN_WINDOW_CANDLES, RETRAIN_STEP_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import add_features, FEATURE_COLUMNS

# پارامترهای جدید پیشنهادی
NEW_ATR_MULTIPLIER = 0.3  # از 1.0
NEW_LOOKAHEAD_CANDLES = 1  # از 3
NEW_MIN_CONFIDENCE = 0.55  # از 0.60


def build_dataset_optimized(df, atr_mult=NEW_ATR_MULTIPLIER, 
                           lookahead=NEW_LOOKAHEAD_CANDLES):
    """ساخت دیتاست با پارامترهای نو"""
    df = add_features(df.copy())
    
    # لیبل‌گذاری نو
    future_return = df['close'].shift(-lookahead) / df['close'] - 1
    dynamic_threshold = df['atr_pct'] * atr_mult
    
    df['future_return'] = future_return
    df['label'] = 0
    df.loc[future_return >= dynamic_threshold, 'label'] = 1
    df.loc[future_return <= -dynamic_threshold, 'label'] = -1
    
    df = df.dropna(subset=FEATURE_COLUMNS + ['label'])
    return df


def test_optimization():
    """تست تأثیر تغییرات"""
    print("=" * 100)
    print("🧪 تست تأثیر بهینه‌سازی")
    print("=" * 100)
    
    print("\n📥 دریافت داده...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    
    # دیتاست قدیمی (فعلی)
    print("\n🔨 ساخت دیتاست با پارامترهای قدیمی...")
    from features import add_labels
    dataset_old = add_features(raw.copy())
    dataset_old = add_labels(dataset_old)
    dataset_old = dataset_old.dropna(subset=FEATURE_COLUMNS + ['label'])
    
    # دیتاست جدید (بهینه‌شده)
    print("🔨 ساخت دیتاست با پارامترهای جدید...")
    dataset_new = build_dataset_optimized(raw)
    
    # مقایسهی توزیع کلاسها
    print("\n" + "=" * 100)
    print("📊 مقایسهی توزیع کلاسها")
    print("=" * 100)
    
    print("\n❌ پارامترهای قدیمی:")
    old_dist = dataset_old['label'].value_counts(normalize=True).sort_index()
    for cls, frac in old_dist.items():
        name = {1: 'خرید', -1: 'فروش', 0: 'خنثی'}.get(cls)
        bar = '█' * int(frac * 50)
        print(f"  {name:<8} {frac*100:6.2f}% {bar}")
    
    print("\n✅ پارامترهای جدید:")
    new_dist = dataset_new['label'].value_counts(normalize=True).sort_index()
    for cls, frac in new_dist.items():
        name = {1: 'خرید', -1: 'فروش', 0: 'خنثی'}.get(cls)
        bar = '█' * int(frac * 50)
        print(f"  {name:<8} {frac*100:6.2f}% {bar}")
    
    # تقسیم و آموزش
    print("\n" + "=" * 100)
    print("🧠 مقایسهی عملکرد مدل")
    print("=" * 100)
    
    split_idx = int(len(dataset_old) * 0.8)
    
    # قدیمی
    X_train_old = dataset_old.iloc[:split_idx][FEATURE_COLUMNS].values
    y_train_old = dataset_old.iloc[:split_idx]['label'].values
    X_test_old = dataset_old.iloc[split_idx:][FEATURE_COLUMNS].values
    y_test_old = dataset_old.iloc[split_idx:]['label'].values
    
    # جدید
    split_idx_new = int(len(dataset_new) * 0.8)
    X_train_new = dataset_new.iloc[:split_idx_new][FEATURE_COLUMNS].values
    y_train_new = dataset_new.iloc[:split_idx_new]['label'].values
    X_test_new = dataset_new.iloc[split_idx_new:][FEATURE_COLUMNS].values
    y_test_new = dataset_new.iloc[split_idx_new:]['label'].values
    
    for name, X_tr, y_tr, X_te, y_te in [
        ('قدیمی', X_train_old, y_train_old, X_test_old, y_test_old),
        ('جدید', X_train_new, y_train_new, X_test_new, y_test_new),
    ]:
        print(f"\n{'='*50}")
        print(f"مدل {name}")
        print(f"{'='*50}")
        
        scaler = StandardScaler()
        X_tr_scaled = scaler.fit_transform(X_tr)
        X_te_scaled = scaler.transform(X_te)
        
        model = RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=20,
            class_weight='balanced', random_state=42, n_jobs=-1
        )
        model.fit(X_tr_scaled, y_tr)
        
        proba = model.predict_proba(X_te_scaled)
        classes = model.classes_
        class_to_idx = {c: i for i, c in enumerate(classes)}
        
        # AUC
        auc_scores = []
        for target_cls in [1, -1]:
            if target_cls in classes:
                idx = class_to_idx[target_cls]
                y_binary = (y_te == target_cls).astype(int)
                
                if y_binary.sum() > 0 and y_binary.sum() < len(y_te):
                    auc = roc_auc_score(y_binary, proba[:, idx])
                    auc_scores.append(auc)
                    cls_name = 'خرید' if target_cls == 1 else 'فروش'
                    print(f"  AUC {cls_name}: {auc:.4f}")
        
        if auc_scores:
            avg_auc = np.mean(auc_scores)
            print(f"  میانگین AUC: {avg_auc:.4f}")
    
    # نتیجه‌گیری
    print("\n" + "=" * 100)
    print("💡 نتیجه‌گیری")
    print("=" * 100)
    
    improvement = new_dist[0] < old_dist[0]  # آیا neutral کم شد؟
    
    if improvement:
        print("✅ توزیع کلاسها بهتر شد!")
        print("\n🎯 مراحل بعدی:")
        print("  1. تغییر config.py به پارامترهای جدید")
        print("  2. آموزش مدل دوباره با: python model_train_phase2.py")
        print("  3. بکتست: python backtest_phase2.py")
    else:
        print("⚠️ بهبودی برای ترتیب اقدام دیگر نیاز است")


if __name__ == '__main__':
    test_optimization()
