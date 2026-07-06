"""
ensemble_models.py - سیستم Ensemble Voting

ایده: از چند الگوریتم متفاوت استفاده میکنیم:
  1. Random Forest
  2. Gradient Boosting (XGBoost)
  3. LightGBM
  4. CatBoost
  5. Logistic Regression (برای diversity)

سپس با Voting میانگین میگیریم:
  - Soft Voting: میانگین احتمالات
  - Hard Voting: اکثریت رای
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from typing import List, Tuple

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("⚠️ XGBoost نصب نیست - نمایش نمی‌دهد")

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False
    print("⚠️ LightGBM نصب نیست - نمایش نمی‌دهد")

try:
    import catboost as cb
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False
    print("⚠️ CatBoost نصب نیست - نمایش نمی‌دهد")


class EnsemblePredictor:
    """
    سیستم Ensemble برای بهبود دقت پیشبینی
    """
    
    def __init__(self, use_xgboost: bool = False, use_lightgbm: bool = False,
                 use_catboost: bool = False, voting: str = 'soft'):
        """
        Parameters:
        -----------
        voting: 'soft' (میانگین احتمالات) یا 'hard' (اکثریت رای)
        """
        self.use_xgboost = use_xgboost and HAS_XGBOOST
        self.use_lightgbm = use_lightgbm and HAS_LIGHTGBM
        self.use_catboost = use_catboost and HAS_CATBOOST
        self.voting = voting
        self.ensemble = None
        self.scaler = None
        
        self._build_ensemble()
    
    def _build_ensemble(self):
        """ساخت مدلهای ensemble"""
        models = []
        
        # ۱. Random Forest (Base)
        models.append(('rf', RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=20,
            class_weight='balanced', random_state=42, n_jobs=-1
        )))
        
        # ۲. Gradient Boosting
        models.append(('gb', GradientBoostingClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.1,
            subsample=0.8, random_state=42
        )))
        
        # ۳. XGBoost (اگر موجود باشد)
        if self.use_xgboost:
            models.append(('xgb', xgb.XGBClassifier(
                n_estimators=200, max_depth=5, learning_rate=0.1,
                subsample=0.8, colsample_bytree=0.8,
                scale_pos_weight=1, random_state=42, n_jobs=-1, verbosity=0
            )))
        
        # ۴. LightGBM (اگر موجود باشد)
        if self.use_lightgbm:
            models.append(('lgb', lgb.LGBMClassifier(
                n_estimators=200, max_depth=5, learning_rate=0.1,
                num_leaves=31, subsample=0.8, colsample_bytree=0.8,
                random_state=42, n_jobs=-1, verbose=-1
            )))
        
        # ۵. CatBoost (اگر موجود باشد)
        if self.use_catboost:
            models.append(('cat', cb.CatBoostClassifier(
                iterations=200, depth=5, learning_rate=0.1,
                subsample=0.8, random_state=42, verbose=False
            )))
        
        # ۶. Logistic Regression (برای diversity)
        models.append(('lr', LogisticRegression(
            max_iter=1000, random_state=42, n_jobs=-1
        )))
        
        print(f"🔨 Ensemble ساخت شد: {len(models)} مدل")
        for name, _ in models:
            print(f"   • {name}")
        
        self.ensemble = VotingClassifier(
            estimators=models,
            voting=self.voting,
            n_jobs=-1
        )
    
    def fit(self, X_train: np.ndarray, y_train: np.ndarray, 
            X_val: np.ndarray = None, y_val: np.ndarray = None):
        """
        آموزش Ensemble
        """
        print("\n🧠 آموزش Ensemble (ممکن است کمی طول بکشد)...")
        
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        self.ensemble.fit(X_train_scaled, y_train)
        
        print("✅ آموزش تکمیل شد")
        
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            score = self.ensemble.score(X_val_scaled, y_val)
            print(f"   دقت روی Validation: {score:.4f}")
        
        return self
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """پیشبینی احتمالات"""
        X_scaled = self.scaler.transform(X)
        return self.ensemble.predict_proba(X_scaled)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """پیشبینی کلاس"""
        X_scaled = self.scaler.transform(X)
        return self.ensemble.predict(X_scaled)
    
    def feature_importance_from_rf(self) -> dict:
        """استخراج Feature Importance از مدل Random Forest"""
        for name, estimator in self.ensemble.estimators_:
            if name == 'rf':
                return dict(zip(range(len(estimator.feature_importances_)),
                               estimator.feature_importances_))
        return {}
