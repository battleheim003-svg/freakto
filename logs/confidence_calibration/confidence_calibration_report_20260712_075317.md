# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-12T07:53:17.147940+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 54
- Overall Directional Win: 74.07%
- Overall Target 1 Hit: 48.15%
- Mean Calibration Error: 29.76 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 54/100

## Confidence Label Buckets
- **Low**: n=30, predicted=25.0%, directional=70.00%, T1=13.33%, gap=+45.00, verdict=UNDER_CONFIDENT
- **Medium**: n=15, predicted=55.0%, directional=73.33%, T1=93.33%, gap=+18.33, verdict=UNDER_CONFIDENT
- **Medium-High**: n=9, predicted=67.5%, directional=88.89%, T1=88.89%, gap=+21.39, verdict=LOW_SAMPLE

## Score Buckets
- **score_10_19**: n=3, predicted=14.5%, directional=66.67%, T1=0.00%, gap=+52.17, verdict=LOW_SAMPLE
- **score_20_29**: n=5, predicted=24.5%, directional=80.00%, T1=0.00%, gap=+55.50, verdict=LOW_SAMPLE
- **score_30_39**: n=15, predicted=34.5%, directional=66.67%, T1=0.00%, gap=+32.17, verdict=UNDER_CONFIDENT
- **score_40_49**: n=5, predicted=44.5%, directional=60.00%, T1=40.00%, gap=+15.50, verdict=LOW_SAMPLE
- **score_50_59**: n=7, predicted=54.5%, directional=85.71%, T1=100.00%, gap=+31.21, verdict=LOW_SAMPLE
- **score_60_69**: n=10, predicted=64.5%, directional=70.00%, T1=90.00%, gap=+5.50, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_70_79**: n=9, predicted=74.5%, directional=88.89%, T1=88.89%, gap=+14.39, verdict=LOW_SAMPLE