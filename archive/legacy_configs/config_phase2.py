"""
تنظیمات Feature Engineering پیشرفته
"""

# کدام فیچرهای جدید فعال باشند؟
ENABLED_ADVANCED_FEATURES = [
    'market_structure',      # ✅ بسیار توصیه‌شده
    'order_flow',           # ✅ بسیار توصیه‌شده
    'volume_profile',       # ✅ توصیه‌شده
    'liquidity',           # ✅ توصیه‌شده
    'fvg',                 # ✅ توصیه‌شده (Crypto-specific)
    'imbalance',           # ✅ توصیه‌شده
    'funding',             # ⚠️ فقط اگر funding_df موجود باشد
    'liquidation',         # ⚠️ فقط اگر liq_df موجود باشد
    'vwap_session',        # ✅ توصیه‌شده
]

# آستانه‌های حساس‌سازی برای تشخیص FVG
FVG_MIN_MAGNITUDE = 0.005  # حداقل 0.5% شکاف

# آستانه Volume Imbalance
IMBALANCE_THRESHOLD = 0.3  # بیشتر از 30% نامتقارن

# آستانه Liquidity برای تشخیص منطقه خطرناک
MIN_LIQUIDITY_RATIO = 100  # حجم / Range

# تعداد کندلها برای تحلیل بک‌تست
LOOKBACK_PERIODS = {
    'market_structure': 20,
    'order_flow': 14,
    'volume_profile': 100,
    'liquidity': 14,
    'imbalance': 14,
}
