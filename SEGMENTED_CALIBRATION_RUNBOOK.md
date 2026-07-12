# Freakto Side & Regime Segmented Calibration Runbook

این مرحله یک آزمایش Research-only است. هیچ سفارش Live، Paper position یا تنظیم Actionability را فعال نمی‌کند.

## هدف

اعتبارسنجی جداگانه‌ی Score و Edge Gate برای این Segmentهای از پیش تعریف‌شده:

- `SIDE:LONG` و `SIDE:SHORT`
- `REGIME:BULL`, `REGIME:BEAR`, `REGIME:SIDEWAYS`, `REGIME:VOLATILE`, `REGIME:QUIET`
- ترکیب‌های `SIDE_REGIME:<SIDE>|<REGIME>`

برچسب‌های ناشناخته به `UNKNOWN` نگاشت می‌شوند و فقط برای تشخیص گزارش می‌شوند؛ هیچ Policy از Segment ناشناخته قابل Promotion نیست.

## قرارداد ضد نشت داده

1. کل دیتاست یک بار به ترتیب زمان مرتب می‌شود.
2. همه Segmentها از مرز مشترک `Train → Purge → Optimize → Purge → Holdout` استفاده می‌کنند.
3. جدول Score-to-Probability فقط روی Train همان Segment ساخته می‌شود.
4. Threshold فقط روی Optimize همان Segment انتخاب می‌شود.
5. Holdout برای انتخاب Policy استفاده نمی‌شود و فقط یک بار نتیجه نهایی را می‌سنجد.
6. Walk-forward فقط روی دوره Development یعنی `Train + Optimize` اجرا می‌شود و Holdout نهایی را لمس نمی‌کند.
7. Outcome/Return فقط Target ارزیابی است و در تعریف Segment یا نگاشت Score به‌عنوان Feature استفاده نمی‌شود.

## اقتصاد معامله

برای هر Segment، احتمال سربه‌سر از میانگین سود و میانگین زیان Train محاسبه می‌شود:

```text
break_even_probability = avg_loss / (avg_win + avg_loss)
```

اگر تعداد برد یا باخت Train کافی نباشد، مقدار ایمن 50% استفاده می‌شود. این مقدار فقط از Train به دست می‌آید.

## اجرای تست‌ها

```bat
python -m pytest
```

اجرای فقط تست‌های این مرحله:

```bat
python -m pytest tests/test_segmented_calibration.py tests/test_segmented_threshold_optimizer.py
```

## اجرای اعتبارسنجی

```bat
python -X utf8 segmented_calibration_validation.py
```

مسیر پیش‌فرض ورودی:

```text
logs/calibration_dataset/calibration_training.csv
```

اجرای سفارشی:

```bat
python -X utf8 segmented_calibration_validation.py ^
  --input logs/calibration_dataset/calibration_training.csv ^
  --output-dir logs/segmented_calibration_validation ^
  --minimum-train-rows 120 ^
  --minimum-optimize-rows 40 ^
  --minimum-holdout-rows 40 ^
  --minimum-selected-optimize 20 ^
  --minimum-selected-holdout 20
```

## معنی Exit Code

- `0`: حداقل یک Segment تمام شروط سخت `PASS` را گذرانده است.
- `2`: هیچ Segment قابل Promotion پیدا نشده است. این می‌تواند یک نتیجه تحقیقاتی صحیح باشد و لزوماً خطای برنامه نیست.

## خروجی‌ها

در `logs/segmented_calibration_validation/`:

- `segment_summary.csv`: خلاصه همه Segmentها و دلیل Pass/Fail
- `segmented_score_calibration_train.csv`: نگاشت‌هایی که فقط با Train ساخته شده‌اند
- `segmented_score_calibration_candidate.csv`: نگاشت نهایی Candidate بعد از اتمام اعتبارسنجی
- `segment_threshold_candidates.csv`: تمام Thresholdهای بررسی‌شده
- `segment_holdout_scored.csv`: Holdout کالیبره‌شده و ماسک انتخاب Policy
- `segment_walk_forward_folds.csv`: مرزها و نتیجه Foldهای توسعه‌ای
- `recommended_segmented_edge_gate_policy.json`: فقط Policyهای `PASS`
- `segmented_calibration_validation_report.json`: گزارش کامل قابل‌ماشین‌خواندن

## شروط سخت PASS

یک Segment فقط وقتی `PASS` می‌شود که:

- Train، Optimize و Holdout حجم کافی داشته باشند؛
- Threshold در Optimize Expectancy مثبت و Profit Factor حداقل 1 داشته باشد؛
- Holdout حداقل تعداد انتخاب لازم، Expectancy مثبت و Profit Factor حداقل 1.05 داشته باشد؛
- Brier Score و ECE از سقف‌های تعیین‌شده عبور نکنند؛
- Walk-forward دوره Development پایدار باشد؛
- حد پایین فاصله اطمینان 95% Expectancy مثبت باشد؛
- حجم نمونه و Profit Factor از Gate قوی Promotion عبور کنند.

`PASS_WITH_WARNINGS` هرگز به‌صورت خودکار Promote نمی‌شود.

## Promotion

فعلاً فقط بعد از مشاهده `Status: PASS` قابل اجرا است:

```bat
python -X utf8 segmented_calibration_validation.py --promote
```

در حالت `FAIL` یا نبود Policy سخت، Promotion مسدود می‌شود و فایل Runtime ساخته نخواهد شد.
