"""
triple_barrier_diagnostic.py — ارزیابی مدل با لیبل‌های Triple-Barrier

نیازمند triple_barrier.py و strategy_core.py در همان پوشه.

این فایل دو چیز را با هم مقایسه می‌کند:
  ۱. AUC/Log Loss/Accuracy مدل با لیبل جدید (triple-barrier) در برابر
     نتیجه‌ی قبلی با لیبل افق‌ثابت (AUC≈0.50 که در edge_diagnostic.py دیدیم)
  ۲. نتیجه‌ی بک‌تست واقعی (با همان مکانیزم SL/TP) با این مدل جدید، در برابر
     نتیجه‌ی قبلی (Cumul=-21% در آستانه‌ی 0.60)

اگر AUC با لیبل جدید بهبود معنادار نشان دهد، یعنی بخشی از مشکل قبلی واقعاً
ناهم‌خوانی لیبل با مکانیزم معامله بوده و این تغییر کمک کرده. اگر AUC هنوز هم
نزدیک 0.50 بماند، یعنی مشکل عمیق‌تر از نوع لیبل‌گذاری است (به‌سراغ فیچرهای
جدید یا بازبینی کلی‌تر باید رفت).

اجرا:
    python triple_barrier_diagnostic.py
"""

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score, confusion_matrix

from config import TRAINING_CANDLES, TRAIN_WINDOW_CANDLES, MIN_CONFIDENCE
from data_fetcher import fetch_ohlcv_extended

from triple_barrier import build_dataset_triple_barrier, label_distribution_report
from strategy_core import (
    build_fold_bounds, run_ml_for_threshold, compute_metrics, print_metrics_row,
    run_full_significance_report,
)


def collect_oos_predictions(fold_bounds: list) -> pd.DataFrame:
    frames = []
    for fb in fold_bounds:
        ts = fb["test_slice"].copy()
        if "proba_0" not in ts.columns:
            ts["proba_0"] = (1 - ts["proba_1"] - ts["proba_-1"]).clip(lower=0)
        frames.append(ts[["timestamp", "label", "proba_-1", "proba_0", "proba_1"]])
    return pd.concat(frames, ignore_index=True)


def classification_diagnostic(fold_bounds: list, dataset: pd.DataFrame):
    oos = collect_oos_predictions(fold_bounds)
    y_true = oos["label"].values
    n_total = len(oos)

    print("\n" + "=" * 70)
    print("توزیع کلاس‌های واقعی (out-of-sample)")
    print("=" * 70)
    dist = pd.Series(y_true).value_counts(normalize=True).sort_index()
    for cls, frac in dist.items():
        name = {1: "صعودی (1)", -1: "نزولی (-1)", 0: "خنثی (0)"}.get(cls, str(cls))
        print(f"  {name}: {frac*100:.1f}% ({(pd.Series(y_true) == cls).sum()} ردیف)")

    proba_cols = ["proba_-1", "proba_0", "proba_1"]
    class_labels = [-1, 0, 1]
    proba_matrix = oos[proba_cols].values
    y_pred = np.array(class_labels)[np.argmax(proba_matrix, axis=1)]

    majority_class = pd.Series(y_true).mode()[0]
    y_pred_baseline = np.full(n_total, majority_class)

    acc_model = accuracy_score(y_true, y_pred)
    acc_baseline = accuracy_score(y_true, y_pred_baseline)
    print(f"\nAccuracy مدل: {acc_model*100:.2f}% | Accuracy baseline (اکثریت): {acc_baseline*100:.2f}%")

    eps = 1e-9
    proba_clipped = np.clip(proba_matrix, eps, 1 - eps)
    proba_clipped = proba_clipped / proba_clipped.sum(axis=1, keepdims=True)
    ll_model = log_loss(y_true, proba_clipped, labels=class_labels)
    baseline_proba = np.tile(dist.reindex(class_labels).fillna(eps).values, (n_total, 1))
    ll_baseline = log_loss(y_true, baseline_proba, labels=class_labels)
    print(f"Log Loss مدل: {ll_model:.4f} | Log Loss baseline: {ll_baseline:.4f}")

    y_up = (y_true == 1).astype(int)
    y_down = (y_true == -1).astype(int)
    auc_up = roc_auc_score(y_up, oos["proba_1"].values)
    auc_down = roc_auc_score(y_down, oos["proba_-1"].values)

    print(f"\nAUC صعودی (1):  {auc_up:.4f}   (قبلاً با لیبل افق‌ثابت: 0.5174)")
    print(f"AUC نزولی (-1): {auc_down:.4f}   (قبلاً با لیبل افق‌ثابت: 0.4994)")

    improved = (auc_up > 0.55) or (auc_down > 0.55)
    if improved:
        print("\n✅ حداقل یکی از AUCها به‌طور محسوسی بهتر از 0.50 و از نتیجه‌ی قبلی است -")
        print("   بازتعریف لیبل با triple-barrier کمک کرده. ادامه‌ی کار روی این مسیر منطقی است.")
    else:
        print("\n⚠️ AUC هنوز هم نزدیک به 0.50 است، حتی با لیبل triple-barrier.")
        print("   یعنی مشکل صرفاً از نوع لیبل‌گذاری نبوده - فیچرهای تکنیکال فعلی")
        print("   احتمالاً برای این بازار/تایم‌فریم به‌اندازه‌ی کافی سیگنال ندارند.")

    cm = confusion_matrix(y_true, y_pred, labels=class_labels)
    print("\nماتریس درهم‌ریختگی (سطر=واقعی، ستون=پیش‌بینی):")
    header = "         " + "".join(f"{'پیش‌بینی '+str(c):>14}" for c in class_labels)
    print(header)
    for i, c in enumerate(class_labels):
        row_str = f"واقعی {c:>3} |" + "".join(f"{cm[i][j]:>14}" for j in range(len(class_labels)))
        print(row_str)

    return {"auc_up": auc_up, "auc_down": auc_down, "acc_model": acc_model, "acc_baseline": acc_baseline}


