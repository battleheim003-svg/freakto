# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-11T15:37:27.817146+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 52
- Overall Directional Win: 75.00%
- Overall Target 1 Hit: 50.00%
- Mean Calibration Error: 30.23 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 52/100

## Confidence Label Buckets
- **Low**: n=28, predicted=25.0%, directional=71.43%, T1=14.29%, gap=+46.43, verdict=UNDER_CONFIDENT
- **Medium**: n=15, predicted=55.0%, directional=73.33%, T1=93.33%, gap=+18.33, verdict=UNDER_CONFIDENT
- **Medium-High**: n=9, predicted=67.5%, directional=88.89%, T1=88.89%, gap=+21.39, verdict=LOW_SAMPLE

## Score Buckets
- **score_10_19**: n=3, predicted=14.5%, directional=66.67%, T1=0.00%, gap=+52.17, verdict=LOW_SAMPLE
- **score_20_29**: n=5, predicted=24.5%, directional=80.00%, T1=0.00%, gap=+55.50, verdict=LOW_SAMPLE
- **score_30_39**: n=14, predicted=34.5%, directional=71.43%, T1=0.00%, gap=+36.93, verdict=UNDER_CONFIDENT
- **score_40_49**: n=4, predicted=44.5%, directional=50.00%, T1=50.00%, gap=+5.50, verdict=LOW_SAMPLE
- **score_50_59**: n=7, predicted=54.5%, directional=85.71%, T1=100.00%, gap=+31.21, verdict=LOW_SAMPLE
- **score_60_69**: n=10, predicted=64.5%, directional=70.00%, T1=90.00%, gap=+5.50, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_70_79**: n=9, predicted=74.5%, directional=88.89%, T1=88.89%, gap=+14.39, verdict=LOW_SAMPLE