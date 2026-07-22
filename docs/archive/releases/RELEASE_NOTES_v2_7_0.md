# Freakto v2.7.0 — Position & Risk Intelligence Engine

## هدف نسخه

این نسخه Freakto را از یک موتور تشخیص فرصت به یک موتور مدیریت معامله نزدیک‌تر می‌کند. از این نسخه، وقتی یک خروجی LONG/SHORT وجود داشته باشد، سیستم فقط Bias و Score را نمایش نمی‌دهد؛ بلکه کیفیت معامله، R:R، اندازه موقعیت، ریسک پیشنهادی و Drawdown تاریخی را هم محاسبه می‌کند.

## قابلیت‌های جدید

### 1. Risk / Reward Engine
فایل جدید: `engine/risk_reward.py`

- Entry میانگین Zone را محاسبه می‌کند.
- فاصله Stop را محاسبه می‌کند.
- R:R برای T1/T2/T3 را محاسبه می‌کند.
- برای وضعیت‌های NEUTRAL خروجی غیرمعامله‌ای برمی‌گرداند.

### 2. Position Sizing Engine
فایل جدید: `engine/position_size.py`

- Account Size و Risk Percent را از تنظیمات می‌گیرد.
- مقدار دلاری ریسک را حساب می‌کند.
- Position Notional و Units را بر اساس فاصله Stop محاسبه می‌کند.

تنظیمات جدید در `config.py`:

```env
TRADE_ACCOUNT_SIZE=10000
TRADE_RISK_PCT=1.0
TRADE_MAX_RISK_PCT=2.0
```

### 3. Kelly Risk Model
فایل جدید: `engine/kelly.py`

- بر اساس Win Rate تاریخی و R:R، Kelly ساده را محاسبه می‌کند.
- خروجی نهایی محافظه‌کارانه است و ریسک پیشنهادی را محدود می‌کند.

### 4. Historical Drawdown Estimator
فایل جدید: `engine/drawdown.py`

- از Similar Snapshotها برای تخمین Expected Drawdown و Worst Drawdown استفاده می‌کند.
- اگر داده کافی نباشد، خروجی امن و غیرخطا برمی‌گرداند.

### 5. Trade Quality Engine
فایل جدید: `engine/trade_quality.py`

یک کارت کیفیت معامله می‌سازد:

- Grade: `AAA+ / AAA / AA / A / B / C / Avoid`
- Trade Quality Score
- Historical Win Rate / Stop Rate / Avg Return
- R:R
- Position Size
- Kelly Risk
- Historical Drawdown

### 6. Monitor Upgrade
فایل تغییرکرده: `monitor.py`

در گزارش کنسول، اگر خروجی جهت‌دار باشد، بخش جدید Trade Intelligence چاپ می‌شود.

### 7. Telegram Trade Card
فایل تغییرکرده: `engine/score.py`

در پیام تلگرام، بخش جدید `Trade Intelligence` اضافه شده است.

### 8. Portfolio Scanner v2.7
فایل‌های تغییرکرده:

- `portfolio_scanner.py`
- `engine/portfolio.py`

Portfolio Scanner حالا در جدول خروجی موارد زیر را هم نشان می‌دهد:

- Trade Grade
- R:R اولیه
- Recommended Risk
- Position Notional
- Expected Drawdown در CSV

## فایل‌های جدید

```text
engine/risk_reward.py
engine/position_size.py
engine/kelly.py
engine/drawdown.py
engine/trade_quality.py
RELEASE_NOTES_v2_7_0.md
```

## فایل‌های تغییرکرده

```text
config.py
monitor.py
portfolio_scanner.py
engine/score.py
engine/portfolio.py
```

## تست پیشنهادی

```cmd
python monitor.py --once
python portfolio_scanner.py
python portfolio_scanner.py --send
```

## نکته مهم

این نسخه همچنان توصیه مالی یا دستور خرید/فروش تولید نمی‌کند. خروجی Position Size و Kelly فقط ابزار مدیریت ریسک است و باید با تنظیمات شخصی کاربر کنترل شود.
