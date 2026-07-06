"""
triple_barrier.py — بازتعریف لیبل با روش Triple-Barrier

مشکل لیبل‌گذاری فعلی (در features.py):
  برچسب صرفاً بر اساس قیمت *دقیقاً* در کندل LOOKAHEAD_CANDLES=3 آینده تعیین
  می‌شود، بدون توجه به مسیر قیمت در این فاصله. یعنی حتی اگر قیمت در کندل ۱ به
  اندازه‌ی زیادی بالا برود و در کندل ۳ برگردد، لیبل می‌تواند صفر یا حتی منفی
  باشد - در حالی که یک معامله‌ی واقعی با TP در کندل ۱ می‌بست و سود می‌کرد.
  این ناهم‌خوانی بین "چیزی که مدل یاد می‌گیرد" و "چیزی که در عمل اتفاق می‌افتد"
  می‌تواند بخشی از دلیل AUC≈0.50 در edge_diagnostic.py باشد.

روش Triple-Barrier (ایده از کتاب Advances in Financial Machine Learning،
مارکوس لوپز د پرادو):
  برای هر کندل، سه "مرز" تعریف می‌شود:
    1. مرز بالا (Take-Profit): entry_price + TP_ATR_MULT × ATR
    2. مرز پایین (Stop-Loss):   entry_price - SL_ATR_MULT × ATR
    3. مرز زمانی (Vertical):    MAX_HOLD_CANDLES کندل بعد

  لیبل = هر کدام که زودتر لمس شود:
    +1  اگر مرز بالا اول لمس شود (شبیه‌سازی یک معامله‌ی خرید موفق)
    -1  اگر مرز پایین اول لمس شود (شبیه‌سازی یک معامله‌ی فروش/ضرر)
     0  اگر تا پایان MAX_HOLD_CANDLES هیچ‌کدام لمس نشود

  نکته‌ی مهم: این SL_ATR_MULT/TP_ATR_MULT/MAX_HOLD_CANDLES دقیقاً همان
  مقادیری هستند که در strategy_core.py برای شبیه‌سازی خروج واقعی معامله
  استفاده می‌شوند - یعنی حالا مدل دقیقاً دارد همان چیزی را یاد می‌گیرد که
  قرار است در عمل از آن استفاده شود.

  محدودیت شناخته‌شده (برای شفافیت): اگر در یک کندل هم مرز بالا و هم مرز
  پایین لمس شوند (نوسان شدید داخل یک کندل)، طبق قرارداد simulate_exit در
  strategy_core.py، اولویت با SL است (محافظه‌کارانه). هم‌چنین این پیاده‌سازی
  ساده‌شده است و وزن‌دهی بر اساس همپوشانی نمونه‌ها (sample uniqueness،
  به‌شکلی که در نسخه‌ی کامل روش لوپز د پرادو توصیه می‌شود) را انجام نمی‌دهد.
"""

import numpy as np
import pandas as pd

from features import add_features, FEATURE_COLUMNS
from strategy_core import SL_ATR_MULT, TP_ATR_MULT, MAX_HOLD_CANDLES


def compute_triple_barrier_labels(df: pd.DataFrame, sl_mult: float = SL_ATR_MULT,
                                   tp_mult: float = TP_ATR_MULT,
                                   max_hold: int = MAX_HOLD_CANDLES) -> pd.DataFrame:
    """
    df باید ستون‌های close, high, low, atr_pct را داشته باشد (خروجی add_features).
    خروجی: همان df با دو ستون اضافه: label (-1/0/1) و label_touch_bars (چند کندل
    طول کشید تا لیبل تعیین شود؛ برای تشخیص/دیباگ مفید است).
    ردیف‌های انتهایی که به‌اندازه‌ی max_hold کندل آینده ندارند، NaN می‌مانند
    (باید بعداً dropna شوند - دقیقاً مثل رویه‌ی فعلی در features.build_dataset).
    """
    df = df.copy()
    n = len(df)
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    atr_pct = df["atr_pct"].values

    labels = np.full(n, np.nan)
    touch_bars = np.full(n, np.nan)

    for i in range(n - max_hold):
        a = atr_pct[i]
        if np.isnan(a) or a <= 0:
            continue
        entry_price = close[i]
        atr_price = a * entry_price
        upper = entry_price + tp_mult * atr_price
        lower = entry_price - sl_mult * atr_price

        label = 0.0
        touch = float(max_hold)
        for j in range(i + 1, i + max_hold + 1):
            hit_lower = low[j] <= lower   # اولویت با SL (هم‌راستا با simulate_exit)
            hit_upper = high[j] >= upper
            if hit_lower:
                label = -1.0
                touch = float(j - i)
                break
            if hit_upper:
                label = 1.0
                touch = float(j - i)
                break
        labels[i] = label
        touch_bars[i] = touch

    df["label"] = labels
    df["label_touch_bars"] = touch_bars
    return df


def build_dataset_triple_barrier(raw_df: pd.DataFrame, sl_mult: float = SL_ATR_MULT,
                                  tp_mult: float = TP_ATR_MULT,
                                  max_hold: int = MAX_HOLD_CANDLES) -> pd.DataFrame:
    """
    نسخه‌ی جایگزین features.build_dataset که به‌جای لیبل افق‌ثابت، از
    triple-barrier استفاده می‌کند. فیچرهای تکنیکال دقیقاً همان فیچرهای قبلی
    هستند (از features.add_features استفاده می‌شود)، فقط روش لیبل‌گذاری فرق دارد.
    """
    df = add_features(raw_df)
    df = compute_triple_barrier_labels(df, sl_mult=sl_mult, tp_mult=tp_mult, max_hold=max_hold)
    df = df.dropna(subset=FEATURE_COLUMNS + ["label"])
    df["label"] = df["label"].astype(int)
    return df


def label_distribution_report(df: pd.DataFrame):
    """گزارش سریع توزیع کلاس‌ها و میانگین طول عمر معامله تا لمس مرز."""
    dist = df["label"].value_counts(normalize=True).sort_index()
    print("توزیع لیبل‌های triple-barrier:")
    for cls, frac in dist.items():
        name = {1: "صعودی (TP اول خورد)", -1: "نزولی (SL اول خورد)", 0: "خنثی (تا سقف زمانی هیچ‌کدام)"}.get(cls, str(cls))
        print(f"  {name}: {frac*100:.1f}%")
    if "label_touch_bars" in df.columns:
        print(f"میانگین تعداد کندل تا لمس مرز: {df['label_touch_bars'].mean():.2f}")
