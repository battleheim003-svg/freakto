# نتیجه واقعی Calibration Validation

تاریخ اجرا: 2026-07-12

ورودی:

```text
logs/calibration_dataset/calibration_training.csv
Rows: 3200
```

جداسازی زمانی و بدون Shuffle:

- Train: 1914 ردیف
- Purge: 6 ردیف
- Optimize: 634 ردیف
- Purge: 6 ردیف
- Holdout: 640 ردیف

## نتیجه نهایی

```text
Validation Status: FAIL
Recommended Policy: NONE
Policy Promotion: BLOCKED
```

هیچ ترکیب عمومی از Raw Score، Calibrated Probability، Minimum Samples و Expected Edge در بخش Optimize نتوانست Expectancy مثبت و حداقل حجم نمونه لازم را هم‌زمان حفظ کند. بنابراین سیستم به‌صورت Fail-Closed هیچ Policyای را فعال نکرد.

## Baseline روی Holdout

شرط Baseline: `score >= 70`

```text
Samples       : 129
Win Rate      : 50.39%
Expectancy    : -0.205940%
Profit Factor : 0.806459
Max Drawdown  : -51.587203%
Total Return  : -26.566261%
```

تفکیک جهت:

```text
LONG  : 71 samples | Win Rate 54.93% | Expectancy -0.040498% | PF 0.960625
SHORT : 58 samples | Win Rate 44.83% | Expectancy -0.408464% | PF 0.631208
```

## کیفیت کالیبراسیون روی Holdout

```text
Brier Score : 0.273966
Log Loss    : 0.745310
ECE         : 0.164032
MCE         : 0.366853
```

## نکته تحقیقاتی مهم

در Holdout، زیرگروه `LONG + score >= 80` نتیجه مثبت داشت، اما فقط 16 نمونه داشت. همین زیرگروه در بخش Optimize مثبت نبود؛ بنابراین استفاده از آن به‌عنوان Gate فعال، نمونه واضح Overfitting و Data Snooping محسوب می‌شود و عمداً رد شد.

قدم علمی بعدی باید بررسی **Side-aware / Regime-aware calibration** باشد، نه پایین‌آوردن اجباری Thresholdهای عمومی.
