"""
backtest_final.py - بکتست نهایی با مدل بهینه‌شده

خصوصیات:
- استفاده از مدل جدید (phase4_optimized)
- پارامترهای بهینه
- گزارش جزیی
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
import warnings
warnings.filterwarnings('ignore')

from config import MODEL_PATH, TRAINING_CANDLES, MIN_CONFIDENCE
from data_fetcher import fetch_ohlcv_extended
from features import add_features, FEATURE_COLUMNS

FEE_RATE = 0.001


def backtest():
    """بکتست نهایی"""
    
    print("=" * 100)
    print("🧪 بکتست نهایی - مدل بهینه‌شده")
    print("=" * 100)
    
    # ۱. بارگذاری مدل
    try:
        bundle = joblib.load(MODEL_PATH)
        model = bundle['model']
        scaler = bundle['scaler']
        feature_cols = bundle.get('feature_columns', FEATURE_COLUMNS)
        train_end_timestamp = bundle.get('train_end_timestamp')
        
        print(f"\n✅ مدل بارگذاری شد: {MODEL_PATH}")
        print(f"   Phase: {bundle.get('phase', 'unknown')}")
        print(f"   فیچرها: {len(feature_cols)}")
    
    except FileNotFoundError:
        print(f"❌ مدل یافت نشد: {MODEL_PATH}")
        print("ابتدا python model_train_final.py را اجرا کن")
        return
    
    # ۲. دریافت داده
    print(f"\n📥 دریافت {TRAINING_CANDLES} کندل...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    
    # ۳. ساخت فیچرها
    print("🔨 ساخت فیچرها...")
    dataset = add_features(raw)
    dataset = dataset.dropna(subset=feature_cols)
    
    if len(dataset) < 30:
        print("❌ دادهی کافی برای بکتست وجود ندارد")
        return
    
    # ۴. فیلتر کردن بر اساس train_end_timestamp
    if train_end_timestamp is not None:
        before = len(dataset)
        dataset = dataset[dataset.index > train_end_timestamp]
        print(f"✓ فقط داده بعد از {train_end_timestamp}")
        print(f"  ({before} → {len(dataset)} کندل)")
    
    # ۵. پیشبینی
    print("\n🔮 پیشبینی...")
    X = scaler.transform(dataset[feature_cols].values)
    proba = model.predict_proba(X)
    classes = model.classes_
    
    dataset_copy = dataset.copy()
    for i, c in enumerate(classes):
        dataset_copy[f'proba_{c}'] = proba[:, i]
    
    # ۶. تشخیص سیگنال
    print(f"🎯 تشخیص سیگنالها (MIN_CONFIDENCE = {MIN_CONFIDENCE})...")
    
    def decide(row):
        if row.get('proba_1', 0) >= MIN_CONFIDENCE:
            return 1
        if row.get('proba_-1', 0) >= MIN_CONFIDENCE:
            return -1
        return 0
    
    dataset_copy['signal'] = dataset_copy.apply(decide, axis=1)
    
    # ۷. محاسبهی معاملات (فرض: future_return موجود است)
    trades = dataset_copy[dataset_copy['signal'] != 0].copy()
    
    if len(trades) > 0:
        trades['strategy_return'] = trades['signal'] * trades['future_return'] - FEE_RATE
    
    # ۸. گزارش
    print("\n" + "=" * 100)
    print("📊 نتایج بکتست")
    print("=" * 100)
    
    total_trades = len(trades)
    win_rate = (trades['strategy_return'] > 0).mean() if total_trades > 0 else 0
    avg_return = trades['strategy_return'].mean() if total_trades > 0 else 0
    cumulative = (1 + trades['strategy_return']).prod() - 1 if total_trades > 0 else 0
    
    print(f"\n📈 Statistics:")
    print(f"  کندلهای بررسی‌شده: {len(dataset_copy)}")
    print(f"  کندلهایی بدون سیگنال: {len(dataset_copy[dataset_copy['signal'] == 0])} "
          f"({len(dataset_copy[dataset_copy['signal'] == 0])/len(dataset_copy)*100:.1f}%)")
    print(f"  سیگنالهای صادرشده: {total_trades}")
    
    if total_trades > 0:
        print(f"\n💹 Performance:")
        print(f"  Win Rate: {win_rate * 100:.2f}% ({(trades['strategy_return'] > 0).sum()}/{total_trades})")
        print(f"  میانگین بازده: {avg_return * 100:.3f}%")
        print(f"  بازده تجمعی: {cumulative * 100:.2f}%")
        
        # AUC روی سیگنالها
        if total_trades > 10:
            try:
                y_up = (trades['label'] == 1).astype(int) if 'label' in trades.columns else None
                if y_up is not None and y_up.sum() > 0:
                    auc_up = roc_auc_score(y_up, trades['proba_1'].values)
                    print(f"  AUC (خرید): {auc_up:.4f}")
            except:
                pass
        
        # توزیع سیگنالها
        print(f"\n📊 توزیع سیگنالها:")
        buy_signals = (trades['signal'] == 1).sum()
        sell_signals = (trades['signal'] == -1).sum()
        print(f"  خرید (1): {buy_signals} ({buy_signals/total_trades*100:.1f}%)")
        print(f"  فروش (-1): {sell_signals} ({sell_signals/total_trades*100:.1f}%)")
    
    else:
        print("\n⚠️ هیچ سیگنالی صادر نشد")
    
    # ۹. نتیجه‌گیری
    print("\n" + "=" * 100)
    print("💡 نتیجه‌گیری")
    print("=" * 100)
    
    if total_trades == 0:
        print("⚠️ MIN_CONFIDENCE خیلی سختگیرانه است - هیچ سیگنالی صادر نشد")
        print(f"پیشنهاد: کاهش MIN_CONFIDENCE از {MIN_CONFIDENCE} به 0.50")
    elif cumulative > 0:
        print(f"✅ بازده مثبت: {cumulative*100:.2f}%")
        
        if win_rate > 0.5:
            print("✅ Win Rate بالا است (>50%)")
        else:
            print(f"⚠️ Win Rate پایین است ({win_rate*100:.1f}%)")
            print("   احتمالاً سیگنالها جهت دقیق ندارند")
    else:
        print(f"❌ بازده منفی: {cumulative*100:.2f}%")
        print("نیاز به بهینه‌سازی بیشتر یا فیچرهای جدید")
    
    return {
        'n_trades': total_trades,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'cumulative_return': cumulative,
    }


if __name__ == '__main__':
    backtest()
