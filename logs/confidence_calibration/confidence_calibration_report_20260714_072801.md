# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-14T07:28:00.366520+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 64
- Overall Directional Win: 62.50%
- Overall Target 1 Hit: 40.62%
- Mean Calibration Error: 21.64 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 64/100

## Confidence Label Buckets
- **Low**: n=33, predicted=25.0%, directional=63.64%, T1=12.12%, gap=+38.64, verdict=UNDER_CONFIDENT
- **nan**: n=3, predicted=50.0%, directional=0.00%, T1=0.00%, gap=-50.00, verdict=LOW_SAMPLE
- **Medium**: n=17, predicted=55.0%, directional=64.71%, T1=82.35%, gap=+9.71, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium-High**: n=11, predicted=67.5%, directional=72.73%, T1=72.73%, gap=+5.23, verdict=WELL_CALIBRATED_DIRECTIONAL

## Score Buckets
- **score_10_19**: n=4, predicted=14.5%, directional=50.00%, T1=0.00%, gap=+35.50, verdict=LOW_SAMPLE
- **score_20_29**: n=5, predicted=24.5%, directional=80.00%, T1=0.00%, gap=+55.50, verdict=LOW_SAMPLE
- **score_30_39**: n=18, predicted=34.5%, directional=55.56%, T1=0.00%, gap=+21.06, verdict=UNDER_CONFIDENT
- **score_40_49**: n=7, predicted=44.5%, directional=42.86%, T1=28.57%, gap=-1.64, verdict=LOW_SAMPLE
- **score_50_59**: n=7, predicted=54.5%, directional=85.71%, T1=100.00%, gap=+31.21, verdict=LOW_SAMPLE
- **score_60_69**: n=12, predicted=64.5%, directional=58.33%, T1=75.00%, gap=-6.17, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_70_79**: n=11, predicted=74.5%, directional=72.73%, T1=72.73%, gap=-1.77, verdict=WELL_CALIBRATED_DIRECTIONAL