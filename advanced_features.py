"""
advanced_features.py - سیستم فیچر پیشرفتهی Modular

این فایل تمام فیچرهای جدید رو دارا است:
  - Market Structure (Support/Resistance, Trends)
  - Order Flow (Volume Imbalance, CVD)
  - Volume Profile
  - Liquidity Metrics
  - Fair Value Gap Detection
  - Funding/OI Features
  - Liquidation Flow
  - VWAP & Price Action
  
هر دسته فیچر در یک تابع جداگانه برای modularity.
می‌تونی در config.py تنظیم کنی کدام فیچرها فعال باشند.
"""

import numpy as np
import pandas as pd
import ta
from typing import Dict, List, Tuple


# ============================================================
# ۱. MARKET STRUCTURE FEATURES
# ============================================================

def detect_market_structure(df: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """
    تشخیص ساختار بازار: Trend، Consolidation، Reversal Points
    
    فیچرهای خروجی:
    - trend_direction: -1 (Down), 0 (Side), 1 (Up)
    - structure_strength: 0-1 (قوت ترند)
    - support_level: نزدیکترین مقاومت پایین
    - resistance_level: نزدیکترین مقاومت بالا
    - market_regime: 'strong_up', 'weak_up', 'consolidation', 'weak_down', 'strong_down'
    """
    df = df.copy()
    
    # میانگین متحرک برای تشخیص جهت
    df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
    df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
    
    # Higher High/Lower Low (HH/LL) برای تشخیص ترند
    df['high_rollmax'] = df['high'].rolling(lookback).max()
    df['low_rollmin'] = df['low'].rolling(lookback).min()
    
    # جهت ترند
    df['trend_direction'] = 0
    df.loc[df['sma_20'] > df['sma_50'], 'trend_direction'] = 1
    df.loc[df['sma_20'] < df['sma_50'], 'trend_direction'] = -1
    
    # قوت ترند (چقدر HH/LL پی‌درپی شدند)
    hh_count = (df['high'] > df['high_rollmax'].shift(1)).rolling(5).sum()
    ll_count = (df['low'] < df['low_rollmin'].shift(1)).rolling(5).sum()
    df['structure_strength'] = (hh_count + ll_count) / 10  # normalize to 0-1
    
    # Support/Resistance
    df['support_level'] = df['low'].rolling(lookback).min()
    df['resistance_level'] = df['high'].rolling(lookback).max()
    
    # Market Regime
    def assign_regime(row):
        strength = row['structure_strength']
        direction = row['trend_direction']
        if direction == 1:
            return 'strong_up' if strength > 0.5 else 'weak_up'
        elif direction == -1:
            return 'strong_down' if strength > 0.5 else 'weak_down'
        else:
            return 'consolidation'
    
    df['market_regime'] = df.apply(assign_regime, axis=1)
    
    # فاصله از Support/Resistance (نرمالشده)
    df['distance_support'] = (df['close'] - df['support_level']) / df['support_level']
    df['distance_resistance'] = (df['resistance_level'] - df['close']) / df['resistance_level']
    
    return df[['trend_direction', 'structure_strength', 'support_level', 
               'resistance_level', 'distance_support', 'distance_resistance', 'market_regime']]


# ============================================================
# ۲. ORDER FLOW & VOLUME IMBALANCE
# ============================================================

def calculate_order_flow(df: pd.DataFrame, lookback: int = 14) -> pd.DataFrame:
    """
    تحلیل Order Flow: Buy/Sell Imbalance
    
    ایده: اگر حجم روز صعودی بیشتر باشد، یعنی خریداران کنترل دارند.
    
    فیچرهای خروجی:
    - buy_volume: حجم معاملات صعودی (تقریبی)
    - sell_volume: حجم معاملات نزولی (تقریبی)
    - volume_imbalance: نسبت خریداران به فروشندگان
    - cumulative_volume_delta: CVD (تجمعی)
    - accumulation_distribution: A/D Line
    """
    df = df.copy()
    
    # تقریب Buy/Sell Volume با استفاده از بسته شدن
    # اگر close > open، بیشتر خریداران فعال بودند
    price_change = df['close'] - df['open']
    typical_price = (df['high'] + df['low']) / 2
    
    # Money Flow
    money_flow = typical_price * df['volume']
    positive_flow = np.where(price_change >= 0, money_flow, 0)
    negative_flow = np.where(price_change < 0, money_flow, 0)
    
    df['buy_volume'] = positive_flow
    df['sell_volume'] = negative_flow
    
    # Imbalance (نسبت)
    total_volume = positive_flow + negative_flow
    df['volume_imbalance'] = np.where(
        total_volume > 0,
        (positive_flow - negative_flow) / total_volume,
        0
    )
    
    # Cumulative Volume Delta (CVD)
    df['cvd'] = (df['buy_volume'] - df['sell_volume']).cumsum()
    
    # Accumulation/Distribution
    df['ad_line'] = ta.volume.acc_dist_index(
        df['high'], df['low'], df['close'], df['volume']
    )
    
    # Volume Trend (آیا CVD بالا میره یا پایین)
    df['cvd_trend'] = df['cvd'].rolling(5).mean()
    df['cvd_momentum'] = df['cvd'].diff(5)
    
    return df[['buy_volume', 'sell_volume', 'volume_imbalance', 
               'cvd', 'ad_line', 'cvd_trend', 'cvd_momentum']]


# ============================================================
# ۳. VOLUME PROFILE & PRICE LEVELS
# ============================================================

def volume_profile_features(df: pd.DataFrame, lookback: int = 100) -> pd.DataFrame:
    """
    شناسایی سطح‌های تراکم حجم (Point of Control, Value Area)
    
    فیچرهای خروجی:
    - poc_level: سطح بیشترین حجم
    - value_area_high/low: نواحی مهم حجم
    - volume_concentration: درجه تمرکز حجم روی POC
    """
    df = df.copy()
    
    # نسخه ساده: Price × Volume Weighted
    recent = df.tail(lookback)
    
    # محاسبه POC (نرمالشده)
    typical_price = (df['high'] + df['low']) / 2
    volume_weighted_price = (typical_price * df['volume']).rolling(lookback).sum()
    volume_total = df['volume'].rolling(lookback).sum()
    
    df['poc_level'] = np.where(
        volume_total > 0,
        volume_weighted_price / volume_total,
        df['close']
    )
    
    # Value Area (نزدیکترین قیمت‌ها)
    df['value_area_high'] = df['high'].rolling(lookback).quantile(0.75)
    df['value_area_low'] = df['low'].rolling(lookback).quantile(0.25)
    
    # درجه تمرکز حجم
    price_range = df['high'] - df['low']
    normalized_range = price_range / df['close']
    df['volume_concentration'] = df['volume'] / normalized_range
    df['volume_concentration'] = df['volume_concentration'].rolling(lookback).mean()
    
    # فاصله از POC
    df['distance_from_poc'] = (df['close'] - df['poc_level']) / df['poc_level']
    
    return df[['poc_level', 'value_area_high', 'value_area_low', 
               'volume_concentration', 'distance_from_poc']]


# ============================================================
# ۴. LIQUIDITY METRICS
# ============================================================

def liquidity_features(df: pd.DataFrame, lookback: int = 14) -> pd.DataFrame:
    """
    اندازه‌گیری نقدینگی بازار
    
    فیچرهای خروجی:
    - bid_ask_spread_est: تقریب Spread
    - liquidity_ratio: نسبت حجم به Range
    - spread_trend: روند تغییر Spread
    """
    df = df.copy()
    
    # Spread تقریبی (High - Low به عنوان Proxy برای Spread)
    df['hl_spread'] = df['high'] - df['low']
    df['spread_percent'] = df['hl_spread'] / df['close'] * 100
    
    # Liquidity Ratio = Volume / Range
    # بزرگتر = نقدینگی بیشتر
    df['liquidity_ratio'] = df['volume'] / (df['hl_spread'] + 0.0001)
    
    # تغییر Spread (منفی = بهتر، مثبت = بدتر)
    df['spread_trend'] = df['spread_percent'].rolling(lookback).mean()
    
    # Volume per Dollar (Turnover Ratio)
    df['volume_dollar'] = df['volume'] * df['close']
    df['turnover_ratio'] = df['volume_dollar'].rolling(lookback).mean()
    
    return df[['spread_percent', 'liquidity_ratio', 'spread_trend', 'turnover_ratio']]


# ============================================================
# ۵. FAIR VALUE GAP (FVG) - ایده پیشرفته
# ============================================================

def fair_value_gap_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    تشخیص Fair Value Gap: شکاف‌های قیمتی نپر شده
    
    در Crypto غالباً شکاف‌های بزرگی تشکیل میشه و Market اغلب دوباره
    برای پر کردن اون میرود.
    
    فیچرهای خروجی:
    - fvg_exists: آیا FVG وجود دارد
    - fvg_direction: بالا یا پایین
    - fvg_magnitude: بزرگی شکاف
    - fvg_target: هدف احتمالی پرشدن شکاف
    """
    df = df.copy()
    
    df['fvg_exists'] = 0
    df['fvg_direction'] = 0  # 1: بالا، -1: پایین
    df['fvg_magnitude'] = 0.0
    df['fvg_target'] = 0.0
    
    for i in range(2, len(df) - 1):
        # FVG بالا: کندل ۱ بسته میشه، کندل ۲ Gap Up میشه (Low از High کندل ۱ بالاتر)
        if df['low'].iloc[i] > df['high'].iloc[i-2]:
            df.loc[i, 'fvg_exists'] = 1
            df.loc[i, 'fvg_direction'] = 1
            df.loc[i, 'fvg_magnitude'] = (df['low'].iloc[i] - df['high'].iloc[i-2]) / df['close'].iloc[i]
            df.loc[i, 'fvg_target'] = df['high'].iloc[i-2]
        
        # FVG پایین: کندل ۱ بسته میشه، کندل ۲ Gap Down میشه (High از Low کندل ۱ پایین‌تر)
        elif df['high'].iloc[i] < df['low'].iloc[i-2]:
            df.loc[i, 'fvg_exists'] = 1
            df.loc[i, 'fvg_direction'] = -1
            df.loc[i, 'fvg_magnitude'] = (df['low'].iloc[i-2] - df['high'].iloc[i]) / df['close'].iloc[i]
            df.loc[i, 'fvg_target'] = df['low'].iloc[i-2]
    
    return df[['fvg_exists', 'fvg_direction', 'fvg_magnitude', 'fvg_target']]


# ============================================================
# ۶. IMBALANCE DETECTION (Volume/Price)
# ============================================================

def imbalance_features(df: pd.DataFrame, lookback: int = 14) -> pd.DataFrame:
    """
    شناسایی عدم تعادل بین قیمت و حجم
    
    فیچرهای خروجی:
    - price_volume_divergence: آیا قیمت بالا میرود ولی حجم کم؟
    - bullish_confirmation: آیا صعود توسط حجم تایید شده؟
    - hidden_divergence: Divergence پنهان
    """
    df = df.copy()
    
    # Divergence: قیمت بالا ولی حجم پایین
    price_trend = df['close'].diff().rolling(lookback).mean()
    volume_trend = df['volume'].rolling(lookback).mean()
    
    # نرمالسازی
    price_norm = (df['close'] - df['close'].rolling(lookback).min()) / (df['close'].rolling(lookback).max() - df['close'].rolling(lookback).min() + 0.0001)
    volume_norm = df['volume'] / df['volume'].rolling(lookback).mean()
    
    df['price_volume_divergence'] = price_norm - (volume_norm / volume_norm.max())
    
    # Bullish Confirmation: صعود + حجم بالا
    df['bullish_confirmation'] = np.where(
        (df['close'] > df['close'].shift(1)) & (df['volume'] > df['volume'].rolling(lookback).mean()),
        1, 0
    )
    
    # Bearish Confirmation: نزول + حجم بالا
    df['bearish_confirmation'] = np.where(
        (df['close'] < df['close'].shift(1)) & (df['volume'] > df['volume'].rolling(lookback).mean()),
        -1, 0
    )
    
    return df[['price_volume_divergence', 'bullish_confirmation', 'bearish_confirmation']]


# ============================================================
# ۷. FUNDING & OI FEATURES (اگر داده موجود باشد)
# ============================================================

def funding_features(df: pd.DataFrame, funding_df: pd.DataFrame = None, 
                     oi_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    ترکیب اطلاعات Funding Rate و Open Interest
    
    فیچرهای خروجی:
    - funding_trend: روند Funding
    - funding_extreme: آیا Funding خیلی بالا یا پایین؟
    - oi_trend: روند OI
    - oi_divergence: OI vs Price
    """
    df = df.copy()
    
    df['funding_trend'] = 0.0
    df['funding_extreme'] = 0
    df['oi_trend'] = 0.0
    df['oi_divergence'] = 0.0
    
    if funding_df is not None and not funding_df.empty:
        funding_df = funding_df.sort_index()
        funding_merged = pd.merge_asof(
            df.sort_index(), funding_df, left_index=True, right_index=True, direction='backward'
        )
        df['funding_trend'] = funding_merged['funding_rate'].rolling(3).mean()
        
        # Extreme = Funding خیلی بالا (+0.1%) یا خیلی پایین (-0.1%)
        df['funding_extreme'] = np.where(
            funding_merged['funding_rate'] > 0.001, 1,
            np.where(funding_merged['funding_rate'] < -0.001, -1, 0)
        )
    
    if oi_df is not None and not oi_df.empty:
        oi_df = oi_df.sort_index()
        oi_merged = pd.merge_asof(
            df.sort_index(), oi_df, left_index=True, right_index=True, direction='backward'
        )
        if 'open_interest' in oi_merged.columns:
            df['oi_trend'] = oi_merged['open_interest'].pct_change(5)
            
            # OI Divergence: OI بالا ولی قیمت پایین (bearish)
            price_change = df['close'].pct_change(5)
            oi_change = oi_merged['open_interest'].pct_change(5)
            df['oi_divergence'] = oi_change - price_change
    
    return df[['funding_trend', 'funding_extreme', 'oi_trend', 'oi_divergence']]


# ============================================================
# ۸. LIQUIDATION FLOW
# ============================================================

def liquidation_features(df: pd.DataFrame, liq_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    تحلیل Liquidation: نقاط ضعف یا قوت
    
    فیچرهای خروجی:
    - liquidation_intensity: شدت Liquidation
    - liquidation_bias: طرفداری Longs یا Shorts
    - liquidation_clusters: تجمع Liquidations
    """
    df = df.copy()
    
    df['liquidation_intensity'] = 0.0
    df['liquidation_bias'] = 0
    df['liquidation_momentum'] = 0.0
    
    if liq_df is not None and not liq_df.empty:
        liq_df = liq_df.sort_index()
        liq_merged = pd.merge_asof(
            df.sort_index(), liq_df, left_index=True, right_index=True, direction='backward'
        )
        
        if 'liquidations_long' in liq_merged.columns and 'liquidations_short' in liq_merged.columns:
            total_liq = liq_merged['liquidations_long'] + liq_merged['liquidations_short']
            
            # نرمالسازی
            df['liquidation_intensity'] = (total_liq / total_liq.rolling(14).mean()).fillna(0)
            
            # Bias: Long Liquidations > Short Liquidations = Bearish
            df['liquidation_bias'] = np.where(
                liq_merged['liquidations_long'] > liq_merged['liquidations_short'], -1,
                np.where(liq_merged['liquidations_long'] < liq_merged['liquidations_short'], 1, 0)
            )
            
            # تغییر Liquidations
            df['liquidation_momentum'] = total_liq.diff(5)
    
    return df[['liquidation_intensity', 'liquidation_bias', 'liquidation_momentum']]


# ============================================================
# ۹. VWAP & SESSION FEATURES
# ============================================================

def vwap_session_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    VWAP و Session-based Features
    
    فیچرهای خروجی:
    - vwap: حد وسط قیمت موزون حجم
    - distance_vwap: فاصله از VWAP
    - session_type: کدام سشن (Asian, London, NY)
    - session_momentum: قوت Session فعلی
    """
    df = df.copy()
    
    # VWAP
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    vwap = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    df['vwap'] = vwap
    df['distance_vwap'] = (df['close'] - df['vwap']) / df['vwap']
    
    # Session Features (بر اساس ساعت)
    df['hour'] = df.index.hour if hasattr(df.index, 'hour') else 0
    
    def assign_session(hour):
        if 0 <= hour < 8:
            return 'asian'
        elif 8 <= hour < 16:
            return 'london'
        elif 16 <= hour < 24:
            return 'ny'
        else:
            return 'other'
    
    df['session_type'] = df['hour'].apply(assign_session)
    
    # Session Momentum: میانگین صعود/نزول در این سشن
    session_returns = df.groupby('session_type')['close'].pct_change().rolling(5).mean()
    df['session_momentum'] = session_returns.values
    
    return df[['vwap', 'distance_vwap', 'session_type', 'session_momentum']]


# ============================================================
# ۱۰. تابع اصلی: جمع‌آوری تمام فیچرها
# ============================================================

def build_advanced_dataset(
    df: pd.DataFrame,
    funding_df: pd.DataFrame = None,
    oi_df: pd.DataFrame = None,
    liq_df: pd.DataFrame = None,
    enabled_features: List[str] = None
) -> pd.DataFrame:
    """
    ساخت دیتاست کامل با تمام فیچرهای جدید (انتخابی)
    
    Parameters:
    -----------
    enabled_features: لیست فیچرهایی که فعال کنیم
        ['market_structure', 'order_flow', 'volume_profile', 'liquidity',
         'fvg', 'imbalance', 'funding', 'liquidation', 'vwap_session']
    """
    
    if enabled_features is None:
        enabled_features = [
            'market_structure', 'order_flow', 'volume_profile', 
            'liquidity', 'fvg', 'imbalance', 'funding', 
            'liquidation', 'vwap_session'
        ]
    
    df = df.copy()
    all_features = {}
    
    print("🔨 در حال ساخت Advanced Features...")
    
    if 'market_structure' in enabled_features:
        print("  ✓ Market Structure...")
        ms = detect_market_structure(df)
        all_features.update(ms.to_dict('series'))
    
    if 'order_flow' in enabled_features:
        print("  ✓ Order Flow & CVD...")
        of = calculate_order_flow(df)
        all_features.update(of.to_dict('series'))
    
    if 'volume_profile' in enabled_features:
        print("  ✓ Volume Profile...")
        vp = volume_profile_features(df)
        all_features.update(vp.to_dict('series'))
    
    if 'liquidity' in enabled_features:
        print("  ✓ Liquidity...")
        lq = liquidity_features(df)
        all_features.update(lq.to_dict('series'))
    
    if 'fvg' in enabled_features:
        print("  ✓ Fair Value Gap...")
        fvg = fair_value_gap_features(df)
        all_features.update(fvg.to_dict('series'))
    
    if 'imbalance' in enabled_features:
        print("  ✓ Imbalance Detection...")
        imb = imbalance_features(df)
        all_features.update(imb.to_dict('series'))
    
    if 'funding' in enabled_features:
        print("  ✓ Funding & OI...")
        fund = funding_features(df, funding_df=funding_df, oi_df=oi_df)
        all_features.update(fund.to_dict('series'))
    
    if 'liquidation' in enabled_features:
        print("  ✓ Liquidation...")
        lq_features = liquidation_features(df, liq_df=liq_df)
        all_features.update(lq_features.to_dict('series'))
    
    if 'vwap_session' in enabled_features:
        print("  ✓ VWAP & Session...")
        vs = vwap_session_features(df)
        all_features.update(vs.to_dict('series'))
    
    # ترکیب تمام فیچرها
    result = pd.DataFrame(all_features, index=df.index)
    result = pd.concat([df, result], axis=1)
    
    print(f"✅ {len(result.columns) - len(df.columns)} فیچر جدید اضافه شد")
    
    return result


# ============================================================
# لیست تمام فیچرهای جدید
# ============================================================

ADVANCED_FEATURE_COLUMNS = [
    # Market Structure
    'trend_direction', 'structure_strength', 'support_level', 
    'resistance_level', 'distance_support', 'distance_resistance',
    
    # Order Flow
    'volume_imbalance', 'cvd', 'ad_line', 'cvd_momentum',
    
    # Volume Profile
    'poc_level', 'value_area_high', 'value_area_low', 
    'volume_concentration', 'distance_from_poc',
    
    # Liquidity
    'spread_percent', 'liquidity_ratio', 'turnover_ratio',
    
    # FVG
    'fvg_exists', 'fvg_direction', 'fvg_magnitude',
    
    # Imbalance
    'price_volume_divergence', 'bullish_confirmation', 'bearish_confirmation',
    
    # Funding/OI
    'funding_trend', 'funding_extreme', 'oi_trend', 'oi_divergence',
    
    # Liquidation
    'liquidation_intensity', 'liquidation_bias', 'liquidation_momentum',
    
    # VWAP/Session
    'vwap', 'distance_vwap', 'session_momentum',
]
