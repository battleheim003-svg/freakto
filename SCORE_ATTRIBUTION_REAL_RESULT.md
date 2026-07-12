# Freakto Score Attribution & Component Ablation — Real Result

## اجرای واقعی

```text
Selected replay run : market_replay_20260711_192507
Rows file/usable    : 78,452 / 14,174
Directional rows    : LONG 7,453 / SHORT 6,721
Components          : 9
Status              : COMPLETE
Promotion           : NOT AVAILABLE (research-only)
```

فقط جدیدترین Replay Run استفاده شد تا تاریخ بازار مشترک بین Runهای قبلی تکراری شمرده نشود.

## اقتصاد کلی تصمیم‌ها

```text
Samples                 : 14,174
Win Rate                : 38.6482%
Average Net Return      : -0.438369%
Median Net Return       : -0.696932%
Profit Factor           : 0.708966
Average Win             : +2.763073%
Average Loss            : -2.455101%
Payoff-implied BE Rate  : 47.0490%
Actual - Break-even     : -8.4008 percentage points
Stop Hit Rate           : 55.4466%
```

ریشه اصلی فقط بزرگ‌بودن Loss نیست؛ Win Rate واقعی حدود 8.4 واحد درصد پایین‌تر از نرخ لازم برای سربه‌سرشدن است.

تفکیک Side:

```text
LONG  : n=7,453 | WR=40.2120% | Exp=-0.291882% | PF=0.792666
SHORT : n=6,721 | WR=36.9141% | Exp=-0.600810% | PF=0.628081
```

SHORT به‌وضوح ضعیف‌تر است.

## تعمیم مدل مؤلفه‌ها

مدل Ridge فقط روی Development ساخته شد و روی Holdout زمانی ارزیابی شد:

```text
Holdout R²                         : -0.003166
Holdout prediction/return Spearman : -0.013319
```

یعنی ترکیب خطی Componentها روی زمان جدید تعمیم پیدا نکرد. بنابراین تغییر مستقیم Weightها از روی ضریب‌ها قابل دفاع نیست.

Permutation Attribution روی Holdout:

```text
Positive holdout value : Adaptive Adjustment, Risk Penalty, Regime, Momentum
No positive value      : Trend, Volume, Structure
Inactive in Replay     : External Context, Historical Edge
```

این نتیجه به‌تنهایی توصیه حذف نیست، چون Componentها با هم هم‌بستگی و اثر Gate دارند.

## رابطه یک‌متغیره

```text
Momentum     : Higher points associated with worse return
Regime       : Higher points associated with better return
Risk Penalty : Less-negative penalty associated with better return
Trend        : Weak/mixed
Volume       : Weak/mixed overall; materially different between LONG and SHORT
Structure    : Weak/mixed overall
Adaptive     : Mixed; weaker behavior in SHORT
```

## Score Band

هیچ Score Band با حجم حداقل 80 نمونه هم‌زمان Expectancy مثبت و Profit Factor حداقل 1 نداشت.

تنها بازه مثبت:

```text
Score 90-100 : n=30 | Avg Return=+0.273462% | PF=1.249912
```

حجم 30 نمونه برای Promotion کافی نیست و Median آن همچنان `-1.004897%` بود؛ بنابراین این نتیجه ناپایدار و غیرقابل استفاده است.

## Ablation روی Holdout با Gate ثابت Score >= 70

```text
FULL
n=590 | Exp=-0.746615% | PF=0.496742

WITHOUT STRUCTURE
n=243 | Exp=-0.434103% | PF=0.668691
Delta Exp=+0.312512%
Diagnosis=REMOVAL_IMPROVES_BUT_NEGATIVE

WITHOUT VOLUME
n=180 | Exp=-1.088894% | PF=0.292121
Delta Exp=-0.342279%
Diagnosis=REMOVAL_HURTS
```

حذف Structure نتیجه را کمتر منفی کرد، اما Edge مثبت نساخت. این تضاد با بعضی رابطه‌های یک‌متغیره نشان می‌دهد Structure احتمالاً در **Gate interaction / score inflation** مشکل دارد، نه اینکه همیشه اطلاعات بدی تولید کند.

حذف Volume نتیجه را واضحاً بدتر کرد؛ بنابراین کاهش یا حذف مستقیم Volume توصیه نمی‌شود.

حذف Trend یا Momentum باعث شد در Gate ثابت 70 نمونه‌ای باقی نماند؛ پس اثر آن‌ها با این روش قابل مقایسه مستقیم نبود.

## Threshold Stability

Full Score روی Optimize آستانه 85 را انتخاب کرد، اما روی Holdout:

```text
Selected Threshold : 85
Holdout n          : 54
Holdout Expectancy : -1.301235%
Holdout PF         : 0.271155
```

این شکست نشان می‌دهد Thresholdهای ظاهراً مثبت در یک بازه زمانی پایدار نیستند.

## نتیجه نهایی

1. Score فعلی Proxy قابل‌اعتماد Edge نیست.
2. مشکل با پایین‌آوردن یا بالابردن Threshold حل نمی‌شود.
3. SHORT از LONG ضعیف‌تر است و باید در آزمایش بعدی محدود یا جداگانه بازطراحی شود.
4. Structure احتمال Score Inflation/Gate Interaction دارد، ولی حذف آن هنوز Edge مثبت نساخت.
5. Volume نقش محافظتی دارد و حذفش مضر بود.
6. Historical Edge و External Context در Replay فعلی صفر بودند و عملاً قابل ارزیابی نیستند.
7. هیچ Weight جدیدی نباید Promote شود.

## آزمایش بعدی پیشنهادی

ساخت **Candidate Score v2** به‌صورت Research-only:

- کاهش وزن Structure به‌جای حذف کامل؛
- محدودکردن یا Gate سخت‌تر برای SHORT؛
- حفظ Volume؛
- بررسی Interactionهای Side × Component و Regime × Component؛
- اجرای Replay کامل از ابتدا برای هر Candidate؛
- انتخاب فقط با Walk-forward و Holdout جدید.
