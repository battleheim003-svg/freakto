# Freakto Expectancy-Aware Champion–Challenger Runbook

## هدف

این مرحله یک موتور تصمیم دوم را در کنار Decision Engine فعلی ایجاد می‌کند:

- **Champion:** منطق امتیاز و Quality Gate فعلی، فقط به‌عنوان benchmark تحقیقاتی
- **Challenger:** مدل جداگانه مبتنی بر Expected Value

Challenger فقط در حالت **Research / Shadow** اجرا می‌شود. این مرحله:

- وزن‌های Decision Engine را تغییر نمی‌دهد.
- Champion را جایگزین نمی‌کند.
- Paper Trading یا Live Trading را فعال نمی‌کند.
- سفارش یا معامله‌ای ایجاد نمی‌کند.
- هیچ فایل تنظیمات عملیاتی را Promote نمی‌کند.

## فایل‌های اصلی

```text
engine/expectancy_challenger.py
engine/champion_challenger.py
champion_challenger_analysis.py
tests/test_expectancy_challenger.py
tests/test_champion_challenger.py
```

## منطق Challenger

برای LONG و SHORT مدل‌های جداگانه ساخته می‌شوند:

1. برآورد احتمال برد با Logistic Regression
2. برآورد اندازه متوسط برد با Ridge Regression
3. برآورد اندازه متوسط باخت با Ridge Regression
4. محاسبه Expected Value:

```text
EV = P(win) × Predicted Win
   - P(loss) × Predicted Loss
   - Extra Execution Buffer
   - Explicit Risk Cost
```

بازده هدف `evaluated_return` از Replay، بازده خالص پس از اقتصاد Entry/Stop/Target است. بنابراین مدل‌های Payoff، نتیجه واقعی همان اقتصاد ورود، حدضرر و اهداف را یاد می‌گیرند؛ اما این ستون فقط Target آموزشی است و Feature تصمیم نیست.

## Featureهای مجاز

فقط اطلاعات موجود در زمان تصمیم استفاده می‌شوند:

```text
trend_score
volume_score
regime_score
risk_penalty
adaptive_adjustment
external_context_score
historical_edge_score
momentum_capped     # فقط در Variantهای دارای Momentum
regime_group
```

موارد زیر Feature نیستند و استفاده از آن‌ها خطا ایجاد می‌کند:

```text
return / future_return
win / loss / outcome
mfe / mae
stop_hit / target_hit
exit_price
```

## تغییرات طراحی نسبت به Score فعلی

- LONG و SHORT جداگانه مدل می‌شوند.
- Momentum در مدل پایه سقف دارد.
- یک Variant بدون Momentum اجرا می‌شود.
- Structure از Featureهای خطی حذف شده و در Variant مربوطه فقط Gate است.
- Volume به‌عنوان Confirmation Gate حفظ شده است.
- Risk Penalty به هزینه واقعی EV تبدیل می‌شود.
- Side یا Model ناشناخته Fail-Closed است.

## Variantها

```text
EXPECTANCY_BASE
EXPECTANCY_NO_MOMENTUM
EXPECTANCY_STRUCTURE_GATE
EXPECTANCY_LONG_ONLY
EXPECTANCY_SHORT_DISABLED
```

`EXPECTANCY_SHORT_DISABLED` یک Alias صریح و ایمنی برای حالت LONG-only است؛ وجود هر دو نام در گزارش باعث می‌شود غیرفعال‌بودن SHORT مبهم نباشد.

## حفاظت زمانی و جلوگیری از Leakage

داده به ترتیب زمان تقسیم می‌شود:

```text
Train → Purge → Optimize → Purge → Holdout
```

مرزها براساس **timestamp یکتا** ساخته می‌شوند، نه تعداد سطر. بنابراین تصمیم‌های هم‌زمان Symbolهای مختلف نمی‌توانند بین دو Split پخش شوند.

`purge_rows=6` در این مرحله عملاً شش timestamp/candle یکتا را بین Splitها حذف می‌کند تا افق شش‌کندلی ارزیابی به بخش بعد نشت نکند.

- Model فقط روی Train Fit می‌شود.
- EV Threshold فقط روی Optimize انتخاب می‌شود.
- Holdout فقط یک‌بار برای ارزیابی نهایی استفاده می‌شود.
- Walk-forward فقط روی بخش پیش از Holdout انجام می‌شود.

## معیارهای Promotion تحقیقاتی

حتی در صورت PASS، Promotion عملیاتی انجام نمی‌شود. یک Variant فقط می‌تواند `PASS_RESEARCH_ONLY` شود که تمام شروط زیر را داشته باشد:

- Threshold معتبر روی Optimize
- حداقل نمونه کافی روی Holdout
- Holdout Expectancy مثبت
- Profit Factor حداقل `1.05`
- Confidence Interval نودوپنج درصد Expectancy کاملاً بالاتر از صفر
- Walk-forward pass rate حداقل دو سوم
- Drawdown به‌طور معنادار بدتر از Champion نباشد
- سود فقط از یک بخش زمانی Holdout نیامده باشد
- مدل دوطرفه، نمونه کافی LONG و SHORT داشته باشد

## نصب و اجرا

از ریشه پروژه:

```bat
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m pytest
python -X utf8 champion_challenger_analysis.py
```

روی نسخه‌ای که قبل از این مرحله ۵۹ تست داشت، باید مجموعاً **۷۱ تست** جمع‌آوری شود.

اجرای روی فایل یا Run مشخص:

```bat
python -X utf8 champion_challenger_analysis.py ^
  --dataset logs\market_replay\market_replay_evaluations.csv ^
  --run-id market_replay_YYYYMMDD_HHMMSS
```

نمایش Variantها:

```bat
python -X utf8 champion_challenger_analysis.py --list-variants
```

تغییر حداقل نمونه Holdout یا بافر اجرایی Shadow:

```bat
python -X utf8 champion_challenger_analysis.py ^
  --minimum-holdout-selected 80 ^
  --additional-execution-cost-pct 0.05
```

## خروجی‌ها

```text
logs/champion_challenger/champion_challenger_summary.csv
logs/champion_challenger/challenger_threshold_candidates.csv
logs/champion_challenger/challenger_walk_forward.csv
logs/champion_challenger/challenger_holdout_shadow_predictions.csv
logs/champion_challenger/champion_challenger_report.json
logs/champion_challenger/champion_challenger_report.md
```

## تفسیر Status

```text
PASS_RESEARCH_ONLY
```

یعنی یک Variant از معیارهای تحقیقاتی عبور کرده، اما هنوز Shadow-only است و جایگزینی انجام نشده است.

```text
FAIL
```

یعنی هیچ Challenger روی Holdout و Walk-forward Edge پایدار نداشته است. این خطای برنامه نیست.

```text
INSUFFICIENT_DATA
```

یعنی حجم داده برای تقسیم زمانی و ارزیابی کافی نیست.

## نکته ایمنی

هیچ گزینه `--promote` در CLI وجود ندارد. این تصمیم عمدی است. Promotion عملیاتی فقط باید در یک مرحله جداگانه، پس از Replay جدید و Forward Shadow مستقل ساخته شود.
