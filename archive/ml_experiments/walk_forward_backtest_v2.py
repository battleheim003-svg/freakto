"""
نسخه‌ی پیشرفته‌ی Walk-Forward Backtest

نسبت به walk_forward_backtest.py اصلی، سه تغییر اضافه شده:

1. مقایسه‌ی هم‌زمان چند آستانه‌ی اطمینان (CONFIDENCE_THRESHOLDS) به‌جای یک
   MIN_CONFIDENCE ثابت - تا ببینیم آستانه‌ی فعلی (0.60) بیش‌ازحد سخت‌گیرانه است یا نه.
2. خروج از معامله بر اساس Stop Loss / Take Profit واقعی (مبتنی بر ATR لحظه‌ی
   ورود)، نه صرفاً گذشت تعداد ثابتی کندل. هر معامله تا برخورد قیمت به SL یا
   TP، یا رسیدن به سقف زمانی MAX_HOLD_CANDLES، دنبال می‌شود.
3. معیارهای ریسک: Max Drawdown، Profit Factor، و Sharpe تقریبی (بر مبنای
   معاملات، نه روزانه) به گزارش اضافه شده.

این فایل عمداً جدا از walk_forward_backtest.py اصلی نگه داشته شده تا نسخه‌ی
فعلی‌ات دست‌نخورده بماند. بعد از بررسی نتایج، اگر راضی بودی می‌توانیم آن را
جایگزین نسخه‌ی اصلی کنیم یا تنظیمات نهایی را در config.py ثابت کنیم.

محدودیت مهم: منحنی سرمایه با فرض «یک معامله در هر لحظه و بدون هم‌پوشانی»
محاسبه می‌شود (دقیقاً مثل نسخه‌ی اصلی پروژه). اگر MAX_HOLD_CANDLES طولانی
باشد و سیگنال‌ها نزدیک به هم صادر شوند، ممکن است در عمل چند معامله هم‌زمان
باز باشد که این نسخه آن را مدل نمی‌کند.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from config import TRAINING_CANDLES, TRAIN_WINDOW_CANDLES, RETRAIN_STEP_CANDLES
from data_fetcher import fetch_ohlcv_extended
from features import build_dataset, FEATURE_COLUMNS

# ---------- تنظیمات قابل تغییر این نسخه ----------
CONFIDENCE_THRESHOLDS = [0.40, 0.45, 0.50, 0.55, 0.60]  # آستانه‌هایی که مقایسه می‌شوند
SL_ATR_MULT = 1.0       # فاصله‌ی حد ضرر = این عدد × ATR لحظه‌ی ورود
TP_ATR_MULT = 1.5       # فاصله‌ی حد سود = این عدد × ATR لحظه‌ی ورود (R:R تقریبی 1:1.5)
MAX_HOLD_CANDLES = 12    # حداکثر تعداد کندلی که اگر نه SL نه TP خورد، با قیمت بسته می‌شویم
FEE_RATE_ROUNDTRIP = 0.002  # کارمزد رفت‌وبرگشت (هر طرف ~0.1% فرض شده)


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
    """
    شبیه‌سازی خروج واقعی از معامله با SL/TP، به‌جای خروج زمانی ثابت.

    dataset: کل دیتافریم با index پیوسته‌ی 0..n-1 (بعد از reset_index) و
             ستون‌های خام high/low/close.
    entry_pos: موقعیت کندل سیگنال (محل ورود) در dataset.
    direction: 1 برای خرید، -1 برای فروش.

    خروجی: (exit_price, exit_reason, bars_held)
    exit_reason یکی از: "SL", "TP", "TIME"
    """
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

        # اگر هر دو در یک کندل اتفاق بیفتند، برای محافظه‌کاری فرض می‌کنیم SL اول خورده
        if hit_sl:
            return sl_price, "SL", pos - entry_pos
        if hit_tp:
            return tp_price, "TP", pos - entry_pos

    exit_price = dataset.iloc[last_pos]["close"]
    return exit_price, "TIME", last_pos - entry_pos


def run_for_threshold(dataset: pd.DataFrame, fold_bounds: list, threshold: float) -> pd.DataFrame:
    """برای یک آستانه‌ی مشخص، تمام معاملات همه‌ی فولدها را شبیه‌سازی می‌کند."""
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
    profit_sum = returns[returns > 0].sum()
    loss_sum = -returns[returns < 0].sum()
    profit_factor = profit_sum / loss_sum if loss_sum > 0 else np.inf

    # منحنی سرمایه (فرض: معاملات پشت‌سرهم و بدون هم‌پوشانی اعمال می‌شوند)
    equity = (1 + returns).cumprod()
    running_max = np.maximum.accumulate(equity)
    drawdown = (equity - running_max) / running_max
    max_drawdown = drawdown.min()

    # Sharpe تقریبی: بر مبنای معامله محاسبه و سپس با تعداد معامله در سال annualize می‌شود
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
    if np.isinf(value):
        return "inf"
    return pattern.format(value) + suffix


def run():
    print(f"در حال دریافت {TRAINING_CANDLES} کندل تاریخی (ممکن است کمی طول بکشد)...")
    raw = fetch_ohlcv_extended(total_candles=TRAINING_CANDLES)

    dataset = build_dataset(raw, for_training=True)
    dataset = dataset.reset_index()
    n = len(dataset)
    print(f"تعداد کل کندل‌های قابل‌استفاده (بعد از حذف NaN): {n}\n")

    if n < TRAIN_WINDOW_CANDLES + RETRAIN_STEP_CANDLES:
        print(
            "داده‌ی کافی برای walk-forward با این تنظیمات وجود ندارد.\n"
            "TRAINING_CANDLES را در config.py افزایش بده یا TRAIN_WINDOW_CANDLES را کاهش بده."
        )
        return

    # ---- مرحله ۱: مدل هر فولد را فقط یک‌بار آموزش بده و احتمال‌ها را محاسبه کن ----
    # (چون آموزش مدل به آستانه بستگی ندارد، نباید برای هر آستانه دوباره آموزش بدهیم)
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

    # ---- مرحله ۲: برای هر آستانه، معاملات و معیارهای ریسک را با SL/TP واقعی حساب کن ----
    print("\n=== مقایسه‌ی آستانه‌های اطمینان (با خروج واقعی SL/TP) ===")
    header = (f"{'Threshold':>10} | {'تعداد':>6} | {'Win%':>7} | {'AvgRet':>8} | "
              f"{'Cumul':>8} | {'PF':>6} | {'MaxDD':>7} | {'Sharpe~':>8}")
    print(header)
    print("-" * len(header))

    results = {}
    for th in CONFIDENCE_THRESHOLDS:
        trades_df = run_for_threshold(dataset, fold_bounds, th)
        metrics = compute_metrics(trades_df)
        results[th] = (trades_df, metrics)
        if metrics is None:
            print(f"{th:>10.2f} | {'0':>6} | {'—':>7} | {'—':>8} | {'—':>8} | {'—':>6} | {'—':>7} | {'—':>8}")
            continue
        print(
            f"{th:>10.2f} | {metrics['n_trades']:>6} | "
            f"{fmt(metrics['win_rate']*100, '{:.1f}', '%'):>7} | "
            f"{fmt(metrics['avg_return']*100, '{:.3f}', '%'):>8} | "
            f"{fmt(metrics['cumulative_return']*100, '{:.2f}', '%'):>8} | "
            f"{fmt(metrics['profit_factor'], '{:.2f}'):>6} | "
            f"{fmt(metrics['max_drawdown']*100, '{:.2f}', '%'):>7} | "
            f"{fmt(metrics['sharpe_annualized'], '{:.2f}'):>8}"
        )

    print(
        "\nراهنمای ستون‌ها: Win% = درصد معاملات برنده | AvgRet = میانگین بازده هر معامله "
        "| Cumul = بازده تجمعی فرضی | PF = Profit Factor (هرچه بالاتر از 1، بهتر) "
        "| MaxDD = بدترین افت سرمایه از قله تا دره | Sharpe~ = نسبت ریسک به بازده تقریبی"
    )

    # ---- جزئیات بیشتر برای پایین‌ترین آستانه (معمولاً بیشترین تعداد معامله را دارد) ----
    best_th = min(CONFIDENCE_THRESHOLDS)
    trades_df, metrics = results[best_th]
    if metrics:
        print(f"\n=== جزئیات بیشتر برای آستانه {best_th} (بیشترین تعداد معامله) ===")
        print(f"دلایل خروج از معامله: {metrics['exit_counts']}")
        print("(SL = حد ضرر خورد، TP = حد سود خورد، TIME = نه SL نه TP، با گذشت سقف زمانی خارج شدیم)")
        print(f"میانگین تعداد کندل نگه‌داری معامله: {trades_df['bars_held'].mean():.1f}")

    print(
        "\nهشدار: این هم‌چنان شبیه‌سازی است؛ اسپرد و slippage واقعی صرافی، و هم‌پوشانی"
        " احتمالی چند معامله‌ی هم‌زمان را به‌طور کامل مدل نمی‌کند."
    )


if __name__ == "__main__":
    run()