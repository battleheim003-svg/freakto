"""
ساخت فیچرها (ویژگی‌ها) برای مدل، با استفاده از اندیکاتورهای تکنیکال رایج.
کتابخونه‌ی `ta` خالص پایتون است و نیازی به نصب پیچیده (مثل TA-Lib) ندارد.
"""

import pandas as pd
import ta
from config import LOOKAHEAD_CANDLES, ATR_MULTIPLIER
from engine.model_contract import FEATURE_SET_VERSION


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # میانگین‌های متحرک
    df["sma_10"] = ta.trend.sma_indicator(df["close"], window=10)
    df["sma_30"] = ta.trend.sma_indicator(df["close"], window=30)
    df["ema_10"] = ta.trend.ema_indicator(df["close"], window=10)

    # RSI
    df["rsi_14"] = ta.momentum.rsi(df["close"], window=14)

    # MACD
    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_diff"] = macd.macd_diff()

    # باندهای بولینگر
    bb = ta.volatility.BollingerBands(df["close"])
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()
    df["bb_width"] = (df["bb_high"] - df["bb_low"]) / df["close"]

    # ATR: میانگین دامنه‌ی نوسان واقعی - معیار "نوسان طبیعی" بازار در این لحظه
    atr = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14)
    df["atr_pct"] = atr.average_true_range() / df["close"]

    # نوسان (volatility) و حجم نسبی
    df["volatility"] = df["close"].pct_change().rolling(10).std()
    df["volume_change"] = df["volume"].pct_change()

    # فاصله‌ی نسبی قیمت از میانگین‌ها (نرمال‌سازی شده)
    df["dist_sma_10"] = (df["close"] - df["sma_10"]) / df["close"]
    df["dist_sma_30"] = (df["close"] - df["sma_30"]) / df["close"]

    # Metadata is kept in attrs so it cannot accidentally become a model
    # feature, while every caller can still persist the exact feature contract.
    df.attrs["feature_set_version"] = FEATURE_SET_VERSION
    df.attrs["feature_time_basis"] = "BAR_CLOSE_CAUSAL"

    return df


def add_funding_rate_features(df: pd.DataFrame, funding_df: pd.DataFrame) -> pd.DataFrame:
    """
    ادغام داده‌ی Funding Rate با دیتاست اصلی (بر اساس نزدیک‌ترین زمان قبلی).
    funding_df باید index زمانی و ستون funding_rate داشته باشد
    (خروجی futures_data_fetcher.fetch_funding_rate_history).

    فیچرهای ساخته‌شده:
    - funding_rate: آخرین نرخ تسویه‌شده تا این لحظه
    - funding_rate_ma: میانگین ۳ تسویه‌ی اخیر (روند کلی احساسات اهرمی بازار)
    """
    df = df.copy()
    if funding_df is None or funding_df.empty:
        df["funding_rate"] = 0.0
        df["funding_rate_ma"] = 0.0
        return df

    funding_sorted = funding_df.sort_index()
    merged = pd.merge_asof(
        df.sort_index(), funding_sorted, left_index=True, right_index=True, direction="backward"
    )
    merged["funding_rate"] = merged["funding_rate"].fillna(0.0)
    merged["funding_rate_ma"] = merged["funding_rate"].rolling(3, min_periods=1).mean()
    return merged


