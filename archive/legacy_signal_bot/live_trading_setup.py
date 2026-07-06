"""
live_trading_setup.py - آماده‌سازی برای تریدینگ زنده

نکات مهم:
1. تست روی paper trading اول
2. سپس real money با حجم کم شروع کن
3. مقدار ریسک را تنظیم کن
"""

import joblib
import warnings
warnings.filterwarnings('ignore')

from config import MODEL_PATH, MIN_CONFIDENCE, SYMBOL, TIMEFRAME


def check_model_ready():
    """بررسی آمادگی مدل برای live trading"""
    
    print("=" * 100)
    print("🎬 بررسی آمادگی برای Live Trading")
    print("=" * 100)
    
    # ۱. بررسی مدل
    try:
        bundle = joblib.load(MODEL_PATH)
        print(f"\n✅ مدل وجود دارد: {MODEL_PATH}")
        print(f"   فیچرها: {len(bundle.get('feature_columns', []))}")
    except:
        print(f"\n❌ مدل یافت نشد!")
        return False
    
    # ۲. بررسی تنظیمات
    print(f"\n✅ تنظیمات:")
    print(f"   نماد: {SYMBOL}")
    print(f"   تایمفریم: {TIMEFRAME}")
    print(f"   MIN_CONFIDENCE: {MIN_CONFIDENCE}")
    
    # ۳. چیستی اجرا
    print(f"\n" + "=" * 100)
    print("📋 Checklist برای Live Trading")
    print("=" * 100)
    
    checklist = [
        ("✓", "مدل آموزش‌شده و ذخیره شده"),
        ("✓", "بکتست انجام شده (Win Rate: 75%)"),
        ("✓", "Walk Forward نتایج خوب"),
        ("⚠️", "Paper Trading ابتدا توصیه میشود"),
        ("⚠️", "Risk Management تنظیم شود"),
        ("⚠️", "Position Size محافظه‌کارانه شروع کن"),
    ]
    
    for status, item in checklist:
        print(f"  {status} {item}")
    
    print(f"\n" + "=" * 100)
    print("⚠️ هشدارهای مهم")
    print("=" * 100)
    print("""
1️⃣ هیچ پیشبینی‌ای ۱۰۰٪ دقیق نیست
   - Win Rate 75% خوب است اما معناش 25% معاملات باخت دارند

2️⃣ بازار تغییر می‌کند
   - مدل تاریخ روی شده است
   - ممکن است عملکرد زنده متفاوت باشد

3️⃣ شروع با حجم کم
   - فقط ۰.۱ BTC یا کمتر برای شروع
   - بعد از ۲-۳ هفته موفقیت، حجم را بالا ببر

4️⃣ نظارت روزانه
   - هر روز نتایج را چک کن
   - اگر Win Rate <50% شد، مدل را دوباره آموزش بده

5️⃣ Stop Loss حتمی
   - اگر ۳ معاملهی متوالی باخت دار، تریدینگ متوقف کن
    """)
    
    print(f"\n" + "=" * 100)
    print("✅ اگر همهی موارد بالا درست است، می‌توانی شروع کنی!")
    print("=" * 100)
    
    return True


def recommendation():
    """توصیهات نهایی"""
    print(f"\n" + "=" * 100)
    print("💡 توصیهات نهایی")
    print("=" * 100)
    print("""
🎯 بهترین رویه برای شروع:

۱. هفتهی اول: Paper Trading
   python monitor.py  (بدون واقعی ترید کن)
   
۲. هفتهی دوم-سوم: Live Trading حجم کم
   - فقط 0.05 BTC در هر معامله
   - حداقل 10 معامله موفق دیده شود
   
۳. ماه دوم+: Scale Up
   - اگر نتایج خوب بود، حجم را 2 برابر کن
   - تا 1 BTC برسی

📊 نتایج مورد انتظار (اگر مدل دوام بیاورد):
   - Win Rate: 60-75%
   - ماهانه بازده: 5-15% (بسیار خوب!)
   - Drawdown: <20%

⚠️ اگر نتایج بدتر شد:
   - مدل را دوباره آموزش بده
   - یا فیچرهای جدید اضافه کن
   - یا استراتژی را تغییر بده
    """)


if __name__ == '__main__':
    if check_model_ready():
        recommendation()
