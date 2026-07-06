"""
backtest_final_complete.py - بکتست نهایی (ورژن کار کردن)

مشکل قبلی: future_return را خود محاسبه نمی‌کردیم
حل: ساخت future_return داخل کد
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
import warnings
warnings.filterwarnings('ignore')

from config import MODEL_PATH, TRAINING_CANDLES, MIN_CONFIDENCE, LOOKAHEAD_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import add_features, FEATURE_COLUMNS

FEE_RATE = 0.001


def backtest():
    """بکتست نهایی - ورژن تکمیل‌شده"""
    
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
        print(f"   فیچرها: {len(feature_cols)}")
    
    except FileNotFoundError:
        print(f"❌ مدل یافت نشد: {MODEL_PATH}")
        print("ابتدا python model_train_final_Version2.py را اجرا کن")
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
    
    # ۵. محاسبهی future_return (مهم!)
    print("\n📊 محاسبهی future_return...")
    dataset['future_return'] = dataset['close'].shift(-LOOKAHEAD_CANDLES) / dataset['close'] - 1
    dataset = dataset.dropna(subset=['future_return'])
    print(f"✓ {len(dataset)} ردیف با future_return")
    
    # ۶. پیشبینی
    print("\n🔮 پیشبینی...")
    X = scaler.transform(dataset[feature_cols].values)
    proba = model.predict_proba(X)
    classes = model.classes_
    
    dataset_copy = dataset.copy()
    for i, c in enumerate(classes):
        dataset_copy[f'proba_{c}'] = proba[:, i]
    
    # ۷. تشخیص سیگنال
    print(f"🎯 تشخیص سیگنالها (MIN_CONFIDENCE = {MIN_CONFIDENCE})...")
    
    def decide(row):
        proba_buy = row.get('proba_1', 0) if 1 in classes else 0
        proba_sell = row.get('proba_-1', 0) if -1 in classes else 0
        
        if proba_buy >= MIN_CONFIDENCE:
            return 1
        if proba_sell >= MIN_CONFIDENCE:
            return -1
        return 0
    
    dataset_copy['signal'] = dataset_copy.apply(decide, axis=1)
    
    # ۸. محاسبهی معاملات
    trades = dataset_copy[dataset_copy['signal'] != 0].copy()
    
    if len(trades) > 0:
        trades['strategy_return'] = trades['signal'] * trades['future_return'] - FEE_RATE
    
    # ۹. گزارش
    print("\n" + "=" * 100)
    print("📊 نتایج بکتست")
    print("=" * 100)
    
    total_trades = len(trades)
    
    print(f"\n📈 Statistics:")
    print(f"  کندلهای بررسی‌شده: {len(dataset_copy):,}")
    print(f"  سیگنالهای صادرشده: {total_trades}")
    
    if total_trades > 0:
        # بازده
        win_count = (trades['strategy_return'] > 0).sum()
        win_rate = win_count / total_trades
        avg_return = trades['strategy_return'].mean()
        cumulative = (1 + trades['strategy_return']).prod() - 1
        
        print(f"\n💹 Performance:")
        print(f"  Win Rate: {win_rate * 100:.2f}% ({win_count}/{total_trades})")
        print(f"  میانگین بازده: {avg_return * 100:.3f}%")
        print(f"  بازده تجمعی: {cumulative * 100:.2f}%")
        
        # Profit Factor
        wins = trades['strategy_return'][trades['strategy_return'] > 0].sum()
        losses = abs(trades['strategy_return'][trades['strategy_return'] < 0].sum())
        pf = wins / losses if losses > 0 else np.inf
        print(f"  Profit Factor: {pf:.2f}")
        
        # توزیع سیگنالها
        print(f"\n📊 توزیع سیگنالها:")
        buy_signals = (trades['signal'] == 1).sum()
        sell_signals = (trades['signal'] == -1).sum()
        print(f"  خرید (1): {buy_signals} ({buy_signals/total_trades*100:.1f}%)")
        print(f"  فروش (-1): {sell_signals} ({sell_signals/total_trades*100:.1f}%)")
        
        # توزیع بازدهها
        print(f"\n📈 توزیع بازدهها:")
        print(f"  میانگین: {trades['strategy_return'].mean()*100:.3f}%")
        print(f"  میانه: {trades['strategy_return'].median()*100:.3f}%")
        print(f"  max: {trades['strategy_return'].max()*100:.3f}%")
        print(f"  min: {trades['strategy_return'].min()*100:.3f}%")
        print(f"  std: {trades['strategy_return'].std()*100:.3f}%")
    
    else:
        print(f"\n⚠️ هیچ سیگنالی صادر نشد")
        print(f"پیشنهاد: کاهش MIN_CONFIDENCE از {MIN_CONFIDENCE}")
        
        # چک کن چه احتمالات داریم
        print(f"\nتوزیع احتمالات:")
        for cls in classes:
            max_proba = dataset_copy[f'proba_{cls}'].max()
            print(f"  کلاس {cls}: بیشترین احتمال = {max_proba:.4f}")
    
    # ۱۰. نتیجه‌گیری
    print("\n" + "=" * 100)
    print("💡 نتیجه‌گیری و توصیهات")
    print("=" * 100)
    
    if total_trades == 0:
        print("\n⚠️ MIN_CONFIDENCE خیلی سختگیرانه است")
        print(f"پیشنهاد: کاهش MIN_CONFIDENCE از {MIN_CONFIDENCE} به 0.50")
        print("\nدستور:")
        print("  1. در config.py تغییر بده: MIN_CONFIDENCE = 0.50")
        print("  2. دوباره اجرا کن: python backtest_final_complete.py")
    
    elif total_trades < 10:
        print(f"\n⚠️ تعداد سیگنال کم است ({total_trades})")
        print("پیشنهاد: کاهش MIN_CONFIDENCE")
    
    elif cumulative > 0 and win_rate > 0.45:
        print(f"\n✅ نتایج رضایت‌بخش هستند!")
        print(f"   بازده: {cumulative*100:.2f}%")
        print(f"   Win Rate: {win_rate*100:.2f}%")
        print("\nقدم بعدی:")
        print("  1. Live trading می‌توانی شروع کنی")
        print("  2. یا بهینه‌سازی بیشتر با: python walk_forward_optimization_final_Version2.py")
    
    else:
        print(f"\n❌ نتایج منفی هستند")
        print(f"   بازده: {cumulative*100:.2f}%")
        print("\nنیاز به:")
        print("  1. فیچرهای جدید (On-Chain, Sentiment)")
        print("  2. یا تغییر استراتژی")
    
    return {
        'n_trades': total_trades,
        'win_rate': win_rate if total_trades > 0 else 0,
        'avg_return': avg_return if total_trades > 0 else 0,
        'cumulative_return': cumulative if total_trades > 0 else 0,
    }


if __name__ == '__main__':
    backtest()
