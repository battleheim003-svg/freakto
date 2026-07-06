"""
model_train_final_Version2.py - آموزش مدل نهایی (فاز چهارم - Optimized)
برای WunderTrading

اجرا: python model_train_final_Version2.py
"""

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from config import MODEL_PATH, TRAINING_CANDLES, EXCHANGE_ID
from data_fetcher import fetch_ohlcv_extended
from features import add_features, add_labels, FEATURE_COLUMNS


def train_final():
    """آموزش مدل نهایی"""
    
    print("\n" + "=" * 100)
    print("🎯 آموزش مدل نهایی (فاز چهارم - Optimized)")
    print("=" * 100)
    print(f"📱 صرافی: {EXCHANGE_ID.upper()}")
    print(f"💱 نماد: BTC/USDT")
    print(f"⏱️ تایمفریم: 4h")
    print(f"📊 تعداد کندل: {TRAINING_CANDLES}")
    print("=" * 100 + "\n")
    
    # ========== مرحله 1: دریافت داده ==========
    print("📥 مرحله 1: دریافت داده")
    print("-" * 100)
    
    try:
        print(f"در حال دریافت {TRAINING_CANDLES} کندل از {EXCHANGE_ID.upper()}...")
        raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
        print(f"✅ دریافت موفق: {len(raw)} کندل")
        
        if len(raw) == 0:
            print("❌ هیچ داده‌ای دریافت نشد!")
            return
        
        print(f"   تاریخ شروع: {raw.index[0]}")
        print(f"   تاریخ پایان: {raw.index[-1]}")
        
    except Exception as e:
        print(f"❌ خطا در دریافت داده: {e}")
        print("\nلطفاً بررسی کنید:")
        print("  • اتصال اینترنت فعال است")
        print("  • API Key صحیح است")
        print("  • WunderTrading در دسترس است")
        return
    
    # ========== مرحله 2: ساخت فیچرها ==========
    print("\n🔨 مرحله 2: ساخت فیچرها")
    print("-" * 100)
    
    print("در حال محاسبهی اندیکاتورها...")
    dataset = add_features(raw)
    print(f"✅ فیچرهای اساسی ساخته شدند")
    
    print("در حال اضافه‌کردن لیبل‌ها...")
    dataset = add_labels(dataset)
    print(f"✅ لیبل‌ها ساخته شدند")
    
    print("در حال حذف ردیفهای ناقص...")
    dataset = dataset.dropna(subset=FEATURE_COLUMNS + ['label'])
    print(f"✅ ردیفهای ناقص حذف شدند")
    print(f"   ردیفهای موجود: {len(dataset)}")
    print(f"   فیچرها: {len(FEATURE_COLUMNS)}")
    
    # ========== مرحله 3: بررسی توزیع کلاسها ==========
    print("\n📊 مرحله 3: توزیع کلاسها")
    print("-" * 100)
    
    label_dist = dataset['label'].value_counts(normalize=True).sort_index()
    total_samples = len(dataset)
    
    for cls in sorted(label_dist.keys()):
        frac = label_dist[cls]
        count = int(frac * total_samples)
        name = {1: '✅ خرید (1)', -1: '❌ فروش (-1)', 0: '○ خنثی (0)'}.get(cls, f'Unknown ({cls})')
        bar = '█' * int(frac * 50)
        percentage = frac * 100
        print(f"  {name:20} {count:6d} ({percentage:6.2f}%) {bar}")
    
    print(f"\n  کل: {total_samples} نمونه")
    
    # بررسی Class Imbalance
    neutral_pct = label_dist.get(0, 0) * 100
    if neutral_pct > 80:
        print(f"\n  ⚠️ هشدار: {neutral_pct:.1f}% داده خنثی است")
        print("     این ممکن است منجر به مدلی شود که فقط خنثی پیشبینی می‌کند")
    
    # ========== مرحله 4: تقسیم داده ==========
    print("\n📋 مرحله 4: تقسیم داده (Train/Test)")
    print("-" * 100)
    
    split_idx = int(len(dataset) * 0.8)
    train_data = dataset.iloc[:split_idx]
    test_data = dataset.iloc[split_idx:]
    
    X_train = train_data[FEATURE_COLUMNS].values
    y_train = train_data['label'].values
    X_test = test_data[FEATURE_COLUMNS].values
    y_test = test_data['label'].values
    
    print(f"Train Set:")
    print(f"  • تعداد: {len(X_train)} ({len(X_train)/len(dataset)*100:.1f}%)")
    print(f"  • از: {train_data.index[0]} تا {train_data.index[-1]}")
    print(f"\nTest Set:")
    print(f"  • تعداد: {len(X_test)} ({len(X_test)/len(dataset)*100:.1f}%)")
    print(f"  • از: {test_data.index[0]} تا {test_data.index[-1]}")
    
    # ========== مرحله 5: Scaling ==========
    print("\n⚙️ مرحله 5: نرمال‌سازی (Scaling)")
    print("-" * 100)
    
    print("در حال نرمال‌سازی داده...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("✅ نرمال‌سازی تکمیل شد")
    
    # ========== مرحله 6: آموزش مدل ==========
    print("\n🧠 مرحله 6: آموزش مدل")
    print("-" * 100)
    
    print("مشخصات مدل:")
    print("  • الگوریتم: Random Forest Classifier")
    print("  • تعداد درختان: 300")
    print("  • عمق حداکثر: 6")
    print("  • حداقل نمونه برای شاخه: 20")
    print("  • تعادل کلاسها: فعال")
    
    print("\nدر حال آموزش...")
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=20,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1,
    )
    
    try:
        model.fit(X_train_scaled, y_train)
        print("✅ آموزش تکمیل شد")
    except Exception as e:
        print(f"❌ خطا در آموزش: {e}")
        return
    
    # ========== مرحله 7: ارزیابی روی Test Set ==========
    print("\n" + "=" * 100)
    print("📊 مرحله 7: ارزیابی نتایج")
    print("=" * 100 + "\n")
    
    # پیشبینی
    y_pred = model.predict(X_test_scaled)
    
    print("Classification Report (Out-of-Sample):")
    print("-" * 100)
    print(classification_report(
        y_test, 
        y_pred, 
        target_names=['فروش (-1)', 'خنثی (0)', 'خرید (1)'],
        zero_division=0
    ))
    
    # Accuracy
    accuracy = (y_pred == y_test).mean()
    print(f"\nAccuracy: {accuracy*100:.2f}%")
    
    # AUC Score
    print("\n" + "-" * 100)
    print("AUC Scores (هرچه بالاتر بهتر - 0.50 = شانس، 1.0 = کامل):")
    print("-" * 100 + "\n")
    
    proba = model.predict_proba(X_test_scaled)
    classes = model.classes_
    class_to_idx = {c: i for i, c in enumerate(classes)}
    
    auc_scores = {}
    
    for target_cls in [1, -1]:
        if target_cls in classes:
            idx = class_to_idx[target_cls]
            y_binary = (y_test == target_cls).astype(int)
            
            if y_binary.sum() > 0 and y_binary.sum() < len(y_test):
                try:
                    auc = roc_auc_score(y_binary, proba[:, idx])
                    auc_scores[target_cls] = auc
                    
                    name = 'خرید (1)' if target_cls == 1 else 'فروش (-1)'
                    
                    if auc > 0.55:
                        status = "✅ خوب"
                    elif auc > 0.50:
                        status = "〰️ متوسط"
                    else:
                        status = "❌ ضعیف"
                    
                    print(f"  {name:20} AUC: {auc:.4f}  {status}")
                except:
                    pass
    
    # میانگین AUC
    if auc_scores:
        avg_auc = np.mean(list(auc_scores.values()))
        print(f"\n  میانگین AUC: {avg_auc:.4f}")
        
        if avg_auc > 0.55:
            print("\n  ✅ نتایج خوب هستند!")
        elif avg_auc > 0.50:
            print("\n  〰️ نتایج متوسط هستند")
        else:
            print("\n  ❌ نتایج ضعیف هستند")
    
    # ========== مرحله 8: Feature Importance ==========
    print("\n" + "=" * 100)
    print("🎯 مرحله 8: اهمیت فیچرها")
    print("=" * 100 + "\n")
    
    feature_importance = dict(zip(FEATURE_COLUMNS, model.feature_importances_))
    top_10 = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("10 فیچر برتر (بر اساس اهمیت):\n")
    print(f"{'#':<3} {'فیچر':<25} {'اهمیت':<12} {'نمودار'}")
    print("-" * 100)
    
    for i, (feat, imp) in enumerate(top_10, 1):
        bar = '█' * int(imp * 100)
        print(f"{i:<3} {feat:<25} {imp:.4f}{'':<7} {bar}")
    
    # ========== مرحله 9: ذخیره مدل ==========
    print("\n" + "=" * 100)
    print("💾 مرحله 9: ذخیره مدل")
    print("=" * 100 + "\n")
    
    train_end_timestamp = dataset.index[split_idx - 1]
    
    model_bundle = {
        'model': model,
        'scaler': scaler,
        'feature_columns': FEATURE_COLUMNS,
        'feature_importance': feature_importance,
        'train_end_timestamp': train_end_timestamp,
        'use_advanced': False,
        'phase': 'phase4_optimized',
        'exchange': EXCHANGE_ID,
    }
    
    try:
        joblib.dump(model_bundle, MODEL_PATH)
        print(f"✅ مدل با موفقیت ذخیره شد")
        print(f"\n   📁 فایل: {MODEL_PATH}")
        print(f"   🏷️ نام: model.joblib")
        print(f"   📊 Phase: phase4_optimized")
        print(f"   📱 Exchange: {EXCHANGE_ID.upper()}")
        print(f"   🔀 Train/Test Split: {train_end_timestamp}")
    except Exception as e:
        print(f"❌ خطا در ذخیره‌سازی: {e}")
        return
    
    # ========== خلاصه نهایی ==========
    print("\n" + "=" * 100)
    print("✅ خلاصهی نهایی")
    print("=" * 100 + "\n")
    
    print("مشخصات مدل:")
    print(f"  • کل داده: {len(dataset)} کندل")
    print(f"  • داده آموزشی: {len(X_train)}")
    print(f"  • داده تستی: {len(X_test)}")
    print(f"  • تعداد فیچرها: {len(FEATURE_COLUMNS)}")
    print(f"  • درختان تصمیم: 300")
    
    print(f"\nعملکرد:")
    print(f"  • Accuracy: {accuracy*100:.2f}%")
    if auc_scores:
        print(f"  • AUC میانگین: {avg_auc:.4f}")
    
    print(f"\nاطلاعات مهم:")
    print(f"  • مرز Train/Test: {train_end_timestamp}")
    print(f"  • بازهی Test: از {test_data.index[0]} تا {test_data.index[-1]}")
    print(f"  • مدت Test: {(test_data.index[-1] - test_data.index[0]).days} روز")
    
    print("\n" + "=" * 100)
    print("🚀 مدل آماده است!")
    print("=" * 100)
    
    print("\nقدم بعدی:")
    print("  1. بکتست: python backtest_final_complete.py")
    print("  2. Live Trading: python main.py")
    print("\n")


if __name__ == '__main__':
    train_final()