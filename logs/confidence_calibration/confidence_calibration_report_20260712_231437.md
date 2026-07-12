# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-12T23:14:37.331546+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 58
- Overall Directional Win: 68.97%
- Overall Target 1 Hit: 44.83%
- Mean Calibration Error: 24.62 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 58/100

## Confidence Label Buckets
- **Low**: n=32, predicted=25.0%, directional=65.62%, T1=12.50%, gap=+40.62, verdict=UNDER_CONFIDENT
- **Medium**: n=16, predicted=55.0%, directional=68.75%, T1=87.50%, gap=+13.75, verdict=UNDER_CONFIDENT
- **Medium-High**: n=10, predicted=67.5%, directional=80.00%, T1=80.00%, gap=+12.50, verdict=UNDER_CONFIDENT

## Score Buckets
- **score_10_19**: n=3, predicted=14.5%, directional=66.67%, T1=0.00%, gap=+52.17, verdict=LOW_SAMPLE
- **score_20_29**: n=5, predicted=24.5%, directional=80.00%, T1=0.00%, gap=+55.50, verdict=LOW_SAMPLE
- **score_30_39**: n=15, predicted=34.5%, directional=66.67%, T1=0.00%, gap=+32.17, verdict=UNDER_CONFIDENT
- **score_40_49**: n=7, predicted=44.5%, directional=42.86%, T1=28.57%, gap=-1.64, verdict=LOW_SAMPLE
- **score_50_59**: n=7, predicted=54.5%, directional=85.71%, T1=100.00%, gap=+31.21, verdict=LOW_SAMPLE
- **score_60_69**: n=11, predicted=64.5%, directional=63.64%, T1=81.82%, gap=-0.86, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_70_79**: n=10, predicted=74.5%, directional=80.00%, T1=80.00%, gap=+5.50, verdict=WELL_CALIBRATED_DIRECTIONAL