def run():
    print(f"در حال دریافت {TRAINING_CANDLES} کندل تاریخی...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)

    print("در حال ساخت دیتاست با لیبل‌های triple-barrier...")
    dataset = build_dataset_triple_barrier(raw)
    dataset = dataset.reset_index()
    n = len(dataset)
    print(f"تعداد کل کندل‌های قابل‌استفاده: {n}\n")
    label_distribution_report(dataset)

    print("\nدر حال آموزش فولدها (walk-forward)...")
    fold_bounds = build_fold_bounds(dataset, n, verbose=False)
    print(f"تعداد فولدها: {len(fold_bounds)}")

    diag = classification_diagnostic(fold_bounds, dataset)

    # ---- بک‌تست واقعی با همان آستانه‌ی قبلی، برای مقایسه‌ی مستقیم ----
    print("\n" + "=" * 70)
    print(f"بک‌تست واقعی با لیبل جدید در آستانه‌ی {MIN_CONFIDENCE}")
    print("=" * 70)
    trades = run_ml_for_threshold(dataset, fold_bounds, MIN_CONFIDENCE)
    metrics = compute_metrics(trades)
    print_metrics_row("Triple-Barrier", metrics)
    print("(نتیجه‌ی قبلی با لیبل افق‌ثابت در همین آستانه: n=78, Cumul=-21.04%, PF=0.73)")

    if metrics and metrics["n_trades"] >= 10:
        run_full_significance_report(dataset, trades, TRAIN_WINDOW_CANDLES, label="Triple-Barrier")

    print("\n" + "=" * 70)
    print("جمع‌بندی")
    print("=" * 70)
    if diag["auc_up"] > 0.55 or diag["auc_down"] > 0.55:
        print("لیبل triple-barrier سیگنال بهتری نسبت به لیبل افق‌ثابت نشان داد.")
        print("قدم بعدی منطقی: بهینه‌سازی دقیق‌تر threshold/SL/TP روی همین لیبل جدید،")
        print("یا اضافه‌کردن فیچرهای مکمل برای تقویت بیشتر همین سیگنال.")
    else:
        print("لیبل triple-barrier هم بهبود قابل‌توجهی نداد. این شاهد قوی‌تری است که")
        print("مشکل از فیچرهای تکنیکال فعلی می‌آید، نه از نحوه‌ی تعریف لیبل. پیشنهاد بعدی:")
        print("افزودن منابع اطلاعاتی واقعاً جدید (funding rate, open interest, نسبت")
        print("long/short) که در قیمت/حجم OHLCV به‌تنهایی وجود ندارند.")


if __name__ == "__main__":
    run()
