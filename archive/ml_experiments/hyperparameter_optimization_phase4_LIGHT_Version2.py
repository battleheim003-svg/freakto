"""
hyperparameter_optimization_phase4_LIGHT.py - بهینه‌سازی بدون نیاز به Optuna

از GridSearch ساده استفاده میکند (بجای Optuna که نصب نیست)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import warnings
warnings.filterwarnings('ignore')

from config import TRAINING_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import add_features, FEATURE_COLUMNS


class GridSearchOptimizer:
    """بهینه‌سازی ساده با GridSearch"""
    
    def __init__(self, raw_data: pd.DataFrame):
        self.raw_data = raw_data
        self.best_params = None
        self.best_score = 0
        self.results = []
    
    def build_dataset_with_params(self, atr_mult: float, lookahead: int):
        """ساخت دیتاست با پارامترهای مشخص"""
        df = add_features(self.raw_data.copy())
        
        future_return = df['close'].shift(-lookahead) / df['close'] - 1
        dynamic_threshold = df['atr_pct'] * atr_mult
        
        df['future_return'] = future_return
        df['label'] = 0
        df.loc[future_return >= dynamic_threshold, 'label'] = 1
        df.loc[future_return <= -dynamic_threshold, 'label'] = -1
        
        df = df.dropna(subset=FEATURE_COLUMNS + ['label'])
        return df
    
    def evaluate(self, dataset: pd.DataFrame, min_conf: float):
        """ارزیابی یک set پارامترها"""
        
        # تقسیم
        split_idx = int(len(dataset) * 0.8)
        train = dataset.iloc[:split_idx]
        test = dataset.iloc[split_idx:]
        
        X_train = train[FEATURE_COLUMNS].values
        y_train = train['label'].values
        X_test = test[FEATURE_COLUMNS].values
        y_test = test['label'].values
        
        if len(train) < 100 or len(test) < 50:
            return 0.5, 0
        
        # آموزش
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=20,
            class_weight='balanced', random_state=42, n_jobs=-1
        )
        model.fit(X_train_scaled, y_train)
        
        # ارزیابی
        proba = model.predict_proba(X_test_scaled)
        classes = model.classes_
        
        auc_scores = []
        for target_cls in [1, -1]:
            if target_cls in classes:
                idx = list(classes).index(target_cls)
                y_binary = (y_test == target_cls).astype(int)
                
                if y_binary.sum() > 0 and y_binary.sum() < len(y_test):
                    auc = roc_auc_score(y_binary, proba[:, idx])
                    auc_scores.append(auc)
        
        avg_auc = np.mean(auc_scores) if auc_scores else 0.5
        n_signals = ((proba.max(axis=1) > min_conf)).sum()
        
        return avg_auc, n_signals
    
    def optimize(self):
        """بهینه‌سازی با GridSearch"""
        print("=" * 100)
        print("🚀 بهینه‌سازی Hyperparameter (GridSearch)")
        print("=" * 100)
        
        # Grid parameters
        atr_mults = [0.2, 0.3, 0.4, 0.5, 0.6]
        lookaheads = [1, 2, 3]
        min_confs = [0.50, 0.55, 0.60]
        
        total_tests = len(atr_mults) * len(lookaheads) * len(min_confs)
        print(f"\n🔄 تعداد ترکیبات: {total_tests}")
        print(f"این ممکن است ۱۰-۲۰ دقیقه طول بکشد...\n")
        
        test_num = 0
        print(f"{'ATR':<8} {'LA':<6} {'MinC':<8} {'AUC':<10} {'Signals':<10} {'Status'}")
        print("-" * 60)
        
        for atr_mult in atr_mults:
            for lookahead in lookaheads:
                # ساخت دیتاست یکبار
                try:
                    dataset = self.build_dataset_with_params(atr_mult, lookahead)
                except Exception as e:
                    continue
                
                for min_conf in min_confs:
                    test_num += 1
                    
                    try:
                        auc, n_signals = self.evaluate(dataset, min_conf)
                        
                        result = {
                            'atr_mult': atr_mult,
                            'lookahead': lookahead,
                            'min_conf': min_conf,
                            'auc': auc,
                            'n_signals': n_signals,
                        }
                        self.results.append(result)
                        
                        status = "✓" if auc > 0.52 else "〜" if auc > 0.50 else "✗"
                        print(f"{atr_mult:<8.1f} {lookahead:<6} {min_conf:<8.2f} "
                              f"{auc:<10.4f} {n_signals:<10} {status}")
                        
                        if auc > self.best_score:
                            self.best_score = auc
                            self.best_params = result
                    
                    except Exception as e:
                        print(f"{atr_mult:<8.1f} {lookahead:<6} {min_conf:<8.2f} "
                              f"{'ERROR':<10} - {str(e)[:20]}")
        
        self.print_summary()
    
    def print_summary(self):
        """چاپ خلاصهی نتایج"""
        print("\n" + "=" * 100)
        print("🏆 بهترین Hyperparameters")
        print("=" * 100)
        
        if self.best_params is None:
            print("⚠️ هیچ نتیجهی خوبی پیدا نشد")
            return
        
        print(f"\n✅ بهترین AUC: {self.best_score:.4f}\n")
        
        for param, value in self.best_params.items():
            if param != 'auc' and param != 'n_signals':
                print(f"  {param:<15} = {value}")
        
        print(f"\n  تعداد سیگنالها: {self.best_params['n_signals']}")
        
        # توصیهها
        print(f"\n" + "=" * 100)
        print("💡 توصیهات برای config.py:")
        print("=" * 100)
        print(f"""
ATR_MULTIPLIER = {self.best_params['atr_mult']}
LOOKAHEAD_CANDLES = {self.best_params['lookahead']}
MIN_CONFIDENCE = {self.best_params['min_conf']}
        """)
        
        # تحلیل نتایج
        print("\n" + "=" * 100)
        print("📊 تحلیل نتایج")
        print("=" * 100)
        
        results_df = pd.DataFrame(self.results)
        
        print(f"\nAUC Statistics:")
        print(f"  میانگین: {results_df['auc'].mean():.4f}")
        print(f"  بهترین: {results_df['auc'].max():.4f}")
        print(f"  بدترین: {results_df['auc'].min():.4f}")
        
        if results_df['auc'].max() > 0.52:
            print("\n✅ نتایج بهتر از شانس هستند!")
        elif results_df['auc'].max() > 0.50:
            print("\n〰️ نتایج تقریباً در حد شانس هستند")
        else:
            print("\n❌ نتایج بدتر از شانس هستند - نیاز به تغییر رویکرد")


def run_optimization():
    """اجرای بهینه‌سازی کامل"""
    print("\n📥 دریافت داده...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    
    optimizer = GridSearchOptimizer(raw)
    optimizer.optimize()
    
    return optimizer.best_params


if __name__ == '__main__':
    best_params = run_optimization()
