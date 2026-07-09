# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-09T00:21:26.257719+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 43
- Overall Directional Win: 74.42%
- Overall Target 1 Hit: 55.81%
- Mean Calibration Error: 27.80 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 43/100

## Confidence Label Buckets
- **Low**: n=20, predicted=25.0%, directional=65.00%, T1=15.00%, gap=+40.00, verdict=UNDER_CONFIDENT
- **Medium**: n=15, predicted=55.0%, directional=73.33%, T1=86.67%, gap=+18.33, verdict=UNDER_CONFIDENT
- **Medium-High**: n=8, predicted=67.5%, directional=100.00%, T1=100.00%, gap=+32.50, verdict=LOW_SAMPLE

## Score Buckets
- **score_10_19**: n=3, predicted=14.5%, directional=66.67%, T1=0.00%, gap=+52.17, verdict=LOW_SAMPLE
- **score_20_29**: n=1, predicted=24.5%, directional=0.00%, T1=0.00%, gap=-24.50, verdict=LOW_SAMPLE
- **score_30_39**: n=12, predicted=34.5%, directional=66.67%, T1=0.00%, gap=+32.17, verdict=UNDER_CONFIDENT
- **score_40_49**: n=2, predicted=44.5%, directional=50.00%, T1=50.00%, gap=+5.50, verdict=LOW_SAMPLE
- **score_50_59**: n=7, predicted=54.5%, directional=85.71%, T1=100.00%, gap=+31.21, verdict=LOW_SAMPLE
- **score_60_69**: n=10, predicted=64.5%, directional=70.00%, T1=80.00%, gap=+5.50, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_70_79**: n=8, predicted=74.5%, directional=100.00%, T1=100.00%, gap=+25.50, verdict=LOW_SAMPLE