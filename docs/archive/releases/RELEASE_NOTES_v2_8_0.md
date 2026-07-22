# Freakto v2.8.0 - Market Breadth Engine

## هدف نسخه

این نسخه Freakto را از یک Portfolio Scanner صرف به یک موتور تشخیص وضعیت کلی بازار ارتقا می‌دهد. از این به بعد خروجی پورتفو فقط نمی‌گوید کدام نماد بهتر است؛ بلکه می‌گوید کل بازار در چه حالتی قرار دارد:

- RISK_ON
- RISK_OFF
- NEUTRAL
- MIXED

## قابلیت‌های اضافه‌شده

### 1. Market Breadth Engine

فایل جدید:

```text
engine/market_breadth.py
```

این ماژول روی خروجی اسکن پورتفو محاسبه می‌کند:

- درصد نمادهای Bullish
- درصد نمادهای Bearish
- درصد نمادهای Neutral
- تعداد فرصت‌های Actionable
- تعداد Watchlistها
- میانگین Score
- میانگین Confidence
- میانگین Opportunity Score

### 2. Market Mode

خروجی جدید:

```text
Market Mode : NEUTRAL
Risk Tone   : MONITOR
Strength    : 100/100
```

### 3. Portfolio Report Upgrade

گزارش کنسول و تلگرام حالا قبل از جدول نمادها، نمای کلی بازار را نمایش می‌دهد.

### 4. Portfolio CSV Upgrade

فایل زیر حالا ستون‌های Market Breadth هم ذخیره می‌کند:

```text
logs/portfolio_scans.csv
```

ستون‌های اضافه‌شده:

- breadth_mode
- breadth_strength
- breadth_risk_tone
- breadth_bullish_pct
- breadth_bearish_pct
- breadth_neutral_pct
- breadth_avg_opportunity

## دستور تست

```cmd
python portfolio_scanner.py
```

یا برای ارسال تلگرام:

```cmd
python portfolio_scanner.py --send
```

## تفسیر خروجی

اگر بیشتر نمادها NEUTRAL باشند:

```text
Market Mode: NEUTRAL
Risk Tone: MONITOR
```

اگر بیشتر نمادها LONG و فرصت‌ها باکیفیت باشند:

```text
Market Mode: RISK_ON
Risk Tone: BULLISH
```

اگر بیشتر نمادها SHORT و فشار فروش غالب باشد:

```text
Market Mode: RISK_OFF
Risk Tone: BEARISH
```

اگر وضعیت بازار پراکنده باشد:

```text
Market Mode: MIXED
Risk Tone: CAUTION
```

## نکته طراحی

این نسخه intentionally محافظه‌کارانه است. اگر 1D و 4H خنثی باشند، حتی وجود چند سیگنال کوتاه‌مدت باعث Risk-On شدن کل بازار نمی‌شود.
