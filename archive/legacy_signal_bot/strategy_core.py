"""
strategy_core.py — هسته‌ی مشترک تحلیل استراتژی

این فایل شامل تمام منطق پایه‌ای است که در analysis_toolkit.py و سایر اسکریپت‌های
تحلیلی استفاده می‌شود: آموزش مدل هر فولد، شبیه‌سازی خروج با SL/TP، محاسبه‌ی
معیارها، و آزمون‌های آماری (Bootstrap / Permutation).

این فایل به‌تنهایی اجرا نمی‌شود؛ فقط توسط فایل‌های دیگر import می‌شود.
باید همیشه کنار config.py, data_fetcher.py, features.py در یک پوشه باشد.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from config import TRAIN_WINDOW_CANDLES, RETRAIN_STEP_CANDLES
from features import FEATURE_COLUMNS

# ---------- تنظیمات قابل تغییر ----------
SL_ATR_MULT = 1.0
TP_ATR_MULT = 1.5
MAX_HOLD_CANDLES = 12
FEE_RATE_ROUNDTRIP = 0.002


# ============================================================
# آموزش مدل و شبیه‌سازی خروج
# ============================================================

def train_one_fold(train_df: pd.DataFrame):
    X = train_df[FEATURE_COLUMNS].values
    y = train_df["label"].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        min_samples_leaf=20,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled, y)
    return model, scaler


def simulate_exit(dataset: pd.DataFrame, entry_pos: int, direction: int,
                   entry_price: float, atr_pct_at_entry: float):
    """شبیه‌سازی خروج واقعی از معامله با SL/TP. خروجی: (exit_price, exit_reason, bars_held)"""
    atr_price = atr_pct_at_entry * entry_price
    if direction == 1:
        tp_price = entry_price + TP_ATR_MULT * atr_price
        sl_price = entry_price - SL_ATR_MULT * atr_price
    else:
        tp_price = entry_price - TP_ATR_MULT * atr_price
        sl_price = entry_price + SL_ATR_MULT * atr_price

    last_pos = min(entry_pos + MAX_HOLD_CANDLES, len(dataset) - 1)
    for pos in range(entry_pos + 1, last_pos + 1):
        bar = dataset.iloc[pos]
        if direction == 1:
            hit_sl = bar["low"] <= sl_price
            hit_tp = bar["high"] >= tp_price
        else:
            hit_sl = bar["high"] >= sl_price
            hit_tp = bar["low"] <= tp_price
        if hit_sl:
            return sl_price, "SL", pos - entry_pos
        if hit_tp:
            return tp_price, "TP", pos - entry_pos

    return dataset.iloc[last_pos]["close"], "TIME", last_pos - entry_pos


def build_fold_bounds(dataset: pd.DataFrame, n: int, verbose: bool = False,
                       train_window: int = None, retrain_step: int = None) -> list:
    """
    آموزش مدل هر فولد walk-forward و محاسبه‌ی احتمال‌ها روی بازه‌ی تست آن فولد.
    اهمیت فیچرها (feature_importance) هم برای هر فولد ذخیره می‌شود تا بعداً
    قابل تجمیع و بررسی باشد.
    """
    train_window = train_window or TRAIN_WINDOW_CANDLES
    retrain_step = retrain_step or RETRAIN_STEP_CANDLES

    fold_bounds = []
    start = train_window
    fold_num = 0
    while start + retrain_step <= n:
        fold_num += 1
        train_slice = dataset.iloc[start - train_window:start]
        test_slice = dataset.iloc[start:start + retrain_step].copy()

        model, scaler = train_one_fold(train_slice)
        X_test = scaler.transform(test_slice[FEATURE_COLUMNS].values)
        proba = model.predict_proba(X_test)
        for i, c in enumerate(model.classes_):
            test_slice[f"proba_{c}"] = proba[:, i]
        if "proba_-1" not in test_slice.columns:
            test_slice["proba_-1"] = 0.0
        if "proba_1" not in test_slice.columns:
            test_slice["proba_1"] = 0.0

        feature_importance = dict(zip(FEATURE_COLUMNS, model.feature_importances_))

        fold_bounds.append({
            "fold": fold_num,
            "test_slice": test_slice,
            "feature_importance": feature_importance,
        })
        if verbose:
            print(
                f"دوره {fold_num} آموزش دید ({len(train_slice)} کندل) و روی "
                f"{test_slice['timestamp'].iloc[0].date()} تا {test_slice['timestamp'].iloc[-1].date()} تست شد."
            )
        start += retrain_step
    return fold_bounds


# ============================================================
# تولید معامله از سیگنال (هم برای مدل ML و هم برای قانون ساده)
# ============================================================

def trades_from_signaled_rows(dataset: pd.DataFrame, signaled: pd.DataFrame, fold_num) -> list:
    """از یک دیتافریم با ستون signal (1/-1)، لیست معاملات شبیه‌سازی‌شده با SL/TP می‌سازد."""
    trades = []
    for pos, row in signaled.iterrows():
        entry_price = row["close"]
        direction = int(row["signal"])
        atr_pct_at_entry = row["atr_pct"]
        exit_price, reason, bars_held = simulate_exit(
            dataset, pos, direction, entry_price, atr_pct_at_entry
        )
        raw_return = direction * (exit_price / entry_price - 1)
        net_return = raw_return - FEE_RATE_ROUNDTRIP
        trades.append({
            "entry_time": row["timestamp"],
            "entry_pos": pos,
            "fold": fold_num,
            "direction": direction,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "exit_reason": reason,
            "bars_held": bars_held,
            "return": net_return,
        })
    return trades


def run_ml_for_threshold(dataset: pd.DataFrame, fold_bounds: list, threshold: float) -> pd.DataFrame:
    """تولید معاملات با سیگنال مدل ML در یک آستانه‌ی اطمینان مشخص."""
    all_trades = []
    for fb in fold_bounds:
        test_slice = fb["test_slice"]
        sig = np.where(
            test_slice["proba_1"] >= threshold, 1,
            np.where(test_slice["proba_-1"] >= threshold, -1, 0),
        )
        signaled = test_slice.assign(signal=sig)
        signaled = signaled[signaled["signal"] != 0]
        all_trades.extend(trades_from_signaled_rows(dataset, signaled, fb["fold"]))
    return pd.DataFrame(all_trades)


def baseline_trend_signal(test_slice: pd.DataFrame) -> np.ndarray:
    """
    قانون ساده‌ی trend-following (بدون یادگیری ماشین) برای مقایسه با مدل:
    خرید وقتی EMA10 بالای SMA30 است و RSI در ناحیه‌ی مومنتوم صعودی (نه اشباع خرید).
    فروش وقتی برعکس این حالت باشد.
    این صرفاً یک قانون مرجع است؛ هدف فهمیدن این است که آیا مدل ML واقعاً
    بهتر از یک قانون پیش‌پاافتاده عمل می‌کند یا نه.
    """
    cond_buy = (
        (test_slice["ema_10"] > test_slice["sma_30"])
        & (test_slice["rsi_14"] > 50) & (test_slice["rsi_14"] < 70)
    )
    cond_sell = (
        (test_slice["ema_10"] < test_slice["sma_30"])
        & (test_slice["rsi_14"] < 50) & (test_slice["rsi_14"] > 30)
    )
    return np.where(cond_buy, 1, np.where(cond_sell, -1, 0))


def run_baseline(dataset: pd.DataFrame, fold_bounds: list) -> pd.DataFrame:
    """
    تولید معاملات با قانون ساده‌ی trend-following، با همان مکانیزم SL/TP و فولدها.
    برای هم‌راستا بودن با فرض «یک معامله در هر لحظه» که در محاسبه‌ی equity curve
    استفاده می‌شود، بعد از هر سیگنال پذیرفته‌شده حداقل MAX_HOLD_CANDLES کندل صبر
    می‌کنیم تا سیگنال بعدی را بپذیریم (بدون این کار، شرط ساده روی کندل‌های
    پشت‌سرهم پیوسته true می‌ماند و هزاران معامله‌ی هم‌پوشان کاذب تولید می‌شود).
    """
    all_trades = []
    for fb in fold_bounds:
        test_slice = fb["test_slice"]
        sig = baseline_trend_signal(test_slice)
        signaled = test_slice.assign(signal=sig)
        signaled = signaled[signaled["signal"] != 0]

        # فیلتر کردن سیگنال‌های هم‌پوشان: فقط یک سیگنال هر MAX_HOLD_CANDLES کندل
        non_overlapping_rows = []
        last_accepted_pos = -MAX_HOLD_CANDLES - 1
        for pos, row in signaled.iterrows():
            if pos - last_accepted_pos > MAX_HOLD_CANDLES:
                non_overlapping_rows.append((pos, row))
                last_accepted_pos = pos
        if non_overlapping_rows:
            filtered = pd.DataFrame([r for _, r in non_overlapping_rows],
                                     index=[p for p, _ in non_overlapping_rows])
            all_trades.extend(trades_from_signaled_rows(dataset, filtered, fb["fold"]))
    return pd.DataFrame(all_trades)


# ============================================================
# معیارها
# ============================================================

def compute_metrics(trades_df: pd.DataFrame):
    if trades_df is None or len(trades_df) == 0:
        return None

    trades_df = trades_df.sort_values("entry_time").reset_index(drop=True)
    returns = trades_df["return"].values

    win_rate = (returns > 0).mean()
    avg_return = returns.mean()
    profit_sum = returns[returns > 0].sum()
    loss_sum = -returns[returns < 0].sum()
    profit_factor = profit_sum / loss_sum if loss_sum > 0 else np.inf

    equity = (1 + returns).cumprod()
    running_max = np.maximum.accumulate(equity)
    drawdown = (equity - running_max) / running_max
    max_drawdown = drawdown.min()

    std_ret = returns.std()
    sharpe_per_trade = avg_return / std_ret if std_ret > 0 else np.nan
    n_days = (trades_df["entry_time"].iloc[-1] - trades_df["entry_time"].iloc[0]).days
    trades_per_year = len(trades_df) / (n_days / 365) if n_days > 0 else np.nan
    if not np.isnan(trades_per_year) and trades_per_year > 0 and not np.isnan(sharpe_per_trade):
        sharpe_annualized = sharpe_per_trade * np.sqrt(trades_per_year)
    else:
        sharpe_annualized = np.nan

    return {
        "n_trades": len(trades_df),
        "win_rate": win_rate,
        "avg_return": avg_return,
        "cumulative_return": equity[-1] - 1,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown,
        "sharpe_annualized": sharpe_annualized,
        "exit_counts": trades_df["exit_reason"].value_counts().to_dict(),
    }


def fmt(value, pattern="{:.2f}", suffix=""):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    if isinstance(value, float) and np.isinf(value):
        return "inf"
    return pattern.format(value) + suffix


def print_metrics_row(label: str, metrics: dict):
    if metrics is None:
        print(f"{label:>14} | بدون معامله")
        return
    print(
        f"{label:>14} | n={metrics['n_trades']:>4} | "
        f"Win%={fmt(metrics['win_rate']*100, '{:.1f}', '%'):>7} | "
        f"AvgRet={fmt(metrics['avg_return']*100, '{:.3f}', '%'):>8} | "
        f"Cumul={fmt(metrics['cumulative_return']*100, '{:.2f}', '%'):>8} | "
        f"PF={fmt(metrics['profit_factor'], '{:.2f}'):>5} | "
        f"MaxDD={fmt(metrics['max_drawdown']*100, '{:.2f}', '%'):>7} | "
        f"Sharpe~={fmt(metrics['sharpe_annualized'], '{:.2f}'):>6}"
    )


# ============================================================
# آزمون‌های آماری
# ============================================================

def bootstrap_test(trades_df: pd.DataFrame, n_bootstrap: int = 5000, seed: int = 42):
    rng = np.random.default_rng(seed)
    returns = trades_df["return"].values
    n = len(returns)

    boot_avg = np.empty(n_bootstrap)
    boot_cum = np.empty(n_bootstrap)
    boot_winrate = np.empty(n_bootstrap)

    for i in range(n_bootstrap):
        sample = rng.choice(returns, size=n, replace=True)
        boot_avg[i] = sample.mean()
        boot_cum[i] = np.prod(1 + sample) - 1
        boot_winrate[i] = (sample > 0).mean()

    def ci(arr, lo=2.5, hi=97.5):
        return np.percentile(arr, lo), np.percentile(arr, hi)

    return {
        "avg_return_ci": ci(boot_avg),
        "cumulative_return_ci": ci(boot_cum),
        "win_rate_ci": ci(boot_winrate),
        "prob_avg_return_positive": (boot_avg > 0).mean(),
    }


def _adaptive_n_perm(n_trades: int, target_inner_iterations: int = 150_000, cap: int = 3000, floor: int = 150) -> int:
    """
    تعداد تکرار permutation را متناسب با تعداد معاملات کم/زیاد می‌کند تا زمان اجرا
    محدود بماند. هر تکرار داخلی‌اش O(n_trades) کار دارد، پس هدف این است که
    n_perm * n_trades تقریباً ثابت (و قابل‌مدیریت) بماند.
    """
    if n_trades <= 0:
        return floor
    n_perm = target_inner_iterations // n_trades
    return int(max(floor, min(cap, n_perm)))
def direction_permutation_test(dataset: pd.DataFrame, trades_df: pd.DataFrame,
                                observed_cumulative: float, observed_avg: float,
                                n_perm: int = None, seed: int = 42):
    """همان لحظه‌های ورود را نگه می‌دارد، فقط جهت معامله را تصادفی می‌کند."""
    rng = np.random.default_rng(seed)
    n_trades = len(trades_df)
    if n_perm is None:
        n_perm = _adaptive_n_perm(n_trades)
    entry_positions = trades_df["entry_pos"].values.astype(int)
    entry_prices = trades_df["entry_price"].values
    atr_at_entry = dataset.iloc[entry_positions]["atr_pct"].values

    perm_cum = np.empty(n_perm)
    perm_avg = np.empty(n_perm)

    for p in range(n_perm):
        random_directions = rng.choice([-1, 1], size=n_trades)
        rets = np.empty(n_trades)
        for k in range(n_trades):
            exit_price, _, _ = simulate_exit(
                dataset, entry_positions[k], int(random_directions[k]),
                entry_prices[k], atr_at_entry[k],
            )
            raw_ret = random_directions[k] * (exit_price / entry_prices[k] - 1)
            rets[k] = raw_ret - FEE_RATE_ROUNDTRIP
        perm_cum[p] = np.prod(1 + rets) - 1
        perm_avg[p] = rets.mean()

    return {
        "p_value_cumulative": (perm_cum >= observed_cumulative).mean(),
        "p_value_avg_return": (perm_avg >= observed_avg).mean(),
        "perm_cum_mean": perm_cum.mean(),
        "n_perm_used": n_perm,
    }


def random_entry_test(dataset: pd.DataFrame, n_trades: int,
                       observed_cumulative: float, observed_avg: float,
                       train_window: int, n_perm: int = None, seed: int = 42):
    """لحظه و جهت کاملاً تصادفی (نه انتخاب مدل) با همان مکانیزم SL/TP."""
    rng = np.random.default_rng(seed)
    if n_perm is None:
        n_perm = _adaptive_n_perm(n_trades)
    n = len(dataset)
    valid_positions = np.arange(train_window, n - MAX_HOLD_CANDLES - 1)
    # پیش‌استخراج آرایه‌های خام برای جلوگیری از سربار iloc در حلقه‌ی داغ
    close_arr = dataset["close"].values
    atr_arr = dataset["atr_pct"].values

    perm_cum = np.empty(n_perm)
    perm_avg = np.empty(n_perm)

    for p in range(n_perm):
        positions = rng.choice(valid_positions, size=n_trades, replace=False)
        directions = rng.choice([-1, 1], size=n_trades)
        rets = np.empty(n_trades)
        for k in range(n_trades):
            pos = int(positions[k])
            entry_price = close_arr[pos]
            atr_pct = atr_arr[pos]
            exit_price, _, _ = simulate_exit(
                dataset, pos, int(directions[k]), entry_price, atr_pct,
            )
            raw_ret = directions[k] * (exit_price / entry_price - 1)
            rets[k] = raw_ret - FEE_RATE_ROUNDTRIP
        perm_cum[p] = np.prod(1 + rets) - 1
        perm_avg[p] = rets.mean()


    return {
        "p_value_cumulative": (perm_cum >= observed_cumulative).mean(),
        "p_value_avg_return": (perm_avg >= observed_avg).mean(),
        "perm_cum_mean": perm_cum.mean(),
        "n_perm_used": n_perm,
    }


def run_full_significance_report(dataset: pd.DataFrame, trades_df: pd.DataFrame,
                                  train_window: int, label: str = ""):
    """اجرای هر سه آزمون آماری روی یک مجموعه معامله و چاپ گزارش خوانا."""
    metrics = compute_metrics(trades_df)
    if metrics is None:
        print(f"[{label}] هیچ معامله‌ای صادر نشد.")
        return metrics, None

    print(f"\n--- آزمون‌های آماری برای: {label} (n={metrics['n_trades']} معامله) ---")

    # اگر نتیجه از قبل کاملاً فاجعه‌بار است (نزدیک به از دست دادن کل سرمایه)،
    # نیازی به آزمون آماری پرهزینه نیست - نتیجه از قبل روشن است.
    if metrics["cumulative_return"] <= -0.95:
        print("  ⚠️ بازده تجمعی <= -95% (عملاً نابودی سرمایه‌ی فرضی). آزمون آماری اضافی")
        print("     لازم نیست - این نتیجه به‌وضوح یک استراتژی زیان‌ده است، صرف‌نظر از شانس یا edge.")
        return metrics, {"significant": False, "skipped_reason": "catastrophic_loss"}

    n_perm = _adaptive_n_perm(metrics["n_trades"])
    if metrics["n_trades"] > 500:
        print(f"  (تعداد معاملات زیاد است [{metrics['n_trades']}]؛ برای مدیریت زمان اجرا، "
              f"تعداد تکرار permutation به {n_perm} کاهش یافت - همچنان برای این حجم نمونه کافی است)")

    boot = bootstrap_test(trades_df)
    avg_lo, avg_hi = boot["avg_return_ci"]
    print(f"  Bootstrap CI میانگین بازده: [{avg_lo*100:.3f}%, {avg_hi*100:.3f}%] "
          f"| احتمال مثبت بودن واقعی: {boot['prob_avg_return_positive']*100:.1f}%")

    dperm = direction_permutation_test(
        dataset, trades_df, metrics["cumulative_return"], metrics["avg_return"], n_perm=n_perm
    )
    print(f"  p-value شافل جهت: {dperm['p_value_cumulative']:.4f} (با {dperm['n_perm_used']} تکرار)")

    rperm = random_entry_test(
        dataset, metrics["n_trades"], metrics["cumulative_return"], metrics["avg_return"],
        train_window=train_window, n_perm=n_perm,
    )
    print(f"  p-value لحظه‌ی تصادفی: {rperm['p_value_cumulative']:.4f} (با {rperm['n_perm_used']} تکرار)")

    significant = (avg_lo > 0) and (dperm["p_value_cumulative"] < 0.05) and (rperm["p_value_cumulative"] < 0.05)
    verdict = "✅ معنی‌دار (در هر سه آزمون)" if significant else "⚠️ معنی‌دار نیست (حداقل یک آزمون رد شد)"
    print(f"  نتیجه: {verdict}")

    return metrics, {"bootstrap": boot, "direction_perm": dperm, "random_entry": rperm, "significant": significant}