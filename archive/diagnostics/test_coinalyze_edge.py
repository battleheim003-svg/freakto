"""
test_coinalyze_edge.py — تست AUC با داده‌ی طولانی‌تر OI/Long-Short/Liquidation
(از Coinalyze، به‌جای فقط ۳۰ روز بایننس).

با این منبع، به‌جای ~۱۸۰ کندل تست (که در تست قبلی دیدیم غیرقابل‌اعتماد بود)،
به چیزی حدود ۱۵۰۰-۲۰۰۰ کندل (۸-۱۱ ماه) دسترسی داریم - که برای walk-forward
واقعی با چند دوره (fold) کافی است.

اجرا:
    python test_coinalyze_edge.py
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

from config import TRAIN_WINDOW_CANDLES, RETRAIN_STEP_CANDLES
from data_fetcher import fetch_ohlcv
from features import build_dataset, FEATURE_COLUMNS, OI_LONGSHORT_FEATURE_COLUMNS
from coinalyze_fetcher import (
    fetch_oi_history_coinalyze, fetch_long_short_ratio_history_coinalyze,
    fetch_liquidation_history_coinalyze, find_binance_perp_symbol,
)


def add_liquidation_feature(df: pd.DataFrame, liq_df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if liq_df is None or liq_df.empty:
        df["total_liquidations"] = 0.0
        return df
    liq_sorted = liq_df.sort_index()
    liq_sorted["total_liquidations"] = liq_sorted["liquidations_long"] + liq_sorted["liquidations_short"]
    df = pd.merge_asof(df.sort_index(), liq_sorted[["total_liquidations"]],
                        left_index=True, right_index=True, direction="backward")
    df["total_liquidations"] = df["total_liquidations"].fillna(0.0)
    return df


def train_and_predict_folds(dataset: pd.DataFrame, feature_cols: list):
    n = len(dataset)
    all_preds = []
    start = TRAIN_WINDOW_CANDLES

    # اگر داده کمتر از یک پنجره‌ی کامل باشد، پنجره را کوچک‌تر می‌کنیم تا حداقل
    # چند دوره برای تست داشته باشیم
    window = TRAIN_WINDOW_CANDLES
    if n < TRAIN_WINDOW_CANDLES + RETRAIN_STEP_CANDLES:
        window = max(int(n * 0.5), 60)
        start = window
        print(f"(داده کافی برای پنجره‌ی استاندارد نیست؛ پنجره‌ی آموزش به {window} کندل کاهش یافت)")

    while start + RETRAIN_STEP_CANDLES <= n:
        train_slice = dataset.iloc[start - window:start]
        test_slice = dataset.iloc[start:start + RETRAIN_STEP_CANDLES].copy()

        X_train = train_slice[feature_cols].values
        y_train = train_slice["label"].values
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        model = RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=15,
            class_weight="balanced", random_state=42, n_jobs=-1,
        )
        model.fit(X_train_scaled, y_train)

        X_test = scaler.transform(test_slice[feature_cols].values)
        proba = model.predict_proba(X_test)
        classes = list(model.classes_)
        for i, c in enumerate(classes):
            test_slice[f"proba_{c}"] = proba[:, i]
        if "proba_1" not in test_slice.columns:
            test_slice["proba_1"] = 0.0
        if "proba_-1" not in test_slice.columns:
            test_slice["proba_-1"] = 0.0

        all_preds.append(test_slice[["label", "proba_1", "proba_-1"]])
        start += RETRAIN_STEP_CANDLES

    return pd.concat(all_preds, ignore_index=True) if all_preds else pd.DataFrame()


def compute_auc(oos: pd.DataFrame):
    y_true = oos["label"].values
    y_up = (y_true == 1).astype(int)
    y_down = (y_true == -1).astype(int)
    auc_up = roc_auc_score(y_up, oos["proba_1"].values) if 0 < y_up.sum() < len(y_up) else np.nan
    auc_down = roc_auc_score(y_down, oos["proba_-1"].values) if 0 < y_down.sum() < len(y_down) else np.nan
    return auc_up, auc_down


def run():
    symbol = find_binance_perp_symbol()
    print(f"نماد Coinalyze شناسایی‌شده: {symbol}\n")

    print("در حال دریافت Open Interest (تا ~۱۱ ماه گذشته)...")
    oi_df = fetch_oi_history_coinalyze(days_back=330, symbol=symbol)
    print(f"تعداد رکورد OI: {len(oi_df)}"
          + (f" | بازه: {oi_df.index[0]} تا {oi_df.index[-1]}" if not oi_df.empty else ""))

    print("\nدر حال دریافت Long/Short Ratio...")
    ls_df = fetch_long_short_ratio_history_coinalyze(days_back=330, symbol=symbol)
    print(f"تعداد رکورد Long/Short: {len(ls_df)}"
          + (f" | بازه: {ls_df.index[0]} تا {ls_df.index[-1]}" if not ls_df.empty else ""))

    print("\nدر حال دریافت Liquidation History...")
    liq_df = fetch_liquidation_history_coinalyze(days_back=330, symbol=symbol)
    print(f"تعداد رکورد Liquidation: {len(liq_df)}"
          + (f" | بازه: {liq_df.index[0]} تا {liq_df.index[-1]}" if not liq_df.empty else ""))

    if oi_df.empty and ls_df.empty:
        print("\n⚠️ هیچ داده‌ای دریافت نشد. کلید API را در config.py چک کن.")
        return

    earliest = max([d.index[0] for d in [oi_df, ls_df] if not d.empty])
    latest = min([d.index[-1] for d in [oi_df, ls_df] if not d.empty])

    print(f"\nدر حال دریافت داده‌ی قیمت برای بازه‌ی {earliest} تا {latest}...")
    # تخمین تعداد کندل لازم بر اساس بازه‌ی زمانی
    from config import TIMEFRAME
    hours = (latest - earliest).total_seconds() / 3600
    tf_hours = {"1h": 1, "4h": 4, "1d": 24}.get(TIMEFRAME, 4)
    n_candles = int(hours / tf_hours) + 50
    raw = fetch_ohlcv(limit=min(n_candles, 1500))
    raw = raw[(raw.index >= earliest) & (raw.index <= latest)]
    print(f"تعداد کندل قیمت در این بازه: {len(raw)}")

    print("\nدر حال ساخت دیتاست پایه...")
    dataset_base = build_dataset(raw, for_training=True)

    print("در حال ساخت دیتاست غنی‌شده (OI + Long/Short)...")
    dataset_enriched = build_dataset(raw, for_training=True, oi_df=oi_df, longshort_df=ls_df)
    dataset_enriched = add_liquidation_feature(dataset_enriched, liq_df)
    dataset_enriched = dataset_enriched.dropna(subset=["total_liquidations"])

    print(f"\nتعداد ردیف دیتاست پایه: {len(dataset_base)} | دیتاست غنی‌شده: {len(dataset_enriched)}")

    if len(dataset_enriched) < 150:
        print("\n⚠️ حتی با Coinalyze، تعداد ردیف کافی برای یک تست walk-forward قوی نیست.")
        print("   نتیجه‌ی زیر را با احتیاط بیشتری نسبت به تست‌های ۴.۵ساله تفسیر کن.")

    print("\n" + "=" * 70)
    print("نتیجه‌ی walk-forward")
    print("=" * 70)

    oos_base = train_and_predict_folds(dataset_base, FEATURE_COLUMNS)
    auc_up_base, auc_down_base = compute_auc(oos_base)

    enriched_cols = FEATURE_COLUMNS + OI_LONGSHORT_FEATURE_COLUMNS + ["total_liquidations"]
    oos_en = train_and_predict_folds(dataset_enriched, enriched_cols)
    auc_up_en, auc_down_en = compute_auc(oos_en)

    print(f"\n{'':30}{'AUC صعودی':>15}{'AUC نزولی':>15}{'n تست':>10}")
    print(f"{'مدل پایه':30}{auc_up_base:>15.4f}{auc_down_base:>15.4f}{len(oos_base):>10}")
    print(f"{'مدل + OI/L-S/Liquidation':30}{auc_up_en:>15.4f}{auc_down_en:>15.4f}{len(oos_en):>10}")
    print(f"{'تفاوت':30}{auc_up_en - auc_up_base:>+15.4f}{auc_down_en - auc_down_base:>+15.4f}")

    improvement = max(auc_up_en - auc_up_base, auc_down_en - auc_down_base)
    print("\n" + "=" * 70)
    print("جمع‌بندی")
    print("=" * 70)
    if improvement >= 0.03 and len(oos_en) >= 150:
        print("✅ بهبود قابل‌توجه و روی نمونه‌ی معقول - این فیچرها ارزش نگه‌داشتن دارند.")
    elif improvement > 0:
        print("〰️ بهبود جزئی یا نمونه هنوز کوچک - نتیجه را قطعی در نظر نگیر.")
    else:
        print("⚠️ حتی با این داده‌ی جدید و طولانی‌تر، بهبودی مشاهده نشد.")


if __name__ == "__main__":
    run()
