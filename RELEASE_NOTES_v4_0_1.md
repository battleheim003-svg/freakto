# Freakto v4.0.1 — Portfolio Actionability Consistency Patch

## هدف نسخه

v4.0.1 یک Bugfix مهم بعد از Intelligence Layer است. خروجی تست v4.0 نشان داد ممکن است یک نماد در Portfolio Scanner به عنوان `ACTIONABLE` یا `WATCHLIST` نمایش داده شود، درحالی‌که Trade Intelligence همان نماد را `Avoid` نشان می‌دهد یا R:R اولیه آن کمتر از حد قابل قبول است.

این نسخه این ناسازگاری را اصلاح می‌کند.

## مشکل قبل از اصلاح

نمونه مشکل:

```text
DOGE/USDT | Recommendation ACTIONABLE | Trade Avoid | RR 0.91
BNB/USDT  | Recommendation WATCHLIST  | Trade Avoid | RR 0.88
```

این یعنی Opportunity Score خوب بود، اما Trade Quality و R:R هنوز اجازه «قابل اقدام» بودن نمی‌دادند.

## اصلاحات اصلی

### 1. Trade Consistency Guard

فایل اصلاح‌شده:

```text
engine/portfolio.py
```

حالا Recommendation نهایی از یک گیت ایمنی عبور می‌کند:

- `ELITE` فقط وقتی مجاز است که R:R و Trade Quality واقعاً قوی باشند.
- `ACTIONABLE` فقط وقتی مجاز است که Trade Quality حداقل قابل قبول و R:R اولیه مناسب باشد.
- `WATCHLIST` هم اگر R:R خیلی ضعیف یا Trade Quality برابر `Avoid` باشد، به `MONITOR` کاهش می‌یابد.

### 2. کاهش رتبه خودکار توصیه‌های متناقض

اگر یک نماد از نظر Opportunity جذاب باشد ولی Trade Card تأیید ندهد:

```text
ACTIONABLE -> MONITOR
WATCHLIST  -> MONITOR
```

و دلیل downgrade در notes ذخیره می‌شود:

```text
Trade Guard: ACTIONABLE -> MONITOR
Trade Guard reason: R:R برای Actionable کافی نیست
Trade Guard reason: Trade Quality برابر Avoid است
```

### 3. Portfolio Consistency Diagnostic

فایل جدید:

```text
portfolio_consistency_check.py
```

اجرا:

```bash
python portfolio_consistency_check.py
```

این ابزار بررسی می‌کند هیچ `ELITE/ACTIONABLE/WATCHLIST` با شرایط زیر وجود نداشته باشد:

- `Trade=Avoid`
- R:R نامعتبر
- R:R کمتر از حد لازم
- Trade Quality Score کمتر از حد لازم

### 4. نسخه‌بندی خروجی‌ها

خروجی‌های مربوط به Portfolio و Daily Report به v4.0.1 به‌روزرسانی شدند.

## فایل‌های تغییرکرده

```text
engine/portfolio.py
engine/market_breadth.py
engine/daily_report.py
portfolio_scanner.py
portfolio_consistency_check.py
RELEASE_NOTES_v4_0_1.md
```

## تست پیشنهادی

```bash
python portfolio_scanner.py --send
python portfolio_consistency_check.py
python monitor.py --once
python intelligence_dashboard.py
```

## نتیجه مورد انتظار

بعد از این نسخه، اگر خروجی Portfolio Scanner بنویسد `ACTIONABLE` یا `WATCHLIST`، دیگر نباید هم‌زمان `Trade=Avoid` یا R:R بسیار ضعیف داشته باشد.
