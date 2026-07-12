# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-12T15:43:22.508718+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 56
- Overall Directional Win: 71.43%
- Overall Target 1 Hit: 46.43%
- Mean Calibration Error: 27.18 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 56/100

## Confidence Label Buckets
- **Low**: n=31, predicted=25.0%, directional=67.74%, T1=12.90%, gap=+42.74, verdict=UNDER_CONFIDENT
- **Medium**: n=16, predicted=55.0%, directional=68.75%, T1=87.50%, gap=+13.75, verdict=UNDER_CONFIDENT
- **Medium-High**: n=9, predicted=67.5%, directional=88.89%, T1=88.89%, gap=+21.39, verdict=LOW_SAMPLE

## Score Buckets
- **score_10_19**: n=3, predicted=14.5%, directional=66.67%, T1=0.00%, gap=+52.17, verdict=LOW_SAMPLE
- **score_20_29**: n=5, predicted=24.5%, directional=80.00%, T1=0.00%, gap=+55.50, verdict=LOW_SAMPLE
- **score_30_39**: n=15, predicted=34.5%, directional=66.67%, T1=0.00%, gap=+32.17, verdict=UNDER_CONFIDENT
- **score_40_49**: n=6, predicted=44.5%, directional=50.00%, T1=33.33%, gap=+5.50, verdict=LOW_SAMPLE
- **score_50_59**: n=7, predicted=54.5%, directional=85.71%, T1=100.00%, gap=+31.21, verdict=LOW_SAMPLE
- **score_60_69**: n=11, predicted=64.5%, directional=63.64%, T1=81.82%, gap=-0.86, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_70_79**: n=9, predicted=74.5%, directional=88.89%, T1=88.89%, gap=+14.39, verdict=LOW_SAMPLE