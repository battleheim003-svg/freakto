# Freakto v10.2.0 — Score Calibration & Feature Attribution Lab

این ماژول بررسی می‌کند که آیا افزایش Score واقعاً با بهبود نتیجه آینده همراه است و کدام اجزای Score رابطه پایدار یا معکوس با Net Return دارند.

## اجرا

```cmd
python -X utf8 replay_score_calibration_dashboard.py --compact
```

برای اجرای بدون ذخیره فایل:

```cmd
python -X utf8 replay_score_calibration_dashboard.py --compact --no-save
```

## ورودی

```text
logs/market_replay/market_replay_evaluations.csv
```

ابتدا v10.1.5 را اجرا کن تا metricهای canonical موجود باشند:

```cmd
python -X utf8 replay_evaluation_recorder_dashboard.py --apply
```

## خروجی‌ها

```text
logs/market_replay/calibration/replay_score_calibration_*.json
logs/market_replay/calibration/replay_score_calibration_*_report.md
logs/market_replay/calibration/replay_score_calibration_*_score_bands.csv
logs/market_replay/calibration/replay_score_calibration_*_feature_attribution.csv
logs/market_replay/calibration/replay_score_calibration_*_interactions.csv
logs/market_replay/calibration/replay_score_calibration_*_segments.csv
logs/market_replay/calibration/replay_score_calibration_observations.csv
```

## روش جلوگیری از Overfit

- Splitهای زمانی Train/Validation/Test حفظ می‌شوند.
- Q25 و Q75 هر Feature فقط از `TRAIN_60` محاسبه می‌شود.
- همان Threshold بدون تغییر روی Validation و Test اعمال می‌شود.
- Interaction فقط وقتی Candidate می‌شود که Train، Validation و Test همگی Net مثبت و Validation/Test دارای PF بالاتر از 1 باشند.
- هیچ وزن یا Config به‌صورت خودکار تغییر نمی‌کند.

## تفسیر Verdictها

- `SCORE_INVERTED_OR_MISCALIBRATED`: Score بالاتر در Test بهتر نیست یا حتی بدتر است.
- `SCORE_MONOTONIC_RESEARCH_SIGNAL`: Score در Validation/Test رابطه مرتب و مثبت نشان داده است؛ هنوز فقط Research.
- `STABLE_POSITIVE_ASSOCIATION`: Feature در هر سه Split رابطه مثبت پایدار دارد.
- `STABLE_INVERSE_ASSOCIATION`: افزایش Feature در هر سه Split با نتیجه ضعیف‌تر همراه بوده است.
- `FORWARD_SHADOW_INTERACTION_CANDIDATE`: ترکیب Featureها شرایط سخت Research را پاس کرده و فقط برای Forward Shadow مناسب است.

## ایمنی

این ماژول فقط Association و Calibration را بررسی می‌کند. نتیجه آن علت قطعی نیست و هیچ Paper/Live/Order واقعی فعال نمی‌کند.
