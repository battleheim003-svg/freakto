"""
hyperparameter_optimization_phase4.py - بهینه‌سازی Hyperparameter با Optuna

اهداف:
1. بهترین ATR_MULTIPLIER را پیدا کنیم
2. بهترین MIN_CONFIDENCE را پیدا کنیم
3. بهترین پارامترهای مدل را پیدا کنیم
4. Walk Forward Optimization (نه صرفاً train/test)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import optuna
from optuna.pruners import MedianPruner
import warnings
warnings.filterwarnings('ignore')

from config import TRAINING_CANDLES, TRAIN_WINDOW_CANDLES, RETRAIN_STEP_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import add_features, FEATURE_COLUMNS


class HyperparameterOptimizer:
    """بهینه‌سازی Hyperparameter برای بهترین نتایج"""
    
    def __init__(self, raw_data: pd.DataFrame, n_trials: int = 50):
        """
        Parameters:
        -----------
        raw_data: داده OHLCV خام
        n_trials: تعداد آزمایش‌های Optuna
        """
        self.raw_data = raw_data
        self.n_trials = n_trials
        self.best_params = None
        self.best_score = 0
    
    def build_dataset_with_atr_mult(self, atr_mult: float):
        """ساخت دیتاست با ATR_MULTIPLIER مشخص"""
        df = add_features(self.raw_data.copy())
        
        # لیبل‌گذاری با ATR_MULTIPLIER سفارشی
        from config import LOOKAHEAD_CANDLES
        future_return = df['close'].shift(-LOOKAHEAD_CANDLES) / df['close'] - 1
        dynamic_threshold = df['atr_pct'] * atr_mult
        
        df['future_return'] = future_return
        df['label'] = 0
        df.loc[future_return >= dynamic_threshold, 'label'] = 1
        df.loc[future_return <= -dynamic_threshold, 'label'] = -1
        
        df = df.dropna(subset=FEATURE_COLUMNS + ['label'])
        return df
    
    def evaluate_on_validation(self, dataset: pd.DataFrame, 
                               atr_mult: float, min_conf: float,
                               rf_params: dict) -> float:
        """ارزیابی یک set پارامترها روی validation set"""
        
        # تقسیم
        split_idx = int(len(dataset) * 0.8)
        train = dataset.iloc[:split_idx]
        test = dataset.iloc[split_idx:]
        
        X_train = train[FEATURE_COLUMNS].values
        y_train = train['label'].values
        X_test = test[FEATURE_COLUMNS].values
        y_test = test['label'].values
        
        # آموزش
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(**rf_params, random_state=42, n_jobs=-1)
        model.fit(X_train_scaled, y_train)
        
        # ارزیابی
        proba = model.predict_proba(X_test_scaled)
        classes = model.classes_
        
        # AUC برای خرید/فروش
        auc_scores = []
        for target_cls in [1, -1]:
            if target_cls in classes:
                idx = list(classes).index(target_cls)
                y_binary = (y_test == target_cls).astype(int)
                
                if y_binary.sum() > 0 and y_binary.sum() < len(y_binary):
                    auc = roc_auc_score(y_binary, proba[:, idx])
                    auc_scores.append(auc)
        
        # نمره نهایی: میانگین AUC
        return np.mean(auc_scores) if auc_scores else 0.5
    
    def objective(self, trial):
        """تابع Objective برای Optuna"""
        
        # Hyperparameters برای تست
        atr_mult = trial.suggest_float('atr_mult', 0.2, 2.0, step=0.1)
        min_conf = trial.suggest_float('min_conf', 0.4, 0.7, step=0.05)
        
        n_estimators = trial.suggest_int('n_estimators', 100, 500, step=50)
        max_depth = trial.suggest_int('max_depth', 3, 10)
        min_samples_leaf = trial.suggest_int('min_samples_leaf', 5, 50, step=5)
        
        rf_params = {
            'n_estimators': n_estimators,
            'max_depth': max_depth,
            'min_samples_leaf': min_samples_leaf,
            'class_weight': 'balanced',
        }
        
        try:
            # ساخت دیتاست با این ATR_MULTIPLIER
            dataset = self.build_dataset_with_atr_mult(atr_mult)
            
            if len(dataset) < 100:
                return 0.5  # نمره بدی برای dataset های کوچک
            
            # ارزیابی
            score = self.evaluate_on_validation(dataset, atr_mult, min_conf, rf_params)
            
            return score
        
        except Exception as e:
            print(f"⚠️ خطا برای trial: {e}")
            return 0.5
    
    def optimize(self):
        """اجرای بهینه‌سازی"""
        print("=" * 100)
        print("🚀 بهینه‌سازی Hyperparameter با Optuna")
        print("=" * 100)
        print(f"\n🔄 تعداد آزمایش: {self.n_trials}")
        print("این ممکن است 10-30 دقیقه طول بکشد...\n")
        
        sampler = optuna.samplers.TPESampler(seed=42)
        pruner = MedianPruner()
        
        study = optuna.create_study(
            direction='maximize',
            sampler=sampler,
            pruner=pruner
        )
        
        study.optimize(self.objective, n_trials=self.n_trials, show_progress_bar=True)
        
        # بهترین نتایج
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        print("\n" + "=" * 100)
        print("🏆 بهترین Hyperparameters")
        print("=" * 100)
        print(f"بهترین AUC: {self.best_score:.4f}\n")
        
        for param, value in sorted(self.best_params.items()):
            print(f"  {param:<25} {value}")
        
        return self.best_params
    
    def print_summary(self):
        """چاپ خلاصهی نتایج"""
        if self.best_params is None:
            print("⚠️ ابتدا optimize() را فراخوانی کن")
            return
        
        print("\n" + "=" * 100)
        print("📊 خلاصهی بهینه‌سازی")
        print("=" * 100)
        
        print(f"""
✅ بهترین AUC: {self.best_score:.4f}

تغییرات پیشنهادی برای config.py:
---------
ATR_MULTIPLIER = {self.best_params.get('atr_mult', 1.0):.2f}
MIN_CONFIDENCE = {self.best_params.get('min_conf', 0.60):.2f}

بهترین Hyperparameters برای Random Forest:
---------
n_estimators = {self.best_params.get('n_estimators', 300)}
max_depth = {self.best_params.get('max_depth', 6)}
min_samples_leaf = {self.best_params.get('min_samples_leaf', 20)}
        """)


def run_optimization():
    """اجرای بهینه‌سازی کامل"""
    print("\n📥 دریافت داده...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    
    optimizer = HyperparameterOptimizer(raw, n_trials=50)
    optimizer.optimize()
    optimizer.print_summary()
    
    return optimizer.best_params


if __name__ == '__main__':
    best_params = run_optimization()
