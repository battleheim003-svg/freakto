"""
test_oi_longshort_edge.py — آیا Open Interest و Long/Short Ratio سیگنال دارند؟

⚠️ محدودیت مهم: بایننس فقط ~30 روز تاریخچه‌ی رایگان برای این دو منبع می‌دهد.
یعنی نمونه‌ی این تست بسیار کوچک‌تر از تست‌های قبلی (که روی 4.5 سال داده انجام
شدند) خواهد بود. با یک تایم‌فریم 4 ساعته، 30 روز ≈ 180 کندل - این برای
walk-forward چندمرحله‌ای خیلی کم است، پس اینجا فقط یک تقسیم ساده‌ی
train/test انجام می‌دهیم و نتیجه را با احتیاط بیشتری تفسیر می‌کنیم.

نتیجه‌ی این تست را باید "شواهد اولیه‌ی محدود" در نظر بگیریم، نه جواب نهایی.
جواب نهایی و قابل‌اعتماد وقتی به دست می‌آید که چند هفته/ماه داده از
live_data_logger.py جمع شده باشد.

اجرا:
    python test_oi_longshort_edge.py
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

from config import SYMBOL, TIMEFRAME
from data_fetcher import fetch_ohlcv
from features import build_dataset, FEATURE_COLUMNS, OI_LONGSHORT_FEATURE_COLUMNS
from futures_data_fetcher import fetch_open_interest_history, fetch_long_short_ratio_history

# نگاشت TIMEFRAME پروژه به period مورد قبول endpoint های OI/Long-Short بایننس
TIMEFRAME_TO_PERIOD = {
    "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "12h": "12h", "1d": "1d",
}


def compute_auc(y_true, proba_up, proba_down):
    y_up = (y_true == 1).astype(int)
    y_down = (y_true == -1).astype(int)
    auc_up = roc_auc_score(y_up, proba_up) if 0 < y_up.sum() < len(y_up) else np.nan
    auc_down = roc_auc_score(y_down, proba_down) if 0 < y_down.sum() < len(y_down) else np.nan
    return auc_up, auc_down


def train_test_split_and_eval(dataset: pd.DataFrame, feature_cols: list, test_frac: float = 0.3):
    n = len(dataset)
    split_idx = int(n * (1 - test_frac))
    train, test = dataset.iloc[:split_idx], dataset.iloc[split_idx:]

    X_train = train[feature_cols].values
    y_train = train["label"].values
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = RandomForestClassifier(
        n_estimators=300, max_depth=5, min_samples_leaf=10,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)

    X_test = scaler.transform(test[feature_cols].values)
    proba = model.predict_proba(X_test)
    classes = list(model.classes_)
    proba_up = proba[:, classes.index(1)] if 1 in classes else np.zeros(len(test))
    proba_down = proba[:, classes.index(-1)] if -1 in classes else np.zeros(len(test))

    auc_up, auc_down = compute_auc(test["label"].values, proba_up, proba_down)
    return auc_up, auc_down, len(train), len(test)


def run():
    period = TIMEFRAME_TO_PERIOD.get(TIMEFRAME, "4h")
    symbol_futures = SYMBOL.replace("/", "")

    print("در حال دریافت داده‌ی قیمت اخیر (برای هماهنگی با بازه‌ی ۳۰ روزه‌ی OI/Long-Short)...")
    raw = fetch_ohlcv(limit=500)  # حداکثر ممکن، بعداً با بازه‌ی OI/Long-Short هم‌تراز می‌شود
    print(f"بازه‌ی قیمت دریافت‌شده: {raw.index[0]} تا {raw.index[-1]} ({len(raw)} کندل)")

    print("\nدر حال دریافت Open Interest (حداکثر تاریخچه‌ی موجود)...")
    oi_df = fetch_open_interest_history(symbol=symbol_futures, period=period, limit=500)
    print(f"تعداد رکورد OI: {len(oi_df)}"
          + (f" | بازه: {oi_df.index[0]} تا {oi_df.index[-1]}" if not oi_df.empty else ""))

    print("\nدر حال دریافت Long/Short Ratio (حداکثر تاریخچه‌ی موجود)...")
    ls_df = fetch_long_short_ratio_history(symbol=symbol_futures, period=period, limit=500)
    print(f"تعداد رکورد Long/Short: {len(ls_df)}"
          + (f" | بازه: {ls_df.index[0]} تا {ls_df.index[-1]}" if not ls_df.empty else ""))

    if oi_df.empty and ls_df.empty:
        print("\n⚠️ هیچ داده‌ای از OI یا Long/Short دریافت نشد. نمی‌توان تست را ادامه داد.")
        return

    # محدود کردن داده‌ی قیمت به بازه‌ای که OI/Long-Short هم برایش موجود است
    earliest_available = max(
        [d.index[0] for d in [oi_df, ls_df] if not d.empty]
    )
    raw = raw[raw.index >= earliest_available]
    print(f"\nبازه‌ی نهایی مشترک برای تحلیل: {raw.index[0]} تا {raw.index[-1]} ({len(raw)} کندل)")

    if len(raw) < 60:
        print("⚠️ تعداد کندل‌های مشترک خیلی کم است (<۶۰). نتیجه‌ی این تست عملاً غیرقابل‌اعتماد خواهد بود.")

    print("\nدر حال ساخت دیتاست پایه (بدون OI/Long-Short)...")
    dataset_base = build_dataset(raw, for_training=True)

    print("در حال ساخت دیتاست غنی‌شده (با OI/Long-Short)...")
    dataset_enriched = build_dataset(raw, for_training=True, oi_df=oi_df, longshort_df=ls_df)

    print(f"\nتعداد ردیف دیتاست پایه: {len(dataset_base)} | دیتاست غنی‌شده: {len(dataset_enriched)}")

    if len(dataset_enriched) < 40:
        print("\n⚠️ بعد از حذف NaN، تعداد ردیف کافی برای یک تقسیم train/test معنی‌دار باقی نمانده.")
        print("   پیشنهاد: صبر کن تا live_data_logger.py چند روز/هفته‌ی بیشتر داده جمع کند.")
        return

    print("\n" + "=" * 70)
    print("نتیجه (تقسیم ساده‌ی train/test، به‌دلیل حجم کم داده)")
    print("=" * 70)

    auc_up_base, auc_down_base, n_train_b, n_test_b = train_test_split_and_eval(dataset_base, FEATURE_COLUMNS)
    enriched_cols = FEATURE_COLUMNS + OI_LONGSHORT_FEATURE_COLUMNS
    auc_up_en, auc_down_en, n_train_e, n_test_e = train_test_split_and_eval(dataset_enriched, enriched_cols)

    print(f"\nمدل پایه       | آموزش: {n_train_b} | تست: {n_test_b} | AUC صعودی: {auc_up_base:.4f} | AUC نزولی: {auc_down_base:.4f}")
    print(f"مدل + OI/L-S   | آموزش: {n_train_e} | تست: {n_test_e} | AUC صعودی: {auc_up_en:.4f} | AUC نزولی: {auc_down_en:.4f}")
    print(f"تفاوت          | AUC صعودی: {auc_up_en - auc_up_base:+.4f} | AUC نزولی: {auc_down_en - auc_down_base:+.4f}")

    print("\n" + "=" * 70)
    print("جمع‌بندی (با احتیاط - نمونه کوچک است)")
    print("=" * 70)
    print(f"⚠️ این نتیجه فقط روی {n_test_e} کندل تست به‌دست آمده - نمونه‌ی بسیار کوچکی است.")
    print("   حتی اگر AUC بهتر به‌نظر برسد، ممکن است صرفاً نویز آماری باشد.")
    print("   نتیجه‌ی قابل‌اعتماد را باید بعد از تجمیع چند هفته/ماه داده از")
    print("   live_data_logger.py و اجرای دوباره‌ی یک تست walk-forward به‌دست آورد.")


if __name__ == "__main__":
    run()
