# Freakto Segmented Calibration — Real Dataset Result

تاریخ اجرا: 2026-07-12

## داده

- Rows loaded: `3200`
- Rows usable: `3200`
- Timeframe موجود در دیتاست: `4h`
- Segmentهای ارزیابی‌شده: `18`

## نتیجه نهایی

```text
Status               : FAIL
Recommended policies : 0
Promoted              : False
```

توزیع وضعیت:

```text
FAIL              : 6
INSUFFICIENT_DATA : 9
INELIGIBLE        : 3
```

سه Segment شامل `UNKNOWN` عمداً Diagnostic-only بودند. Segmentهای کم‌نمونه مثل Sideways، Quiet و Volatile از Gate حجم نمونه عبور نکردند.

## Segmentهای اصلی پرنمونه

| Segment | Train | Optimize | Holdout | Train break-even probability | نتیجه |
|---|---:|---:|---:|---:|---|
| LONG + BULL | 912 | 235 | 274 | 58.8256% | No positive Optimize policy |
| SHORT + BEAR | 806 | 361 | 315 | 55.0709% | No positive Optimize policy |
| LONG | 1014 | 248 | 293 | 57.5216% | No positive Optimize policy |
| SHORT | 900 | 386 | 347 | 56.5990% | No positive Optimize policy |
| BULL | 912 | 235 | 274 | 58.8256% | No positive Optimize policy |
| BEAR | 808 | 366 | 315 | 55.0285% | No positive Optimize policy |

احتمال سربه‌سر بالاتر از 50% است، زیرا میانگین زیان در Train از میانگین برد بزرگ‌تر بوده است. حتی با Break-even اختصاصی هر Segment، هیچ ترکیب Score/Probability/Sample/Edge با حداقل حجم انتخاب در Optimize، Expectancy مثبت و Profit Factor معتبر نساخت.

## تفسیر

این خروجی خطای فنی نیست. نتیجه نشان می‌دهد تفکیک فعلی بر اساس Side و Regime به‌تنهایی مشکل Edge منفی Score را حل نمی‌کند. پایین‌آوردن Threshold یا فعال‌کردن دستی Policy در این وضعیت Overfitting و نقض Fail-Closed است.

## تصمیم ایمنی

- `--promote` اجرا نشود.
- Paper/Live بدون تغییر باقی بماند.
- داده Segmentهای Sideways/Volatile/Quiet باید بیشتر شود.
- قدم پژوهشی بعدی باید روی علت ضعف Score، Attribution مؤلفه‌ها و Label/Payoff design تمرکز کند؛ نه جست‌وجوی Thresholdهای بیشتر روی همین داده.
