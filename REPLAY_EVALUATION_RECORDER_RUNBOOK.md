# Freakto v10.1.5 — Replay Evaluation Recorder

این Patch مشکل واقعی اتصال Replay و Optimization را برطرف می‌کند.

## نکته مهم

Market Replay v10 از قبل این metricهای واقعی را ثبت می‌کرد:

- `gross_signed_return_after_1c/3c/6c_pct`
- `net_signed_return_after_1c/3c/6c_pct`
- `direction_correct_after_1c/3c/6c`
- `target_1_hit`, `stop_hit`, `mfe_pct`, `mae_pct`

مشکل نسخه‌های v10.1.2 تا v10.1.4 این بود که نام واقعی ستون‌ها را نمی‌شناختند. v10.1.5 هم Replayهای جدید را با schema ثابت ثبت می‌کند و هم فایل‌های قبلی را بدون rerun چندساعته backfill می‌کند.

## 1. Dry Run

```cmd
python -X utf8 replay_evaluation_recorder_dashboard.py
```

خروجی سالم باید ستون source را این‌طور نشان دهد:

```text
Gross Source : gross_signed_return_after_6c_pct
Net Source   : net_signed_return_after_6c_pct
Rows Recorded: بیشتر از صفر
```

## 2. اعمال امن روی CSV موجود

```cmd
python -X utf8 replay_evaluation_recorder_dashboard.py --apply
```

قبل از تغییر فایل، Backup زمان‌دار ساخته می‌شود:

```text
market_replay_evaluations.csv.bak_v1015_YYYYMMDD_HHMMSS
```

## 3. تحلیل واقعی Thresholdها

```cmd
python -X utf8 replay_real_metrics_dashboard.py --compact
```

این داشبورد برای هر Threshold متریک‌های Train/Validation/Test را جداگانه گزارش می‌دهد:

- sample count
- win rate
- average gross/net return
- profit factor
- drawdown proxy
- overfit verdict

## ایمنی

- هیچ وزن Decision Engine تغییر نمی‌کند.
- هیچ Paper Trade جدیدی ایجاد نمی‌شود.
- هیچ سفارش Live ارسال نمی‌شود.
- Candidate فقط در صورت مثبت بودن Validation و Test به `FORWARD_SHADOW_CANDIDATE` تبدیل می‌شود.
