"""
diagnosis_phase4.py - تشخیص root cause مشکل

مسائل احتمالی:
1. Class Imbalance شدید (بیشتر داده کلاس 0)
2. لیبل‌های ضعیف یا تصادفی
3. Forward Bias در لیبل‌گذاری
4. Feature Scale/Normalization مشکل
5. OHLCV Data Quality مشکل
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

from config import TRAINING_CANDLES, LOOKAHEAD_CANDLES, ATR_MULTIPLIER
from data_fetcher import fetch_ohlcv_extended
from features_integrated import build_integrated_dataset, get_all_feature_columns


def diagnose_labels():
    """تشخیص مشکل لیبل‌ها"""
    print("=" * 100)
    print("🔍 تشخیص مشکل لیبل‌ها")
    print("=" * 100)
    
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    dataset = build_integrated_dataset(raw, for_training=True, use_advanced=False)
    
    # ۱. توزیع کلاسها
    print("\n📊 توزیع کلاسها:")
    label_dist = Counter(dataset['label'].values)
    total = len(dataset)
    
    for cls in sorted(label_dist.keys()):
        count = label_dist[cls]
        pct = (count / total) * 100
        name = {1: '✓ خرید', -1: '✗ فروش', 0: '○ خنثی'}.get(cls, str(cls))
        bar = '█' * int(pct / 2)
        print(f"  {name:12} {count:6d} ({pct:5.2f}%) {bar}")
    
    # بررسی Class Imbalance
    if label_dist.get(0, 0) > total * 0.8:
        print("\n❌ CLASS IMBALANCE شدید: بیشتر 80% داده neutral است!")
        print("   نتیجه: مدل تنها برای پیشبینی 0 آموزش میبینه")
    
    # ۲. بررسی Future Return
    print("\n\n📈 بررسی Future Return:")
    print(f"  میانگین: {dataset['future_return'].mean() * 100:.4f}%")
    print(f"  std: {dataset['future_return'].std() * 100:.4f}%")
    print(f"  min: {dataset['future_return'].min() * 100:.4f}%")
    print(f"  max: {dataset['future_return'].max() * 100:.4f}%")
    
    # ۳. بررسی ATR_MULTIPLIER
    print("\n\n🎯 بررسی آستانهی لیبل‌گذاری (ATR_MULTIPLIER):")
    atr_threshold = dataset['atr_pct'].mean() * ATR_MULTIPLIER
    print(f"  ATR میانگین: {dataset['atr_pct'].mean() * 100:.4f}%")
    print(f"  آستانهی لیبل: {atr_threshold * 100:.4f}%")
    print(f"  LOOKAHEAD_CANDLES: {LOOKAHEAD_CANDLES}")
    
    # چند درصد از future_return ها از آستانه بزرگتر هستند؟
    above_threshold = (dataset['future_return'].abs() > atr_threshold).sum()
    pct_above = (above_threshold / len(dataset)) * 100
    print(f"  درصد برای لیبل غیر-0: {pct_above:.2f}%")
    
    if pct_above < 15:
        print("\n  ❌ آستانه خیلی بالا است! بیشتر کندلها neutral میشوند")
        print(f"     پیشنهاد: ATR_MULTIPLIER را از {ATR_MULTIPLIER} کاهش بده")
    
    # ۴. تحلیل Sequential Patterns
    print("\n\n📊 الگوهای Sequential:")
    label_array = dataset['label'].values
    transitions = {
        '-1→0': 0, '-1→1': 0, '0→-1': 0, '0→1': 0, '1→-1': 0, '1→0': 0
    }
    
    for i in range(len(label_array) - 1):
        trans = f"{int(label_array[i])}→{int(label_array[i+1])}"
        if trans in transitions:
            transitions[trans] += 1
    
    print("  انتقالات کلاس:")
    for trans, count in sorted(transitions.items()):
        pct = (count / (len(label_array) - 1)) * 100
        print(f"    {trans}: {count:5d} ({pct:5.2f}%)")
    
    # ۵. بررسی Price Action Quality
    print("\n\n🔍 کیفیت OHLCV Data:")
    
    # چک High > Low
    bad_ohlc = ((dataset['high'] < dataset['low']).sum())
    print(f"  High < Low: {bad_ohlc} (باید 0 باشد)")
    
    # چک Close بین Open و High/Low
    bad_close = (
        ((dataset['close'] < dataset['low']) | (dataset['close'] > dataset['high'])).sum()
    )
    print(f"  Close خارج از [Low, High]: {bad_close} (باید 0 باشد)")
    
    # تغییرات شدید
    pct_change = dataset['close'].pct_change().abs()
    extreme_moves = (pct_change > 0.05).sum()  # > 5%
    print(f"  حرکات > 5%: {extreme_moves} ({(extreme_moves/len(dataset)*100):.2f}%)")
    
    # ۶. Feature Statistics
    print("\n\n📊 آمار فیچرها:")
    feature_cols = get_all_feature_columns(use_advanced=False)
    
    for feat in ['rsi_14', 'macd_diff', 'atr_pct', 'volatility'][:4]:
        if feat in dataset.columns:
            vals = dataset[feat].dropna()
            print(f"  {feat}:")
            print(f"    mean: {vals.mean():.4f}, std: {vals.std():.4f}")
            print(f"    min: {vals.min():.4f}, max: {vals.max():.4f}")
    
    return dataset


def diagnose_feature_quality(dataset):
    """تشخیص کیفیت فیچرها"""
    print("\n\n" + "=" * 100)
    print("🔍 تشخیص کیفیت فیچرها")
    print("=" * 100)
    
    feature_cols = get_all_feature_columns(use_advanced=False)
    
    # ۱. Missing Values
    print("\n📊 Missing Values:")
    missing = dataset[feature_cols].isnull().sum()
    missing_pct = (missing / len(dataset)) * 100
    
    bad_features = missing_pct[missing_pct > 5]
    if len(bad_features) > 0:
        print("  ❌ فیچرهایی با >5% missing:")
        for feat, pct in bad_features.items():
            print(f"    {feat}: {pct:.2f}%")
    else:
        print("  ✅ تمام فیچرها خوب تکمیل هستند")
    
    # ۲. Constant Features
    print("\n📊 Constant Features (بدون variance):")
    for feat in feature_cols[:10]:  # چک اول 10
        if feat in dataset.columns:
            unique = dataset[feat].nunique()
            if unique < 5:
                print(f"  ⚠️ {feat}: فقط {unique} مقدار مختلف")
    
    # ۳. Correlation with Label
    print("\n📊 Correlation با Label:")
    label = dataset['label'].values
    
    correlations = {}
    for feat in feature_cols[:15]:
        if feat in dataset.columns:
            feat_vals = dataset[feat].dropna().values
            label_vals = label[:len(feat_vals)]
            
            if len(feat_vals) > 1:
                corr = np.corrcoef(feat_vals, label_vals)[0, 1]
                correlations[feat] = corr
    
    sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
    for feat, corr in sorted_corr[:10]:
        strength = "قوی" if abs(corr) > 0.3 else "متوسط" if abs(corr) > 0.1 else "ضعیف"
        print(f"  {feat:<20} {corr:+.4f} ({strength})")
    
    if all(abs(c) < 0.05 for _, c in sorted_corr):
        print("\n  ❌ هیچ فیچری با Label ارتباط معنی‌داری ندارد!")


def suggest_fixes():
    """پیشنهادهای حل"""
    print("\n\n" + "=" * 100)
    print("💡 پیشنهادهای حل مشکل")
    print("=" * 100)
    
    print("""
1️⃣ کاهش ATR_MULTIPLIER:
   از 1.0 به 0.5 یا 0.3 کاهش بده تا بیشتر کندلها non-zero label بگیرند

2️⃣ استفاده از Triple Barrier:
   بجای threshold ثابت، از triple barrier استفاده کن
   (SL/TP واقعی، نه صرفاً future_return)

3️⃣ تعادل کلاسها:
   SMOTE یا class_weight استفاده کن

4️⃣ تفریق معاملات بازار:
   فیچرهای regime-based (عادی vs pump)

5️⃣ دادهی بیشتر:
   TRAINING_CANDLES را تا 15000 افزایش بده

6️⃣ Feature Engineering عمیق‌تر:
   Order Flow, On-Chain Data, Sentiment
    """)


if __name__ == '__main__':
    dataset = diagnose_labels()
    diagnose_feature_quality(dataset)
    suggest_fixes()
