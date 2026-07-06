"""
edge_diagnostic.py — تشخیص مستقیم قدرت پیش‌بینی مدل (بدون دخالت SL/TP و کارمزد)

نیازمند strategy_core.py در همان پوشه (از build_fold_bounds آن استفاده می‌کند).

چرا این تحلیل لازم است؟
تا الان همه‌ی نتایج را از دریچه‌ی «بازده بعد از SL/TP و کارمزد» دیده‌ایم. این
لایه‌ی اضافه (SL/TP، آستانه‌ی اطمینان، کارمزد) می‌تواند حتی یک سیگنال ضعیفِ
واقعی را هم زیر نویز خودش دفن کند، یا برعکس - سخت است بفهمیم آیا شکست به‌خاطر
نبودِ سیگنال است یا به‌خاطر مکانیزم معامله. این فایل مستقیماً می‌پرسد:
"آیا مدل اصلاً اطلاعاتی درباره‌ی جهت آینده‌ی قیمت دارد؟" - بدون SL/TP، بدون
آستانه، فقط طبقه‌بندی خام روی داده‌ی out-of-sample هر فولد.

معیارها:
- Accuracy مدل در مقابل baseline «همیشه اکثریت را پیش‌بینی کن» (Dummy Classifier)
- Log Loss مدل در مقابل baseline (log loss پایین‌تر = بهتر)
- AUC (یک-در-مقابل-بقیه) برای کلاس 1 (صعودی) و کلاس -1 (نزولی) -
  AUC=0.50 یعنی دقیقاً هم‌ارز با شانس؛ AUC معنی‌دار بالاتر از 0.50
  (معمولاً از 0.55 به بالا در بازارهای مالی قابل توجه است) نشانه‌ی سیگنال واقعی است.
- ماتریس درهم‌ریختگی (Confusion Matrix) تجمیعی روی همه‌ی فولدها

تفسیر:
- اگر AUC نزدیک 0.50 باشد: فیچرهای فعلی سیگنال قابل‌یادگیری کافی ندارند -
  باید فیچر/لیبل/مدل عوض شود، نه فقط آستانه یا SL/TP.
- اگر AUC معنی‌دار بالاتر از 0.50 باشد ولی نتیجه‌ی بک‌تست منفی بود: مشکل از
  مکانیزم معامله (SL/TP، کارمزد، آستانه) است، نه از خود مدل - می‌توان با تنظیم
  دقیق‌تر این پارامترها نتیجه را نجات داد.

اجرا:
    python edge_diagnostic.py
"""

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, log_loss, accuracy_score, confusion_matrix

from config import TRAINING_CANDLES, TRAIN_WINDOW_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import build_dataset

from strategy_core import build_fold_bounds


def collect_oos_predictions(fold_bounds: list) -> pd.DataFrame:
    """تمام پیش‌بینی‌های out-of-sample (روی داده‌ی تست هر فولد) را یکجا جمع می‌کند."""
    frames = []
    for fb in fold_bounds:
        ts = fb["test_slice"].copy()
        if "proba_0" not in ts.columns:
            ts["proba_0"] = (1 - ts["proba_1"] - ts["proba_-1"]).clip(lower=0)
        frames.append(ts[["timestamp", "label", "proba_-1", "proba_0", "proba_1"]])
    return pd.concat(frames, ignore_index=True)


def per_fold_auc(fold_bounds: list) -> pd.DataFrame:
    """AUC هر فولد به‌طور جداگانه، برای دیدن اینکه آیا سیگنال در طول زمان پایدار است."""
    rows = []
    for fb in fold_bounds:
        ts = fb["test_slice"]
        y_true = ts["label"].values
        if len(set(y_true)) < 2:
            continue
        y_up = (y_true == 1).astype(int)
        y_down = (y_true == -1).astype(int)
        auc_up = np.nan
        auc_down = np.nan
        try:
            if y_up.sum() > 0 and y_up.sum() < len(y_up):
                auc_up = roc_auc_score(y_up, ts["proba_1"].values)
        except ValueError:
            pass
        try:
            if y_down.sum() > 0 and y_down.sum() < len(y_down):
                auc_down = roc_auc_score(y_down, ts["proba_-1"].values)
        except ValueError:
            pass
        rows.append({"fold": fb["fold"], "auc_up": auc_up, "auc_down": auc_down, "n_rows": len(ts)})
    return pd.DataFrame(rows)


