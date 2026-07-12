# Freakto Score Attribution & Component Ablation Runbook

این مرحله یک ابزار **Research-only** برای پیدا کردن علت منفی‌بودن Edge است. هیچ وزن Runtime، Quality Gate، Paper Trading یا Live Trading را تغییر نمی‌دهد.

## هدف

تحلیل می‌کند که مؤلفه‌های زیر چه رابطه‌ای با بازده خالص آینده دارند:

- Trend
- Momentum
- Volume
- Structure
- Regime
- Risk Penalty
- External Context
- Adaptive Adjustment
- Historical Edge

سپس Score ثبت‌شده را به‌صورت Counterfactual بازسازی می‌کند:

```text
Full Score
Full Score - Trend
Full Score - Momentum
Full Score - Volume
Full Score - Structure
...
```

این Ablation به‌معنی تغییر موتور نیست؛ فقط اثر حذف هر مؤلفه از Score ثبت‌شده را روی انتخاب‌های تاریخی بررسی می‌کند.

## ورودی صحیح

مسیر پیش‌فرض:

```text
logs/market_replay/market_replay_evaluations.csv
```

فایل باید علاوه بر Return، ستون‌های Component را داشته باشد. فایل کاهش‌یافته زیر برای این مرحله کافی نیست:

```text
logs/calibration_dataset/calibration_training.csv
```

زیرا Component Scoreها در آن وجود ندارند.

اگر چند Replay Run داخل فایل باشد، ابزار به‌صورت پیش‌فرض فقط جدیدترین `run_id` را انتخاب می‌کند تا یک تاریخ بازار چند بار شمرده نشود.

## قرارداد ضد نشت داده

1. فقط Componentهایی استفاده می‌شوند که هنگام تصمیم وجود داشته‌اند.
2. ستون‌های Return، Win، Target Hit، Stop Hit، MFE، MAE، Outcome و Future نمی‌توانند Feature باشند.
3. داده بر اساس `candle_timestamp` مرتب می‌شود.
4. Ridge Attribution روی Development ساخته و فقط روی Holdout زمانی ارزیابی می‌شود.
5. Thresholdهای Ablation فقط روی Optimize انتخاب می‌شوند.
6. Holdout برای انتخاب Threshold یا وزن استفاده نمی‌شود.
7. نتیجه هیچ Weight یا Gate را خودکار Promote نمی‌کند.

## اجرای تست‌ها

```bat
python -m pytest
```

فقط تست‌های این مرحله:

```bat
python -m pytest tests/test_score_attribution.py tests/test_component_ablation.py
```

## اجرای تحلیل

```bat
python -X utf8 score_attribution_analysis.py
```

ورودی یا Run سفارشی:

```bat
python -X utf8 score_attribution_analysis.py ^
  --input logs\market_replay\market_replay_evaluations.csv ^
  --run-id market_replay_YYYYMMDD_HHMMSS
```

استفاده از همه Runها فقط برای بررسی خاص:

```bat
python -X utf8 score_attribution_analysis.py --all-runs
```

این حالت ممکن است بازارهای تکراری را چند بار بشمارد و برای نتیجه نهایی توصیه نمی‌شود.

## خروجی‌ها

در مسیر زیر:

```text
logs/score_attribution/
```

فایل‌ها:

- `component_attribution.csv`: رابطه یک‌متغیره هر Component با Return و Win
- `component_bins.csv`: عملکرد بازه‌های کم تا زیاد هر Component
- `model_attribution.csv`: ضریب Ridge و Permutation Importance روی Holdout
- `score_band_performance.csv`: عملکرد بازه‌های Score
- `decision_economics.csv`: Win Rate، Avg Win/Loss، Break-even، PF و Drawdown
- `component_ablation_summary.csv`: نتیجه Full و حذف هر Component
- `component_ablation_threshold_candidates.csv`: Thresholdهای بررسی‌شده فقط روی Optimize
- `score_attribution_report.json`: گزارش Attribution
- `component_ablation_report.json`: گزارش Ablation
- `score_attribution_combined_report.json`: گزارش ماشین‌خوان کامل
- `score_attribution_root_cause_report.md`: گزارش خوانا

## معنی Diagnosisهای Ablation

- `BASELINE`: Full Score
- `INACTIVE`: Component در Replay مقدار مؤثر نداشته است
- `REMOVAL_RESTORES_EDGE`: حذف مؤلفه روی Holdout Edge مثبت ساخته است
- `REMOVAL_IMPROVES_BUT_NEGATIVE`: نتیجه کمتر منفی شده، اما هنوز قابل استفاده نیست
- `REMOVAL_HURTS`: حذف مؤلفه نتیجه را بدتر کرده است
- `NEUTRAL_OR_MIXED`: اثر کوچک یا متناقض
- `INSUFFICIENT_HOLDOUT_SELECTION`: بعد از حذف Component، نمونه کافی بالای Gate باقی نمانده است

## قانون تصمیم

حتی اگر حذف یک Component نتیجه را بهتر کند، وزن موتور نباید مستقیم تغییر کند. قبل از هر تغییر Runtime باید:

1. یک نسخه Candidate از وزن‌ها تعریف شود؛
2. Market Replay از ابتدا دوباره اجرا شود؛
3. Calibration و Segmented Calibration تکرار شوند؛
4. Walk-forward و Holdout مثبت باشند؛
5. سپس Shadow Mode اجرا شود.

## Safety

این ابزار سفارش ایجاد نمی‌کند، فایل Policy Runtime نمی‌سازد و گزینه Promotion ندارد.
