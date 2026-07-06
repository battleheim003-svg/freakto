# Freakto v4.6.0 — Practical Testing Suite

این نسخه یک Release بزرگ است که نقشه راه v4.1 تا v4.6 را یکجا اضافه می‌کند. هدف اصلی این نسخه این است که Freakto از «تحلیل و هشدار» وارد فاز تست عملی امن شود، اما هنوز بدون معامله واقعی و بدون اجرای سفارش.

## ماژول‌های جدید

### 1. Paper Trading Engine

فایل‌ها:

- `engine/paper_trading.py`
- `paper_trading_dashboard.py`

قابلیت‌ها:

- ثبت معامله فرضی از خروجی Portfolio Scanner
- ذخیره در `logs/paper_trades.csv`
- ارزیابی معاملات فرضی با کندل‌های آینده
- ذخیره در `logs/paper_trade_evaluations.csv`
- محاسبه Win/Loss، R Multiple، MFE/MAE و Expectancy

دستورها:

```bash
python portfolio_scanner.py --paper
python paper_trading_dashboard.py --scan
python paper_trading_dashboard.py --evaluate
python paper_trading_dashboard.py --scan --evaluate
```

## 2. Trade Readiness Gate

فایل‌ها:

- `engine/trade_readiness.py`
- `trade_readiness_dashboard.py`
- `live_readiness_report.py`

قابلیت‌ها:

- تشخیص اینکه پروژه در کدام فاز است: `RESEARCH_ONLY`، `PAPER_TRADING_PHASE` یا `MICRO_LIVE_READY`
- بررسی حداقل داده لازم برای ورود به تست عملی
- تولید Blockerها، Warningها و Reasons
- جلوگیری از فراموش شدن شرط‌های ورود به بازار واقعی

دستورها:

```bash
python trade_readiness_dashboard.py
python live_readiness_report.py
```

## 3. Strategy Lab پایه

فایل‌ها:

- `engine/strategy_lab.py`
- `strategy_lab_dashboard.py`

قابلیت‌ها:

- مقایسه چند فیلتر ساده روی تصمیم‌های ارزیابی‌شده
- بررسی Score thresholds
- بررسی WATCHLIST or better
- محاسبه Win Rate، Avg 24h، Stop Rate و Verdict

دستور:

```bash
python strategy_lab_dashboard.py
```

## 4. Walk-Forward Validation

فایل‌ها:

- `engine/walk_forward.py`
- `walk_forward_dashboard.py`

قابلیت‌ها:

- تقسیم زمانی داده‌ها به train/test
- تشخیص ریسک overfitting
- بررسی پایداری out-of-sample

دستور:

```bash
python walk_forward_dashboard.py
```

## 5. اتصال Paper Trading به Portfolio Scanner

فایل اصلاح‌شده:

- `portfolio_scanner.py`

قابلیت جدید:

```bash
python portfolio_scanner.py --paper
```

فقط کاندیدهایی که از نظر Recommendation، Trade Quality، R:R و Confidence مجاز باشند به Paper Trading وارد می‌شوند.

## 6. متادیتای کامل‌تر در PortfolioItem

فایل اصلاح‌شده:

- `engine/portfolio.py`

فیلدهای جدید:

- `decision_timestamp`
- `entry_zone`
- `stop_zone`
- `targets`

این فیلدها برای ثبت Paper Trade لازم‌اند.

## 7. نسخه‌بندی خروجی‌ها

خروجی‌های زیر به v4.6 به‌روزرسانی شدند:

- Portfolio Scanner
- Market Breadth
- Daily AI Report
- Intelligence Layer
- Consistency Check

## وضعیت تست عملی

این نسخه عمداً هنوز معامله واقعی انجام نمی‌دهد. شرط پیشنهادی برای Micro Live Test:

- حداقل 100 ارزیابی COMPLETE
- حداقل 30 معامله Paper بسته‌شده
- Paper Expectancy مثبت
- Paper Win Rate حداقل 55%
- نبود تناقض بین Actionability و Trade Quality
- R:R حداقل 1.5 برای سیگنال‌های عملی

تا قبل از این شرایط، خروجی Live Readiness باید `False` بماند.
