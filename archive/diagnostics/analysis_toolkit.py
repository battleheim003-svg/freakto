"""
analysis_toolkit.py — جعبه‌ابزار تحلیل استراتژی

نیازمند strategy_core.py در همان پوشه.

این فایل سه تحلیل را پشت سر هم انجام می‌دهد:

۱. گزارش اهمیت فیچرها (Feature Importance)
   مشخص می‌کند مدل RandomForest در طول ۴۴ فولد بیشتر به کدام فیچرها تکیه
   کرده و آیا این اهمیت‌ها بین فولدها پایدار است یا خیلی نوسان دارد (نوسان
   زیاد = نشانه‌ی عدم پایداری مدل بین رژیم‌های مختلف بازار).

۲. مقایسه‌ی مدل ML با یک قانون ساده‌ی Trend-Following
   یک قانون کاملاً ساده (بدون یادگیری ماشین) را با همان مکانیزم SL/TP و
   همان فولدهای walk-forward اجرا می‌کند و نتیجه‌اش را کنار نتیجه‌ی مدل ML
   می‌گذارد. اگر قانون ساده عملکرد مشابه یا بهتری داشته باشد، یعنی پیچیدگی
   مدل ML در عمل ارزش افزوده‌ای ایجاد نمی‌کند.

۳. تست پایداری روی نمادهای دیگر (Multi-Symbol Robustness)
   همان استراتژی (آستانه‌ی 0.60) را روی چند نماد دیگر هم اجرا می‌کند تا
   ببینیم آیا نتیجه‌ی مثبت BTC/USDT یک الگوی پایدار است یا مختص همین یک
   نماد و این بازه‌ی زمانی بوده. این بخش کند است (هر نماد یعنی یک دانلود
   و walk-forward کامل دیگر) - با RUN_MULTI_SYMBOL_TEST می‌توانی خاموشش کنی.

اجرا:
    python analysis_toolkit.py
"""

import numpy as np
import pandas as pd

from config import TRAINING_CANDLES, TRAIN_WINDOW_CANDLES, SYMBOL
from data_fetcher import fetch_ohlcv_extended
from features import build_dataset, FEATURE_COLUMNS

from strategy_core import (
    build_fold_bounds, run_ml_for_threshold, run_baseline,
    compute_metrics, print_metrics_row, run_full_significance_report,
)

# ---------- تنظیمات قابل تغییر ----------
THRESHOLD_TO_TEST = 0.60
RUN_FEATURE_IMPORTANCE = True
RUN_BASELINE_COMPARISON = True
RUN_MULTI_SYMBOL_TEST = True
SYMBOLS_TO_TEST = ["ETH/USDT", "SOL/USDT"]   # نمادهای اضافی برای تست پایداری (SYMBOL اصلی config.py جداگانه و همیشه تست می‌شود)


# ============================================================
# بخش ۱: اهمیت فیچرها
# ============================================================

def feature_importance_report(fold_bounds: list):
    print("\n" + "=" * 70)
    print("بخش ۱: اهمیت فیچرها (میانگین و پایداری در طول 44 فولد)")
    print("=" * 70)

    importances = pd.DataFrame([fb["feature_importance"] for fb in fold_bounds])
    summary = pd.DataFrame({
        "میانگین اهمیت": importances.mean(),
        "انحراف معیار": importances.std(),
    }).sort_values("میانگین اهمیت", ascending=False)

    # ضریب تغییرات (std/mean) برای سنجش پایداری؛ عدد بالا = اهمیت این فیچر بین فولدها خیلی نوسان دارد
    summary["ضریب نوسان"] = summary["انحراف معیار"] / summary["میانگین اهمیت"]

    print(f"\n{'فیچر':<16} | {'میانگین اهمیت':>14} | {'انحراف معیار':>13} | {'ضریب نوسان':>11}")
    print("-" * 65)
    for feat, row in summary.iterrows():
        print(f"{feat:<16} | {row['میانگین اهمیت']:>14.4f} | {row['انحراف معیار']:>13.4f} | {row['ضریب نوسان']:>11.2f}")

    top3 = summary.index[:3].tolist()
    print(f"\nسه فیچر برتر (بیشترین اتکای مدل): {', '.join(top3)}")
    high_variance = summary[summary["ضریب نوسان"] > 1.0]
    if len(high_variance) > 0:
        print(f"⚠️ فیچرهایی با نوسان اهمیت بالا (ضریب نوسان > 1.0) بین فولدها: {', '.join(high_variance.index.tolist())}")
        print("   این یعنی اتکای مدل به این فیچرها بسته به دوره‌ی بازار خیلی عوض می‌شود -")
        print("   نشانه‌ای از ناپایداری احتمالی مدل بین رژیم‌های مختلف بازار.")

    return summary


# ============================================================
# بخش ۲: مقایسه با قانون ساده
# ============================================================

