"""
test_funding_rate_edge.py — آیا افزودن Funding Rate واقعاً AUC را بهتر می‌کند؟

این اسکریپت دقیقاً مثل edge_diagnostic.py عمل می‌کند، ولی دو مدل را کنار هم
مقایسه می‌کند:
  1) مدل پایه: فقط فیچرهای تکنیکال قبلی (همان‌هایی که AUC≈0.50 داشتند)
  2) مدل غنی‌شده: فیچرهای قبلی + funding_rate + funding_rate_ma

اگر AUC مدل غنی‌شده به‌طور معنی‌دار (حداقل چند صدم) از مدل پایه بهتر باشد،
یعنی Funding Rate واقعاً اطلاعات جدید و مفیدی اضافه کرده. اگر تفاوت
ناچیز بود، یعنی این فیچر هم مثل بقیه کمکی نمی‌کند.

اجرا:
    python test_funding_rate_edge.py
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score

from config import TRAINING_CANDLES, TRAIN_WINDOW_CANDLES, RETRAIN_STEP_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import build_dataset, FEATURE_COLUMNS, FUNDING_FEATURE_COLUMNS
from futures_data_fetcher import fetch_funding_rate_history


def train_and_predict_folds(dataset: pd.DataFrame, feature_cols: list):
    """آموزش/تست walk-forward ساده و برگرداندن پیش‌بینی‌های out-of-sample."""
    n = len(dataset)
    all_preds = []
    start = TRAIN_WINDOW_CANDLES

    while start + RETRAIN_STEP_CANDLES <= n:
        train_slice = dataset.iloc[start - TRAIN_WINDOW_CANDLES:start]
        test_slice = dataset.iloc[start:start + RETRAIN_STEP_CANDLES].copy()

        X_train = train_slice[feature_cols].values
        y_train = train_slice["label"].values
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        model = RandomForestClassifier(
            n_estimators=300, max_depth=6, min_samples_leaf=20,
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
    auc_up = np.nan
    auc_down = np.nan
    if 0 < y_up.sum() < len(y_up):
        auc_up = roc_auc_score(y_up, oos["proba_1"].values)
    if 0 < y_down.sum() < len(y_down):
        auc_down = roc_auc_score(y_down, oos["proba_-1"].values)
    return auc_up, auc_down


def run():
    print(f"در حال دریافت {TRAINING_CANDLES} کندل قیمت...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)

    print("در حال دریافت تاریخچه‌ی کامل Funding Rate (ممکن است کمی طول بکشد)...")
    start_ms = int(raw.index[0].timestamp() * 1000)
    funding_df = fetch_funding_rate_history(start_time_ms=start_ms)
    print(f"تعداد رکورد Funding Rate دریافت‌شده: {len(funding_df)}")

    print("\nدر حال ساخت دیتاست پایه (بدون Funding Rate)...")
    dataset_base = build_dataset(raw, for_training=True)
    dataset_base = dataset_base.reset_index(drop=True) if dataset_base.index.name is None else dataset_base.reset_index()

    print("در حال ساخت دیتاست غنی‌شده (با Funding Rate)...")
    dataset_enriched = build_dataset(raw, for_training=True, funding_df=funding_df)
    dataset_enriched = dataset_enriched.reset_index() if dataset_enriched.index.name is not None else dataset_enriched

    n_base = len(dataset_base)
    n_enriched = len(dataset_enriched)
    print(f"تعداد ردیف دیتاست پایه: {n_base} | دیتاست غنی‌شده: {n_enriched}\n")

    print("=" * 70)
    print("در حال آموزش/تست مدل پایه (walk-forward)...")
    print("=" * 70)
    oos_base = train_and_predict_folds(dataset_base, FEATURE_COLUMNS)
    auc_up_base, auc_down_base = compute_auc(oos_base)

    print("\n" + "=" * 70)
    print("در حال آموزش/تست مدل غنی‌شده با Funding Rate (walk-forward)...")
    print("=" * 70)
    enriched_cols = FEATURE_COLUMNS + FUNDING_FEATURE_COLUMNS
    oos_enriched = train_and_predict_folds(dataset_enriched, enriched_cols)
    auc_up_enriched, auc_down_enriched = compute_auc(oos_enriched)

    print("\n" + "=" * 70)
    print("نتیجه‌ی نهایی مقایسه")
    print("=" * 70)
    print(f"{'':25}{'AUC صعودی':>15}{'AUC نزولی':>15}")
    print(f"{'مدل پایه':25}{auc_up_base:>15.4f}{auc_down_base:>15.4f}")
    print(f"{'مدل + Funding Rate':25}{auc_up_enriched:>15.4f}{auc_down_enriched:>15.4f}")
    print(f"{'تفاوت':25}{auc_up_enriched - auc_up_base:>+15.4f}{auc_down_enriched - auc_down_base:>+15.4f}")

    improvement = max(auc_up_enriched - auc_up_base, auc_down_enriched - auc_down_base)
    print("\n" + "=" * 70)
    print("جمع‌بندی")
    print("=" * 70)
    if improvement >= 0.03:
        print("✅ Funding Rate بهبود قابل‌توجهی (≥۰.۰۳ واحد AUC) ایجاد کرده - ")
        print("   این فیچر ارزش نگه‌داشتن دارد و شایسته‌ی بررسی بیشتر (مثلاً بک‌تست کامل) است.")
    elif improvement > 0:
        print("〰️ Funding Rate بهبود جزئی و احتمالاً بی‌اهمیت ایجاد کرده.")
        print("   ممکن است فقط نویز آماری باشد؛ با احتیاط قضاوت کن.")
    else:
        print("⚠️ Funding Rate هیچ بهبودی نسبت به مدل پایه ایجاد نکرده.")
        print("   حتی این منبع اطلاعاتی اضافه هم به‌تنهایی سیگنال جهت قابل‌اعتمادی نمی‌دهد.")


if __name__ == "__main__":
    run()
