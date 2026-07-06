"""
walk_forward_optimization_final.py - Walk Forward نهایی

تست برای هر فولد:
- بهترین threshold
- بهترین MIN_CONFIDENCE
- AUC و تعداد سیگنال
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
from features import add_features, add_labels, FEATURE_COLUMNS


def run_wfo():
    """اجرای Walk Forward Optimization"""
    
    print("=" * 100)
    print("🎯 Walk Forward Optimization - نسخهی نهایی")
    print("=" * 100)
    
    # ۱. دریافت داده
    print(f"\n📥 دریافت {TRAINING_CANDLES} کندل...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    
    # ۲. ساخت فیچرها
    print("🔨 ساخت فیچرها...")
    dataset = add_features(raw)
    dataset = add_labels(dataset)
    dataset = dataset.dropna(subset=FEATURE_COLUMNS + ['label'])
    dataset = dataset.reset_index(drop=True)
    
    print(f"✓ {len(dataset)} ردیف آماده\n")
    
    # ۳. Walk Forward Loop
    print("=" * 100)
    print("🔄 بهینه‌سازی هر فولد")
    print("=" * 100)
    
    n = len(dataset)
    start = TRAIN_WINDOW_CANDLES
    fold_num = 0
    fold_results = []
    
    thresholds = [0.50, 0.55, 0.60]
    
    print(f"\n{'Fold':<6} {'Threshold':<12} {'AUC':<10} {'Signals':<10} {'Status'}")
    print("-" * 60)
    
    while start + RETRAIN_STEP_CANDLES <= n:
        fold_num += 1
        
        train_data = dataset.iloc[start - TRAIN_WINDOW_CANDLES:start]
        test_data = dataset.iloc[start:start + RETRAIN_STEP_CANDLES]
        
        # آموزش
        X_train = train_data[FEATURE_COLUMNS].values
        y_train = train_data['label'].values
        X_test = test_data[FEATURE_COLUMNS].values
        y_test = test_data['label'].values
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=20,
            class_weight='balanced', random_state=42, n_jobs=-1
        )
        model.fit(X_train_scaled, y_train)
        
        proba = model.predict_proba(X_test_scaled)
        classes = model.classes_
        class_to_idx = {c: i for i, c in enumerate(classes)}
        
        # تست هر threshold
        best_threshold = 0.55
        best_auc = 0.5
        best_signals = 0
        
        for threshold in thresholds:
            signals = np.zeros(len(test_data))
            
            if 1 in classes and -1 in classes:
                buy_idx = class_to_idx[1]
                sell_idx = class_to_idx[-1]
                signals[proba[:, buy_idx] >= threshold] = 1
                signals[proba[:, sell_idx] >= threshold] = -1
            
            n_signals = np.count_nonzero(signals)
            
            if n_signals > 0:
                signaled = signals != 0
                y_test_signaled = pd.Series(y_test[signaled])
                
                if len(y_test_signaled.unique()) > 1:
                    try:
                        if 1 in classes:
                            auc = roc_auc_score(
                                (y_test[signaled] == 1).astype(int),
                                proba[signaled, class_to_idx[1]]
                            )
                            if auc > best_auc:
                                best_auc = auc
                                best_threshold = threshold
                                best_signals = n_signals
                    except:
                        pass
        
        status = "✅" if best_auc > 0.55 else "〜" if best_auc > 0.50 else "❌"
        print(f"{fold_num:<6} {best_threshold:<12.2f} {best_auc:<10.4f} "
              f"{best_signals:<10} {status}")
        
        fold_results.append({
            'fold': fold_num,
            'threshold': best_threshold,
            'auc': best_auc,
            'signals': best_signals,
        })
        
        start += RETRAIN_STEP_CANDLES
    
    # ۴. خلاصهی نتایج
    print("\n" + "=" * 100)
    print("📊 خلاصهی نتایج")
    print("=" * 100)
    
    if fold_results:
        thrs = [r['threshold'] for r in fold_results]
        aucs = [r['auc'] for r in fold_results]
        sigs = [r['signals'] for r in fold_results]
        
        print(f"\nتعداد فولدها: {len(fold_results)}")
        
        print(f"\n📊 Threshold:")
        print(f"  میانگین: {np.mean(thrs):.3f}")
        print(f"  میانه: {np.median(thrs):.3f}")
        
        print(f"\n📊 AUC:")
        print(f"  میانگین: {np.mean(aucs):.4f}")
        print(f"  میانه: {np.median(aucs):.4f}")
        
        print(f"\n📊 تعداد سیگنالها:")
        print(f"  کل: {np.sum(sigs)}")
        print(f"  میانگین بر فولد: {np.mean(sigs):.0f}")
        
        print(f"\n💡 پیشنهاد:")
        print(f"  MIN_CONFIDENCE = {np.median(thrs):.2f}")
        
        if np.mean(aucs) > 0.52:
            print("\n✅ نتایج بهتر از شانس هستند!")
        elif np.mean(aucs) > 0.50:
            print("\n〰️ نتایج تقریباً در حد شانس هستند")
        else:
            print("\n❌ نتایج بدتر از شانس هستند")


if __name__ == '__main__':
    run_wfo()
