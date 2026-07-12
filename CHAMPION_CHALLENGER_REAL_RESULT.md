# Freakto Champion–Challenger Real Replay Result

## وضعیت نهایی

```text
Status                  : FAIL
Mode                    : RESEARCH_SHADOW_ONLY
Selected replay run     : market_replay_20260711_192507
Rows loaded / usable    : 78,452 / 14,174
Recommended challenger  : NONE
Promotion applied       : False
Paper / Live enabled    : False
```

این `FAIL` خطای فنی نیست. مدل‌ها Fit و Evaluate شدند، اما هیچ Variant نتوانست Edge مثبت و پایدار خارج از نمونه حفظ کند.

## Split زمانی

مرزها با timestampهای یکتا و Purge شش‌کندلی ساخته شدند:

```text
Train     : 8,115 rows
            2023-07-30 12:00 UTC → 2025-04-25 12:00 UTC

Optimize  : 2,953 rows
            2025-04-26 20:00 UTC → 2025-12-03 12:00 UTC

Holdout   : 3,082 rows
            2025-12-05 00:00 UTC → 2026-07-08 12:00 UTC
```

## Champion Benchmark روی Holdout

```text
Samples                 : 436
Win Rate                : 32.7982%
Expectancy              : -0.900106%
Profit Factor           : 0.442878
Max Drawdown            : -426.342212%
Expectancy CI95         : [-1.165411%, -0.634802%]
```

این Champion یک benchmark تحقیقاتی از Score و Gateهای تکنیکال فعلی است. Empirical Edge Gate عملیاتی دور زده یا تغییر داده نشده است.

## Challengerها

### EXPECTANCY_BASE

Threshold `0.50%` روی Optimize انتخاب شد، اما روی Holdout شکست خورد:

```text
Selected Holdout Samples : 85
Expectancy               : -1.450304%
Profit Factor            : 0.359434
Walk-forward Pass Rate   : 0%
```

Diagnostic ثابت `EV >= 0`:

```text
Samples                  : 1,084
Expectancy               : -0.793016%
Profit Factor            : 0.489276
```

### EXPECTANCY_NO_MOMENTUM

هیچ Threshold معتبری روی Optimize باقی نماند.

```text
EV >= 0 Samples          : 1,032
EV >= 0 Expectancy       : -0.889174%
EV >= 0 Profit Factor    : 0.453250
Walk-forward Pass Rate   : 0%
```

### EXPECTANCY_STRUCTURE_GATE

هیچ Threshold معتبری روی Optimize باقی نماند.

```text
EV >= 0 Samples          : 881
EV >= 0 Expectancy       : -0.887243%
EV >= 0 Profit Factor    : 0.453976
Walk-forward Pass Rate   : 0%
```

### EXPECTANCY_LONG_ONLY / EXPECTANCY_SHORT_DISABLED

این دو خروجی عمداً معادل‌اند و حالت LONG-only را با نام صریح SHORT-disabled گزارش می‌کنند.

```text
EV >= 0 Samples          : 501
EV >= 0 Expectancy       : -1.074534%
EV >= 0 Profit Factor    : 0.380860
Walk-forward Pass Rate   : 0%
```

در این Holdout، غیرفعال‌کردن SHORT نتیجه را بهتر نکرد؛ LONG-only از مدل دوطرفه نیز ضعیف‌تر بود.

## کیفیت پیش‌بینی

مدل پایه روی تمام ۳٬۰۸۲ سطر Holdout پیش‌بینی ایجاد کرد:

```text
Probability Brier Score       : 0.249808
EV / Realized Return Spearman : -0.039990
Predicted EV P10              : -0.090783%
Predicted EV P50              :  0.055456%
Predicted EV P90              :  0.345186%
```

همبستگی منفی نزدیک صفر نشان می‌دهد EV پیش‌بینی‌شده ترتیب بازده واقعی آینده را به‌شکل قابل‌اعتماد رتبه‌بندی نکرده است.

## نتیجه Walk-forward

هیچ Variant از سه Fold عبور نکرد:

```text
EXPECTANCY_BASE              : 0 / 3
EXPECTANCY_NO_MOMENTUM       : 0 / 3
EXPECTANCY_STRUCTURE_GATE    : 0 / 3
EXPECTANCY_LONG_ONLY         : 0 / 3
EXPECTANCY_SHORT_DISABLED    : 0 / 3
```

در بعضی Optimize windowها Edge ظاهراً مثبت دیده شد، اما روی Test window بعدی منفی شد. این همان ناپایداری زمانی است که Champion–Challenger باید تشخیص دهد.

## نتیجه علمی

- جایگزینی Score جمع‌شونده با یک مدل ساده Expected Value به‌تنهایی مشکل را حل نکرد.
- حذف Momentum Edge ایجاد نکرد.
- تبدیل Structure به Gate Edge ایجاد نکرد.
- نگه‌داشتن Volume به‌عنوان Confirmation کافی نبود.
- LONG-only در Holdout جدید بهتر از مدل دوطرفه نبود.
- Threshold انتخاب‌شده روی Optimize به Holdout تعمیم پیدا نکرد.
- هیچ Challenger برای Promotion یا Paper Trading اصلی مناسب نیست.

## تصمیم ایمنی

```text
Champion replacement : BLOCKED
Runtime weight change : BLOCKED
Paper Trading         : UNCHANGED
Live Trading          : UNCHANGED
Order execution       : DISABLED
```

قدم بعدی نباید تغییر مجدد Weight یا Threshold باشد. ابتدا باید کیفیت Label و اقتصاد Outcome بررسی شود؛ به‌خصوص اثر افق ثابت شش‌کندلی، هم‌زمانی Target و Stop، هزینه‌ها، و تعریف Exit در Replay.
