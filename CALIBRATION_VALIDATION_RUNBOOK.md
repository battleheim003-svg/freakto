# Freakto Calibration Validation & Threshold Optimizer

این مرحله، کالیبراسیون و Edge Gate را با جداسازی زمانی سه‌مرحله‌ای ارزیابی می‌کند:

1. **Train**: فقط برای ساخت نگاشت Score → Probability
2. **Optimize**: فقط برای انتخاب Thresholdها
3. **Holdout**: فقط یک‌بار برای ارزیابی نهایی و تصمیم درباره Promotion

بین Splitها به‌اندازه پیش‌فرض ۶ ردیف purge انجام می‌شود تا هم‌پوشانی افق ارزیابی کاهش یابد. هیچ ستون Outcome/Return به‌عنوان Feature استفاده نمی‌شود؛ تنها ورودی پیش‌بینی، Score ثبت‌شده در زمان تصمیم است.

## اجرای استاندارد

```bash
python -X utf8 calibration_validation.py
```

خروجی‌ها در مسیر زیر ساخته می‌شوند:

```text
logs/calibration_validation/
```

فایل‌های اصلی:

- `calibration_validation_report.json`
- `calibration_validation_report.csv`
- `threshold_candidates.csv`
- `calibration_bucket_diagnostics.csv`
- `holdout_scored.csv`
- `score_calibration_candidate.csv`
- `recommended_edge_gate_policy.json`

## Promotion امن

ابتدا اجرای عادی را انجام بده و گزارش را بررسی کن. سپس فقط درصورتی‌که Status برابر `PASS` باشد:

```bash
python -X utf8 calibration_validation.py --promote
```

در این حالت دو فایل Runtime ساخته/جایگزین می‌شوند:

```text
logs/calibration/score_calibration.csv
logs/calibration/edge_gate_policy.json
```

اگر Holdout پاس نشود، Promotion به‌صورت Fail-Closed مسدود می‌شود.

## تست‌ها

```bash
python -m pytest
```

این ابزار هیچ Paper/Live Trading را فعال نمی‌کند و فقط یک ابزار Research/Validation است.
