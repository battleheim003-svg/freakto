"""
تست آماری معنی‌داری برای نتیجه‌ی آستانه‌ی 0.60 در Walk-Forward Backtest

این فایل کاملاً مستقل است (به walk_forward_backtest_v2.py وابسته نیست) تا مشکل
sync بودن نسخه‌ها پیش نیاید. فقط به config.py, data_fetcher.py, features.py نیاز دارد.

هدف: نتیجه‌ی فعلی در آستانه‌ی 0.60 (~51 معامله، Win rate ~45%، PF ~1.10،
بازده تجمعی ~3.35%) را با سه آزمون آماری می‌سنجیم تا ببینیم این عدد واقعاً
نشانه‌ی یک edge پایدار است یا می‌تواند صرفاً محصول شانس باشد - چون با فقط ~۵۰
معامله، نوسان آماری طبیعی می‌تواند به‌تنهایی چنین نتیجه‌ای تولید کند.

سه آزمون:

۱. Bootstrap Resampling روی بازده‌ی معاملات واقعی
   با resample-با-جایگذاری از همان بازده‌های واقعی، فاصله‌ی اطمینان ۹۵٪ برای
   میانگین بازده و بازده‌ی تجمعی می‌سازیم. اگر صفر داخل این بازه باشد، یعنی
   نمی‌توان با اطمینان آماری کافی گفت میانگین بازده واقعاً مثبت است.

۲. Permutation روی جهت معامله (Direction Shuffle)
   همان لحظه‌های دقیق ورود (با همان قیمت و ATR) را نگه می‌داریم، اما جهت
   معامله (خرید/فروش) را هزاران بار به‌صورت تصادفی 50/50 عوض می‌کنیم. این
   آزمون مشخص می‌کند آیا مدل واقعاً جهت درست بازار را تشخیص می‌دهد، یا فقط
   "زمان مناسب برای معامله" را خوب تشخیص داده (که می‌تواند به‌خاطر نوسان بالای
   آن لحظات باشد، نه پیش‌بینی جهت).

۳. لحظه‌های ورود کاملاً تصادفی (Random Entry-Time)
   به‌جای لحظه‌های انتخاب‌شده‌ی مدل، همان تعداد لحظه و جهت کاملاً تصادفی از کل
   داده انتخاب می‌شود. این آزمون مشخص می‌کند آیا اصلاً معامله‌کردن در این لحظه‌های
   خاص (با همین تنظیمات SL/TP) بهتر از معامله‌ی کاملاً تصادفی است.

برای آزمون‌های ۲ و ۳، یک p-value تقریبی گزارش می‌شود:
   p = (تعداد تکرارهای تصادفی با نتیجه‌ی >= نتیجه‌ی واقعی) / (کل تکرارها)
هرچه p کوچک‌تر (مثلا زیر 0.05)، شواهد قوی‌تری به نفع واقعی‌بودن edge داریم.

هشدار صادقانه: حتی اگر این آزمون‌ها نتیجه‌ی فعلی را تأیید کنند، با این تعداد
معامله روی فقط یک نماد/تایم‌فریم، باز هم برای اطمینان کامل کافی نیست.
اعتبارسنجی روی نمادها/تایم‌فریم‌های دیگر هم‌چنان توصیه می‌شود.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from config import TRAINING_CANDLES, TRAIN_WINDOW_CANDLES, RETRAIN_STEP_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import build_dataset, FEATURE_COLUMNS

# ---------- تنظیمات قابل تغییر ----------
THRESHOLD_TO_TEST = 0.60   # همان آستانه‌ای که نتیجه‌ی مثبت داد
SL_ATR_MULT = 1.0
TP_ATR_MULT = 1.5
MAX_HOLD_CANDLES = 12
FEE_RATE_ROUNDTRIP = 0.002
N_BOOTSTRAP = 5000
N_PERMUTATIONS = 3000
RANDOM_SEED = 42


# ============================================================
# بخش ۱: همان منطق walk-forward backtest (train + exit با SL/TP)
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


def build_fold_bounds(dataset: pd.DataFrame, n: int) -> list:
    fold_bounds = []
    start = TRAIN_WINDOW_CANDLES
    fold_num = 0
    while start + RETRAIN_STEP_CANDLES <= n:
        fold_num += 1
        train_slice = dataset.iloc[start - TRAIN_WINDOW_CANDLES:start]
        test_slice = dataset.iloc[start:start + RETRAIN_STEP_CANDLES].copy()

        model, scaler = train_one_fold(train_slice)
        X_test = scaler.transform(test_slice[FEATURE_COLUMNS].values)
        proba = model.predict_proba(X_test)
        for i, c in enumerate(model.classes_):
            test_slice[f"proba_{c}"] = proba[:, i]
        if "proba_-1" not in test_slice.columns:
            test_slice["proba_-1"] = 0.0
        if "proba_1" not in test_slice.columns:
            test_slice["proba_1"] = 0.0

        fold_bounds.append({"fold": fold_num, "test_slice": test_slice})
        print(
            f"دوره {fold_num} آموزش دید ({len(train_slice)} کندل) و روی "
            f"{test_slice['timestamp'].iloc[0].date()} تا {test_slice['timestamp'].iloc[-1].date()} تست شد."
        )
        start += RETRAIN_STEP_CANDLES
    return fold_bounds


def run_for_threshold(dataset: pd.DataFrame, fold_bounds: list, threshold: float) -> pd.DataFrame:
    all_trades = []
    for fb in fold_bounds:
        test_slice = fb["test_slice"]
        sig = np.where(
            test_slice["proba_1"] >= threshold, 1,
            np.where(test_slice["proba_-1"] >= threshold, -1, 0),
        )
        signaled = test_slice.assign(signal=sig)
        signaled = signaled[signaled["signal"] != 0]

        for pos, row in signaled.iterrows():
            entry_price = row["close"]
            direction = int(row["signal"])
            atr_pct_at_entry = row["atr_pct"]
            exit_price, reason, bars_held = simulate_exit(
                dataset, pos, direction, entry_price, atr_pct_at_entry
            )
            raw_return = direction * (exit_price / entry_price - 1)
            net_return = raw_return - FEE_RATE_ROUNDTRIP
            all_trades.append({
                "entry_time": row["timestamp"],
                "entry_pos": pos,
                "fold": fb["fold"],
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "exit_reason": reason,
                "bars_held": bars_held,
                "return": net_return,
            })

    return pd.DataFrame(all_trades)


def compute_metrics(trades_df: pd.DataFrame):
    if trades_df is None or len(trades_df) == 0:
        return None
    trades_df = trades_df.sort_values("entry_time").reset_index(drop=True)
    returns = trades_df["return"].values
    win_rate = (returns > 0).mean()
    avg_return = returns.mean()
    equity = (1 + returns).cumprod()
    return {
        "n_trades": len(trades_df),
        "win_rate": win_rate,
        "avg_return": avg_return,
        "cumulative_return": equity[-1] - 1,
    }


def fmt(value, pattern="{:.2f}", suffix=""):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "—"
    return pattern.format(value) + suffix


# ============================================================
# بخش ۲: آزمون‌های آماری
# ============================================================

def bootstrap_test(trades_df: pd.DataFrame, n_bootstrap: int = N_BOOTSTRAP, seed: int = RANDOM_SEED):
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


def direction_permutation_test(dataset: pd.DataFrame, trades_df: pd.DataFrame,
                                observed_cumulative: float, observed_avg: float,
                                n_perm: int = N_PERMUTATIONS, seed: int = RANDOM_SEED):
    """همان لحظه‌های ورود را نگه می‌دارد، فقط جهت معامله را تصادفی می‌کند."""
    rng = np.random.default_rng(seed)
    n_trades = len(trades_df)
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
    }


def random_entry_test(dataset: pd.DataFrame, n_trades: int,
                       observed_cumulative: float, observed_avg: float,
                       n_perm: int = N_PERMUTATIONS, seed: int = RANDOM_SEED):
    """لحظه و جهت کاملاً تصادفی (نه انتخاب مدل) با همان مکانیزم SL/TP."""
    rng = np.random.default_rng(seed)
    n = len(dataset)
    valid_positions = np.arange(TRAIN_WINDOW_CANDLES, n - MAX_HOLD_CANDLES - 1)

    perm_cum = np.empty(n_perm)
    perm_avg = np.empty(n_perm)

    for p in range(n_perm):
        positions = rng.choice(valid_positions, size=n_trades, replace=False)
        directions = rng.choice([-1, 1], size=n_trades)
        rets = np.empty(n_trades)
        for k in range(n_trades):
            pos = int(positions[k])
            entry_price = dataset.iloc[pos]["close"]
            atr_pct = dataset.iloc[pos]["atr_pct"]
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
    }


# ============================================================
# بخش ۳: اجرای کامل
# ============================================================

def run():
    print(f"در حال دریافت {TRAINING_CANDLES} کندل تاریخی (ممکن است کمی طول بکشد)...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)
    dataset = build_dataset(raw, for_training=True)
    dataset = dataset.reset_index()
    n = len(dataset)
    print(f"تعداد کل کندل‌های قابل‌استفاده: {n}\n")

    print("در حال آموزش فولدها (walk-forward)...")
    fold_bounds = build_fold_bounds(dataset, n)

    trades_df = run_for_threshold(dataset, fold_bounds, THRESHOLD_TO_TEST)
    metrics = compute_metrics(trades_df)
    if metrics is None:
        print(f"هیچ معامله‌ای در آستانه‌ی {THRESHOLD_TO_TEST} صادر نشد.")
        return

    print(f"\n=== نتیجه‌ی واقعی در آستانه‌ی {THRESHOLD_TO_TEST} ===")
    print(f"تعداد معاملات: {metrics['n_trades']}")
    print(f"Win rate: {fmt(metrics['win_rate']*100, '{:.1f}', '%')}")
    print(f"میانگین بازده هر معامله: {fmt(metrics['avg_return']*100, '{:.3f}', '%')}")
    print(f"بازده تجمعی: {fmt(metrics['cumulative_return']*100, '{:.2f}', '%')}")

    # ---- آزمون ۱: Bootstrap ----
    print(f"\n=== آزمون ۱: Bootstrap Resampling ({N_BOOTSTRAP} تکرار) ===")
    boot = bootstrap_test(trades_df)
    avg_lo, avg_hi = boot["avg_return_ci"]
    cum_lo, cum_hi = boot["cumulative_return_ci"]
    wr_lo, wr_hi = boot["win_rate_ci"]
    print(f"فاصله‌ی اطمینان 95% میانگین بازده هر معامله: [{avg_lo*100:.3f}%, {avg_hi*100:.3f}%]")
    print(f"فاصله‌ی اطمینان 95% بازده تجمعی: [{cum_lo*100:.2f}%, {cum_hi*100:.2f}%]")
    print(f"فاصله‌ی اطمینان 95% win rate: [{wr_lo*100:.1f}%, {wr_hi*100:.1f}%]")
    print(f"احتمال اینکه میانگین بازده واقعاً مثبت باشد: {boot['prob_avg_return_positive']*100:.1f}%")
    if avg_lo <= 0:
        print("⚠️ صفر داخل بازه‌ی اطمینان میانگین بازده است؛ یعنی با این حجم نمونه نمی‌توان")
        print("   با اطمینان ۹۵٪ گفت میانگین بازده واقعی مدل مثبت است.")
    else:
        print("✅ صفر خارج از بازه‌ی اطمینان است؛ شاهدی به نفع مثبت‌بودن واقعی میانگین بازده.")

    # ---- آزمون ۲: Direction Permutation ----
    print(f"\n=== آزمون ۲: Permutation روی جهت معامله ({N_PERMUTATIONS} تکرار) ===")
    print("(همان لحظه‌های ورود مدل حفظ می‌شود؛ فقط جهت خرید/فروش تصادفی می‌شود)")
    dperm = direction_permutation_test(
        dataset, trades_df, metrics["cumulative_return"], metrics["avg_return"]
    )
    print(f"میانگین بازده تجمعی در حالت جهت تصادفی: {dperm['perm_cum_mean']*100:.2f}%")
    print(f"p-value (بازده تجمعی): {dperm['p_value_cumulative']:.4f}")
    print(f"p-value (میانگین بازده): {dperm['p_value_avg_return']:.4f}")
    if dperm["p_value_cumulative"] < 0.05:
        print("✅ نتیجه‌ی واقعی بهتر از ۹۵٪ حالت‌های تصادفی است؛ شاهدی به نفع اینکه مدل")
        print("   واقعاً جهت بازار را بهتر از شانس تشخیص می‌دهد، نه فقط زمان معامله را.")
    else:
        print("⚠️ نتیجه‌ی واقعی از نظر آماری قابل تمایز از حدس تصادفی جهت نیست.")

    # ---- آزمون ۳: Random Entry-Time ----
    print(f"\n=== آزمون ۳: لحظه‌های ورود کاملاً تصادفی ({N_PERMUTATIONS} تکرار) ===")
    print("(به‌جای لحظه‌های انتخاب‌شده‌ی مدل، لحظه و جهت کاملاً تصادفی)")
    rperm = random_entry_test(
        dataset, metrics["n_trades"], metrics["cumulative_return"], metrics["avg_return"]
    )
    print(f"میانگین بازده تجمعی در حالت کاملاً تصادفی: {rperm['perm_cum_mean']*100:.2f}%")
    print(f"p-value (بازده تجمعی): {rperm['p_value_cumulative']:.4f}")
    print(f"p-value (میانگین بازده): {rperm['p_value_avg_return']:.4f}")
    if rperm["p_value_cumulative"] < 0.05:
        print("✅ نتیجه‌ی واقعی بهتر از ۹۵٪ معامله‌های کاملاً تصادفی (زمان و جهت) است.")
    else:
        print("⚠️ نتیجه‌ی واقعی از نظر آماری قابل تمایز از معامله‌ی کاملاً تصادفی نیست.")

    print("\n=== جمع‌بندی ===")
    print("اگر هر سه آزمون بالا p-value پایین (مثلا زیر 0.05) نشان دهند و صفر در فاصله‌ی")
    print("اطمینان Bootstrap نباشد، شواهد به‌نفع یک edge واقعی (هرچند کوچک) قوی‌تر می‌شود.")
    print("اگر حتی یکی از آزمون‌ها رد شود، با این حجم نمونه نمی‌توان با اطمینان گفت")
    print("استراتژی edge واقعی دارد - این لزوماً یعنی استراتژی بی‌فایده است، اما یعنی")
    print("شواهد فعلی برای اثبات آن کافی نیست.")


if __name__ == "__main__":
    run()