def baseline_comparison_report(dataset: pd.DataFrame, fold_bounds: list):
    print("\n" + "=" * 70)
    print("بخش ۲: مقایسه‌ی مدل ML با قانون ساده‌ی Trend-Following")
    print("=" * 70)
    print("قانون ساده: خرید وقتی EMA10 > SMA30 و RSI بین 50-70 | فروش وقتی برعکس")
    print("(همان مکانیزم SL/TP و همان فولدها؛ تنها تفاوت، روش تولید سیگنال است)\n")

    ml_trades = run_ml_for_threshold(dataset, fold_bounds, THRESHOLD_TO_TEST)
    baseline_trades = run_baseline(dataset, fold_bounds)

    ml_metrics = compute_metrics(ml_trades)
    baseline_metrics = compute_metrics(baseline_trades)

    print_metrics_row("مدل ML", ml_metrics)
    print_metrics_row("قانون ساده", baseline_metrics)

    if ml_metrics and baseline_metrics:
        if baseline_metrics["cumulative_return"] >= ml_metrics["cumulative_return"]:
            print("\n⚠️ قانون ساده‌ی trend-following عملکردی مشابه یا بهتر از مدل ML داشته است.")
            print("   این نشانه‌ی نگران‌کننده‌ای است: پیچیدگی مدل یادگیری ماشین در عمل")
            print("   ارزش افزوده‌ی قابل توجهی نسبت به یک قانون خیلی ساده ایجاد نکرده.")
        else:
            print("\n✅ مدل ML از قانون ساده بهتر عمل کرده - حداقل نسبت به این baseline،")
            print("   پیچیدگی مدل توجیه دارد.")

    if baseline_metrics and baseline_metrics["n_trades"] >= 10:
        run_full_significance_report(dataset, baseline_trades, TRAIN_WINDOW_CANDLES, label="قانون ساده")
    elif baseline_metrics:
        print(f"\n(تعداد معاملات قانون ساده [{baseline_metrics['n_trades']}] برای آزمون آماری معتبر کم است)")

    return ml_metrics, baseline_metrics


# ============================================================
# بخش ۳: تست روی نمادهای دیگر
# ============================================================

def test_single_symbol(symbol: str):
    print(f"\n--- در حال دریافت داده برای {symbol} ---")
    try:
        raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES, symbol=symbol)
    except Exception as e:
        print(f"خطا در دریافت داده‌ی {symbol}: {e}")
        return None

    dataset = build_dataset(raw, for_training=True)
    dataset = dataset.reset_index()
    n = len(dataset)

    fold_bounds = build_fold_bounds(dataset, n, verbose=False)
    if not fold_bounds:
        print(f"داده‌ی کافی برای {symbol} نیست.")
        return None

    trades = run_ml_for_threshold(dataset, fold_bounds, THRESHOLD_TO_TEST)
    metrics = compute_metrics(trades)
    print_metrics_row(symbol, metrics)

    if metrics and metrics["n_trades"] >= 10:
        _, stats = run_full_significance_report(dataset, trades, TRAIN_WINDOW_CANDLES, label=symbol)
        return {"symbol": symbol, "metrics": metrics, "stats": stats}
    return {"symbol": symbol, "metrics": metrics, "stats": None}


def multi_symbol_report(primary_symbol: str, primary_metrics: dict):
    print("\n" + "=" * 70)
    print("بخش ۳: تست پایداری روی نمادهای دیگر")
    print("=" * 70)

    results = [{"symbol": primary_symbol, "metrics": primary_metrics, "stats": None}]
    for sym in SYMBOLS_TO_TEST:
        r = test_single_symbol(sym)
        if r:
            results.append(r)

    print("\n--- خلاصه‌ی مقایسه‌ای همه‌ی نمادها (آستانه {:.2f}) ---".format(THRESHOLD_TO_TEST))
    for r in results:
        print_metrics_row(r["symbol"], r["metrics"])

    positive_count = sum(
        1 for r in results if r["metrics"] and r["metrics"]["cumulative_return"] > 0
    )
    print(f"\nاز {len(results)} نماد تست‌شده، {positive_count} نماد بازده تجمعی مثبت داشتند.")
    if positive_count <= len(results) / 2:
        print("⚠️ نتیجه‌ی مثبت روی نماد اصلی در اکثر نمادهای دیگر تکرار نشد؛")
        print("   این شاهد قوی‌ای است که نتیجه‌ی اولیه ممکن است مختص یک نماد/بازه‌ی خاص بوده باشد، نه یک edge عمومی.")
    else:
        print("✅ نتیجه‌ی مثبت در اکثر نمادهای تست‌شده هم دیده شد - شاهدی به نفع پایداری استراتژی.")


# ============================================================
# اجرای کامل
# ============================================================

def run():
    print(f"در حال دریافت {TRAINING_CANDLES} کندل تاریخی برای نماد اصلی ({SYMBOL})...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    dataset = build_dataset(raw, for_training=True)
    dataset = dataset.reset_index()
    n = len(dataset)
    print(f"تعداد کل کندل‌های قابل‌استفاده: {n}")

    print("\nدر حال آموزش فولدها (walk-forward)...")
    fold_bounds = build_fold_bounds(dataset, n, verbose=False)
    print(f"تعداد فولدها: {len(fold_bounds)}")

    primary_ml_trades = run_ml_for_threshold(dataset, fold_bounds, THRESHOLD_TO_TEST)
    primary_metrics = compute_metrics(primary_ml_trades)
    print(f"\n--- نتیجه‌ی مدل ML روی {SYMBOL} در آستانه‌ی {THRESHOLD_TO_TEST} ---")
    print_metrics_row(SYMBOL, primary_metrics)

    if RUN_FEATURE_IMPORTANCE:
        feature_importance_report(fold_bounds)

    if RUN_BASELINE_COMPARISON:
        baseline_comparison_report(dataset, fold_bounds)

    if RUN_MULTI_SYMBOL_TEST:
        multi_symbol_report(SYMBOL, primary_metrics)

    print("\n" + "=" * 70)
    print("پایان گزارش")
    print("=" * 70)


if __name__ == "__main__":
    run()