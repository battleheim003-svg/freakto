# Freakto Metric Definitions v4.7.1

Created UTC: 2026-07-23T09:33:11.115540+00:00

## Directional Win Rate
- Label: Dir Win
- Source: decision_evaluations.csv
- Formula: `count(return_after_24h_pct > 0) / count(valid evaluated returns)`
- Meaning: درصد تصمیم‌هایی که بازده ارزیابی‌شده آن‌ها مثبت شده است. اگر 24h هنوز موجود نباشد، ماژول‌های ارزیابی ممکن است به 12h یا 4h fallback کنند.
- Used in: Edge Validation, Walk-Forward, Live Readiness notes

## Target 1 Hit Rate
- Label: T1 Hit
- Source: decision_evaluations.csv
- Formula: `count(target_1_hit == True) / count(COMPLETE evaluations)`
- Meaning: درصد تصمیم‌هایی که تارگت اول را زده‌اند. این با مثبت بودن بازده یکی نیست؛ ممکن است بازده مثبت باشد ولی T1 نخورده باشد.
- Used in: Strategy Lab, Regime Matrix, historical target validation

## Paper Trade Win Rate
- Label: Paper Win
- Source: paper_trade_evaluations.csv
- Formula: `count(closed paper trades with positive R or WIN result) / count(closed paper trades)`
- Meaning: درصد معاملات فرضی بسته‌شده که بر اساس R Multiple یا نتیجه ثبت‌شده سودده بوده‌اند.
- Used in: Paper Trading, Live Readiness

## Expectancy
- Label: Expectancy
- Source: decision_evaluations.csv / paper_trade_evaluations.csv
- Formula: `average(return_after_24h_pct) for decisions OR average(r_multiple) for paper trades`
- Meaning: میانگین سود/زیان مورد انتظار در نمونه‌های موجود. برای تصمیم‌ها درصدی و برای Paper Trade بر حسب R است.
- Used in: Edge Validation, Live Readiness, Strategy Lab

## Profit Factor
- Label: PF
- Source: evaluated returns
- Formula: `gross positive returns / abs(gross negative returns)`
- Meaning: نسبت مجموع سودها به مجموع زیان‌ها. در نمونه‌های خیلی کم یا بدون زیان می‌تواند بزرگ و ناپایدار باشد.
- Used in: Edge Validation, Regime Matrix, Live Readiness