def run():
    print(f"در حال دریافت {TRAINING_CANDLES} کندل تاریخی...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    dataset = build_dataset(raw, for_training=True)
    dataset = dataset.reset_index()
    n = len(dataset)
    print(f"تعداد کل کندل‌های قابل‌استفاده: {n}\n")

    print("در حال آموزش فولدها (walk-forward)...")
    fold_bounds = build_fold_bounds(dataset, n, verbose=False)
    print(f"تعداد فولدها: {len(fold_bounds)}\n")

    oos = collect_oos_predictions(fold_bounds)
    y_true = oos["label"].values
    n_total = len(oos)

    print("=" * 70)
    print("توزیع کلاس‌های واقعی (Ground Truth) در کل داده‌ی out-of-sample")
    print("=" * 70)
    dist = pd.Series(y_true).value_counts(normalize=True).sort_index()
    for cls, frac in dist.items():
        name = {1: "صعودی (1)", -1: "نزولی (-1)", 0: "خنثی (0)"}.get(cls, str(cls))
        print(f"  {name}: {frac*100:.1f}% ({(pd.Series(y_true) == cls).sum()} ردیف)")

    # ---- پیش‌بینی مدل (argmax) در مقابل baseline اکثریت ----
    proba_cols = ["proba_-1", "proba_0", "proba_1"]
    class_labels = [-1, 0, 1]
    proba_matrix = oos[proba_cols].values
    y_pred = np.array(class_labels)[np.argmax(proba_matrix, axis=1)]

    majority_class = pd.Series(y_true).mode()[0]
    y_pred_baseline = np.full(n_total, majority_class)

    acc_model = accuracy_score(y_true, y_pred)
    acc_baseline = accuracy_score(y_true, y_pred_baseline)

    print("\n" + "=" * 70)
    print("مقایسه‌ی Accuracy: مدل در مقابل baseline (همیشه پیش‌بینی اکثریت)")
    print("=" * 70)
    print(f"Accuracy مدل:     {acc_model*100:.2f}%")
    print(f"Accuracy baseline: {acc_baseline*100:.2f}%  (baseline همیشه کلاس {majority_class} را پیش‌بینی می‌کند)")
    if acc_model <= acc_baseline:
        print("⚠️ مدل حتی از پیش‌بینی ثابتِ «همیشه اکثریت» بهتر عمل نکرده.")
    else:
        print(f"✅ مدل {(acc_model-acc_baseline)*100:.2f} واحد درصد از baseline بهتر است.")

    # ---- Log Loss ----
    eps = 1e-9
    proba_clipped = np.clip(proba_matrix, eps, 1 - eps)
    proba_clipped = proba_clipped / proba_clipped.sum(axis=1, keepdims=True)
    ll_model = log_loss(y_true, proba_clipped, labels=class_labels)

    baseline_proba = np.tile(dist.reindex(class_labels).fillna(eps).values, (n_total, 1))
    ll_baseline = log_loss(y_true, baseline_proba, labels=class_labels)

    print(f"\nLog Loss مدل:      {ll_model:.4f}")
    print(f"Log Loss baseline:  {ll_baseline:.4f}  (baseline = توزیع پایه‌ی کلاس‌ها، بدون فیچر)")
    if ll_model >= ll_baseline:
        print("⚠️ Log Loss مدل بهتر از پیش‌بینی توزیع پایه (بدون هیچ فیچری) نیست.")
    else:
        print("✅ Log Loss مدل بهتر از baseline است - مدل احتمالات را بهتر از حالت کورکورانه تخمین می‌زند.")

    # ---- AUC (یک‌در‌مقابل‌بقیه) ----
    print("\n" + "=" * 70)
    print("AUC (یک-در-مقابل-بقیه) — معیار اصلی قدرت تفکیک مدل")
    print("=" * 70)
    print("(0.50 = دقیقاً هم‌ارز شانس | هرچه بالاتر از 0.50، تفکیک بهتر)")

    y_up = (y_true == 1).astype(int)
    y_down = (y_true == -1).astype(int)
    auc_up = roc_auc_score(y_up, oos["proba_1"].values)
    auc_down = roc_auc_score(y_down, oos["proba_-1"].values)
    print(f"AUC کلاس صعودی (1):  {auc_up:.4f}")
    print(f"AUC کلاس نزولی (-1): {auc_down:.4f}")

    both_near_chance = abs(auc_up - 0.5) < 0.03 and abs(auc_down - 0.5) < 0.03
    if both_near_chance:
        print("\n⚠️ هر دو AUC عملاً نزدیک به 0.50 هستند - شواهد قوی که فیچرهای فعلی")
        print("   سیگنال قابل‌یادگیری معناداری درباره‌ی جهت قیمت آینده ندارند.")
        print("   تنظیم آستانه/SL/TP این مشکل بنیادی را حل نمی‌کند؛ باید فیچرها،")
        print("   نحوه‌ی لیبل‌گذاری، یا کل رویکرد بازبینی شود.")
    else:
        print("\n✅ حداقل یکی از AUCها معنادار بالاتر از 0.50 است - یعنی مدل سیگنال")
        print("   واقعی دارد، و مشکلات بک‌تست قبلی احتمالاً از مکانیزم معامله")
        print("   (SL/TP، آستانه، کارمزد) می‌آید، نه از نبودِ اطلاعات در مدل.")

    # ---- Confusion Matrix ----
    print("\n" + "=" * 70)
    print("ماتریس درهم‌ریختگی (سطر = واقعی، ستون = پیش‌بینی مدل)")
    print("=" * 70)
    cm = confusion_matrix(y_true, y_pred, labels=class_labels)
    header = "         " + "".join(f"{'پیش‌بینی '+str(c):>14}" for c in class_labels)
    print(header)
    for i, c in enumerate(class_labels):
        row_str = f"واقعی {c:>3} |" + "".join(f"{cm[i][j]:>14}" for j in range(len(class_labels)))
        print(row_str)

    # ---- پایداری AUC در طول زمان ----
    print("\n" + "=" * 70)
    print("پایداری AUC در طول فولدها (آیا سیگنال در طول زمان ثابت است؟)")
    print("=" * 70)
    fold_auc = per_fold_auc(fold_bounds)
    if len(fold_auc) > 0:
        print(fold_auc.to_string(index=False))
        print(f"\nانحراف معیار AUC صعودی بین فولدها: {fold_auc['auc_up'].std():.4f}")
        print(f"انحراف معیار AUC نزولی بین فولدها: {fold_auc['auc_down'].std():.4f}")
        print("(انحراف معیار بالا = سیگنال بین دوره‌های مختلف بازار خیلی بی‌ثبات است،")
        print(" حتی اگر میانگین کلی AUC قابل قبول باشد)")

    print("\n" + "=" * 70)
    print("جمع‌بندی")
    print("=" * 70)
    if both_near_chance and ll_model >= ll_baseline:
        print("نتیجه‌گیری: با این مجموعه فیچر و این تعریف لیبل، مدل عملاً هیچ اطلاعات")
        print("قابل‌استفاده‌ای درباره‌ی جهت قیمت آینده ندارد. پیشنهاد: به‌جای تنظیم دقیق‌تر")
        print("SL/TP یا آستانه، باید سراغ فیچرهای جدید (حجم/orderflow، همبستگی بین‌بازاری،")
        print("رژیم نوسان)، بازتعریف لیبل (مثلاً triple-barrier با افق متغیر)، یا")
        print("مدل‌های دیگر (Gradient Boosting) رفت.")
    else:
        print("نتیجه‌گیری: شواهدی از سیگنال واقعی (هرچند ضعیف) در مدل هست. تمرکز بعدی")
        print("باید روی بهینه‌سازی مکانیزم معامله (SL/TP، آستانه، کارمزد) و شاید افزودن")
        print("فیچرهای مکمل برای تقویت همین سیگنال باشد.")


if __name__ == "__main__":
    run()
