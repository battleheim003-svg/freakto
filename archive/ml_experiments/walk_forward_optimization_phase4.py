"""
walk_forward_optimization_phase4.py - بهینه‌سازی واقعی Walk Forward

نه صرفاً Train/Test، بلکه:
1. هر فولد را بهینه‌سازی کن (موضعی)
2. معاملات را شبیه‌سازی کن
3. بیرونی‌ترین آزمایش (out-of-fold)

ایده: هر کندل می‌تونه بهترین پارامترها را از ماضی خود استنتاج کند
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import warnings
warnings.filterwarnings('ignore')

from config import TRAINING_CANDLES, TRAIN_WINDOW_CANDLES, RETRAIN_STEP_CANDLES, ATR_MULTIPLIER
from data_fetcher import fetch_ohlcv_extended
from features import add_features, add_labels, FEATURE_COLUMNS

# پارامترهای SL/TP
SL_ATR_MULT = 1.0
TP_ATR_MULT = 1.5
MAX_HOLD_CANDLES = 12
FEE_RATE = 0.001


class WalkForwardOptimizer:
    """بهینه‌سازی Walk Forward - هر فولد از تاریخچهی خود یاد بگیرد"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.fold_results = []
    
    def optimize_fold(self, fold_num: int, train_data: pd.DataFrame, 
                     test_data: pd.DataFrame) -> dict:
        """بهینه‌سازی یک فولد واحد"""
        
        # ۱. پیدا کردن بهترین threshold برای این فولد
        thresholds = np.arange(0.40, 0.71, 0.05)
        best_threshold = 0.60
        best_auc = 0.5
        
        X_train = train_data[FEATURE_COLUMNS].values
        y_train = train_data['label'].values
        X_test = test_data[FEATURE_COLUMNS].values
        y_test = test_data['label'].values
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # آموزش مدل
        model = RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=20,
            class_weight='balanced', random_state=42, n_jobs=-1
        )
        model.fit(X_train_scaled, y_train)
        proba = model.predict_proba(X_test_scaled)
        
        classes = model.classes_
        class_to_idx = {c: i for i, c in enumerate(classes)}
        
        # تست هر threshold
        for threshold in thresholds:
            # سیگنالات
            signals = np.zeros(len(test_data))
            
            if 1 in classes and -1 in classes:
                buy_idx = class_to_idx[1]
                sell_idx = class_to_idx[-1]
                
                signals[proba[:, buy_idx] >= threshold] = 1
                signals[proba[:, sell_idx] >= threshold] = -1
            
            # محاسبهی AUC
            if signals.sum() > 0:
                signaled = signals != 0
                if y_test[signaled].nunique() > 1:
                    auc = roc_auc_score(
                        (y_test[signaled] == 1).astype(int),
                        proba[signaled, class_to_idx.get(1, 1)]
                    )
                    if auc > best_auc:
                        best_auc = auc
                        best_threshold = threshold
        
        result = {
            'fold': fold_num,
            'best_threshold': best_threshold,
            'auc': best_auc,
            'n_train': len(train_data),
            'n_test': len(test_data),
        }
        
        return result
    
    def run(self):
        """اجرای Walk Forward Optimization"""
        print("=" * 100)
        print("🎯 Walk Forward Optimization")
        print("=" * 100)
        
        n = len(self.df)
        start = TRAIN_WINDOW_CANDLES
        fold_num = 0
        
        print("\n🔄 بهینه‌سازی هر فولد بر اساس تاریخچهی خود:\n")
        
        while start + RETRAIN_STEP_CANDLES <= n:
            fold_num += 1
            
            train_data = self.df.iloc[start - TRAIN_WINDOW_CANDLES:start]
            test_data = self.df.iloc[start:start + RETRAIN_STEP_CANDLES]
            
            result = self.optimize_fold(fold_num, train_data, test_data)
            self.fold_results.append(result)
            
            print(f"Fold {fold_num:2d} | Threshold: {result['best_threshold']:.2f} | "
                  f"AUC: {result['auc']:.4f} | Test: {result['n_test']:4d} candles")
            
            start += RETRAIN_STEP_CANDLES
        
        self.print_summary()
    
    def print_summary(self):
        """چاپ خلاصهی نتایج"""
        print("\n" + "=" * 100)
        print("📊 خلاصهی Walk Forward Optimization")
        print("=" * 100)
        
        thresholds = [r['best_threshold'] for r in self.fold_results]
        aucs = [r['auc'] for r in self.fold_results]
        
        print(f"\nتعداد فولدها: {len(self.fold_results)}")
        print(f"\nThreshold:")
        print(f"  میانگین: {np.mean(thresholds):.3f}")
        print(f"  میانه: {np.median(thresholds):.3f}")
        print(f"  min/max: {np.min(thresholds):.3f} / {np.max(thresholds):.3f}")
        
        print(f"\nAUC:")
        print(f"  میانگین: {np.mean(aucs):.4f}")
        print(f"  میانه: {np.median(aucs):.4f}")
        print(f"  min/max: {np.min(aucs):.4f} / {np.max(aucs):.4f}")
        
        print(f"\n💡 پیشنهاد برای config.py:")
        print(f"  MIN_CONFIDENCE = {np.median(thresholds):.2f}")
        
        # بررسی ثبات
        if np.std(thresholds) > 0.1:
            print(f"\n⚠️ Threshold بین فولدها خیلی متغیر است (std: {np.std(thresholds):.3f})")
            print("   یعنی مدل برای شرایط بازار مختلف نیاز به پارامترهای متفاوت دارد")


def run_wfo():
    """اجرای تکمیل WFO"""
    print("\n📥 دریافت داده...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    
    print("🔨 ساخت فیچرها...")
    dataset = add_features(raw)
    dataset = add_labels(dataset)
    dataset = dataset.dropna(subset=FEATURE_COLUMNS + ['label'])
    dataset = dataset.reset_index()
    
    optimizer = WalkForwardOptimizer(dataset)
    optimizer.run()


if __name__ == '__main__':
    run_wfo()