def add_oi_longshort_features(df: pd.DataFrame, oi_df: pd.DataFrame = None,
                               longshort_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    ادغام داده‌ی Open Interest و Long/Short Ratio با دیتاست اصلی.
    چون این داده‌ها فقط ~۳۰ روز تاریخچه دارند، این تابع معمولاً روی یک
    بازه‌ی کوتاه (نه کل TRAINING_CANDLES) استفاده می‌شود.

    فیچرهای ساخته‌شده:
    - oi_change: درصد تغییر Open Interest نسبت به کندل قبل
    - long_short_ratio: نسبت حساب‌های لانگ به شورت
    - long_short_ratio_change: تغییر این نسبت نسبت به کندل قبل
    """
    df = df.copy()

    if oi_df is not None and not oi_df.empty:
        oi_sorted = oi_df.sort_index()
        df = pd.merge_asof(df.sort_index(), oi_sorted[["open_interest"]],
                            left_index=True, right_index=True, direction="backward")
        df["oi_change"] = df["open_interest"].pct_change()
    else:
        df["open_interest"] = None
        df["oi_change"] = None

    if longshort_df is not None and not longshort_df.empty:
        ls_sorted = longshort_df.sort_index()
        df = pd.merge_asof(df.sort_index(), ls_sorted[["long_short_ratio"]],
                            left_index=True, right_index=True, direction="backward")
        df["long_short_ratio_change"] = df["long_short_ratio"].pct_change()
    else:
        df["long_short_ratio"] = None
        df["long_short_ratio_change"] = None

    return df


def add_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    لیبل (target) برای آموزش مدل:
    1  -> قیمت در آینده بیشتر از نوسان طبیعی بازار (ATR) بالا می‌رود (سیگنال خرید)
    -1 -> قیمت در آینده بیشتر از نوسان طبیعی بازار (ATR) پایین می‌آید (سیگنال فروش)
    0  -> تغییر در محدوده‌ی نوسان عادی بازار است (بدون سیگنال)

    به‌جای یک درصد ثابت (مثلا همیشه 0.3%)، آستانه نسبت به ATR لحظه‌ای تنظیم
    می‌شود؛ یعنی در بازار آرام آستانه کوچک‌تر و در بازار پرنوسان آستانه بزرگ‌تر
    می‌شود. این منطقی‌تر از یک عدد ثابت برای همه‌ی شرایط بازار است.
    """
    df = df.copy()
    future_return = df["close"].shift(-LOOKAHEAD_CANDLES) / df["close"] - 1
    dynamic_threshold = df["atr_pct"] * ATR_MULTIPLIER

    df["future_return"] = future_return
    df["label"] = 0
    df.loc[future_return >= dynamic_threshold, "label"] = 1
    df.loc[future_return <= -dynamic_threshold, "label"] = -1

    return df


FEATURE_COLUMNS = [
    "sma_10", "sma_30", "ema_10", "rsi_14",
    "macd", "macd_signal", "macd_diff",
    "bb_width", "atr_pct", "volatility", "volume_change",
    "dist_sma_10", "dist_sma_30",
]

# وقتی funding rate ادغام شده باشد، این ستون‌ها هم به فیچرها اضافه می‌شوند
FUNDING_FEATURE_COLUMNS = ["funding_rate", "funding_rate_ma"]

# وقتی OI/Long-Short ادغام شده باشد، این ستون‌ها هم اضافه می‌شوند
OI_LONGSHORT_FEATURE_COLUMNS = ["oi_change", "long_short_ratio", "long_short_ratio_change"]


def build_dataset(df: pd.DataFrame, for_training: bool = True, funding_df: pd.DataFrame = None,
                   oi_df: pd.DataFrame = None, longshort_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    ساخت دیتاست نهایی: فیچرها + (در صورت آموزش) لیبل‌ها.
    ردیف‌هایی که فیچر یا لیبل آن‌ها NaN است حذف می‌شوند.

    اگر funding_df داده شود، ستون‌های funding_rate و funding_rate_ma هم اضافه می‌شوند.
    اگر oi_df و/یا longshort_df داده شود، ستون‌های مربوط به آن‌ها هم اضافه می‌شوند.
    """
    df = add_features(df)

    feature_cols = list(FEATURE_COLUMNS)
    if funding_df is not None:
        df = add_funding_rate_features(df, funding_df)
        feature_cols = feature_cols + FUNDING_FEATURE_COLUMNS

    if oi_df is not None or longshort_df is not None:
        df = add_oi_longshort_features(df, oi_df=oi_df, longshort_df=longshort_df)
        feature_cols = feature_cols + OI_LONGSHORT_FEATURE_COLUMNS

    if for_training:
        df = add_labels(df)
        df = df.dropna(subset=feature_cols + ["label"])
    else:
        df = df.dropna(subset=feature_cols)
    return df
