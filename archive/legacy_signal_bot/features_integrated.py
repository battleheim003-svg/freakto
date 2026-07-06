"""
ترکیب فیچرهای اصلی (momentum/trend) با فیچرهای جدید
"""

import pandas as pd
from features import add_features, add_labels, FEATURE_COLUMNS
from advanced_features import build_advanced_dataset, ADVANCED_FEATURE_COLUMNS
from config_phase2 import ENABLED_ADVANCED_FEATURES


def build_integrated_dataset(
    df: pd.DataFrame,
    for_training: bool = True,
    funding_df: pd.DataFrame = None,
    oi_df: pd.DataFrame = None,
    liq_df: pd.DataFrame = None,
    use_advanced: bool = True
) -> pd.DataFrame:
    """
    ساخت دیتاست کامل: فیچرهای قدیمی + جدید
    """
    
    # فیچرهای اصلی (قدیمی)
    df = add_features(df)
    
    # فیچرهای پیشرفته (جدید)
    if use_advanced:
        df = build_advanced_dataset(
            df,
            funding_df=funding_df,
            oi_df=oi_df,
            liq_df=liq_df,
            enabled_features=ENABLED_ADVANCED_FEATURES
        )
    
    # لیبل‌ها (برای آموزش)
    if for_training:
        df = add_labels(df)
    
    # حذف NaN
    all_feature_cols = FEATURE_COLUMNS
    if use_advanced:
        all_feature_cols = all_feature_cols + [f for f in ADVANCED_FEATURE_COLUMNS 
                                                if f in df.columns]
    
    label_cols = ['label'] if for_training else []
    df = df.dropna(subset=all_feature_cols + label_cols)
    
    if for_training:
        df['label'] = df['label'].astype(int)
    
    return df


# لیست تمام فیچرهای موجود (برای مدل)
def get_all_feature_columns(use_advanced: bool = True) -> list:
    """بازگرداندن لیست کامل فیچرهای استفاده‌شده"""
    cols = list(FEATURE_COLUMNS)
    if use_advanced:
        cols.extend([f for f in ADVANCED_FEATURE_COLUMNS])
    return cols
