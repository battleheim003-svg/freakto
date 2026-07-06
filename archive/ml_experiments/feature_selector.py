"""
feature_selector.py - انتخاب خودکار بهترین فیچرها

روشها:
1. Permutation Importance - کدام فیچر بیشتر تأثیر دارد؟
2. Correlation Analysis - کدام فیچرها خود‌همبسته اند؟
3. Mutual Information - کدام فیچرها بیشترین اطلاع دارند؟
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.inspection import permutation_importance
from sklearn.feature_selection import mutual_info_classif
import warnings
warnings.filterwarnings('ignore')


class FeatureSelector:
    """انتخاب خودکار فیچرهای بهترین"""
    
    def __init__(self, max_features: int = 30, method: str = 'permutation'):
        """
        Parameters:
        -----------
        max_features: حداکثر تعداد فیچرهایی که نگاه داریم
        method: 'permutation' یا 'mutual_info' یا 'correlation'
        """
        self.max_features = max_features
        self.method = method
        self.selected_features = None
        self.importance_scores = None
    
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list,
            X_test: np.ndarray = None, y_test: np.ndarray = None):
        """
        محاسبهی اهمیت فیچرها و انتخاب بهترین‌ها
        """
        print(f"🔍 انتخاب فیچرها با روش: {self.method}")
        
        if self.method == 'permutation' and X_test is not None:
            importance_scores = self._permutation_importance(
                X, y, X_test, y_test, feature_names
            )
        elif self.method == 'mutual_info':
            importance_scores = self._mutual_information(X, y, feature_names)
        elif self.method == 'correlation':
            importance_scores = self._correlation_based(X, y, feature_names)
        else:
            raise ValueError(f"روش نامعلوم: {self.method}")
        
        # انتخاب top N
        self.importance_scores = importance_scores
        top_idx = np.argsort(importance_scores)[-self.max_features:][::-1]
        self.selected_features = [feature_names[i] for i in top_idx]
        
        print(f"✅ {len(self.selected_features)} فیچر انتخاب شد\n")
        
        return self.selected_features
    
    def _permutation_importance(self, X, y, X_test, y_test, feature_names):
        """
        اهمیت Permutation:
        هر فیچر را random shuffle میکنیم و میبینیم مدل چقدر بدتر میشود
        """
        # مدل سریع برای محاسبهی اهمیت
        model = RandomForestClassifier(
            n_estimators=100, max_depth=5, random_state=42, n_jobs=-1
        )
        model.fit(X, y)
        
        perm_importance = permutation_importance(
            model, X_test, y_test, n_repeats=10, random_state=42
        )
        
        return perm_importance.importances_mean
    
    def _mutual_information(self, X, y, feature_names):
        """
        Mutual Information:
        هر فیچر چقدر اطلاعات درباره لیبل میدهد؟
        """
        mi_scores = mutual_info_classif(X, y, random_state=42)
        return mi_scores
    
    def _correlation_based(self, X, y, feature_names):
        """
        Correlation:
        هر فیچر چقدر با لیبل همبسته است؟
        """
        correlations = np.abs([
            np.corrcoef(X[:, i], y)[0, 1] if not np.isnan(np.corrcoef(X[:, i], y)[0, 1]) else 0
            for i in range(X.shape[1])
        ])
        return correlations
    
    def print_summary(self):
        """چاپ خلاصهی فیچرهای انتخاب‌شده"""
        if self.importance_scores is None:
            print("⚠️ ابتدا fit() را فراخوانی کن")
            return
        
        print("=" * 80)
        print("📊 بهترین فیچرهای انتخاب‌شده")
        print("=" * 80)
        
        for i, feat in enumerate(self.selected_features, 1):
            importance = self.importance_scores[i-1]
            print(f"{i:2d}. {feat:<40} (اهمیت: {importance:.4f})")
        
        print(f"\nکل: {len(self.selected_features)} فیچر از {len(self.importance_scores)}")
