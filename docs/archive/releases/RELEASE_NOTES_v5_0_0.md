# Freakto v5.0.0 — Portfolio Memory, Confidence Calibration & Monte Carlo Risk Lab

این نسخه سه اولویت نهایی فاز Validation را اضافه می‌کند:

1. **Portfolio Memory Engine**
   - حافظه جداگانه برای هر نماد می‌سازد.
   - از `portfolio_scans.csv`, `decisions.csv`, `decision_evaluations.csv`, `paper_trades.csv` و `paper_trade_evaluations.csv` استفاده می‌کند.
   - برای هر Symbol آمار اسکن، تصمیم، Directional Win، Target 1 Hit، Paper Expectancy و وضعیت حافظه را نشان می‌دهد.

2. **Confidence Calibration Engine**
   - بررسی می‌کند Confidence داخلی سیستم با outcome واقعی چقدر هم‌خوان است.
   - خروجی را بر اساس Confidence Label و Score Bucket جدا می‌کند.
   - تفاوت Directional Win Rate و Target 1 Hit Rate را حفظ می‌کند.

3. **Monte Carlo Risk Lab**
   - با bootstrap از Paper R multiples یا در نبود آن از decision returns شبیه‌سازی می‌کند.
   - Median/P05/P95، Max Drawdown، Probability of Loss و Probability of Ruin را گزارش می‌دهد.
   - اگر Paper Trade کافی نباشد، با هشدار از decision returns fallback می‌گیرد.

## فایل‌های جدید

- `engine/portfolio_memory.py`
- `portfolio_memory_dashboard.py`
- `engine/confidence_calibration.py`
- `confidence_calibration_dashboard.py`
- `engine/monte_carlo.py`
- `monte_carlo_dashboard.py`
- `risk_lab_dashboard.py`

## فایل اصلاح‌شده

- `validation_suite_dashboard.py`

## دستورهای تست

```cmd
python portfolio_memory_dashboard.py
python confidence_calibration_dashboard.py
python monte_carlo_dashboard.py
python risk_lab_dashboard.py
python validation_suite_dashboard.py
```

## نکته عملی

این نسخه هنوز مجوز Live Trading نیست. هدفش ساخت شواهد قوی‌تر برای زمان مناسب Paper Trading و Micro Live Test است.
