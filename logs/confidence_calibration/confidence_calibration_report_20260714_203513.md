# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-14T20:35:12.619832+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 67
- Overall Directional Win: 64.18%
- Overall Target 1 Hit: 49.25%
- Mean Calibration Error: 20.55 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 67/100

## Confidence Label Buckets
- **Low**: n=33, predicted=25.0%, directional=63.64%, T1=21.21%, gap=+38.64, verdict=UNDER_CONFIDENT
- **nan**: n=6, predicted=50.0%, directional=50.00%, T1=0.00%, gap=+0.00, verdict=LOW_SAMPLE
- **Medium**: n=17, predicted=55.0%, directional=64.71%, T1=100.00%, gap=+9.71, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium-High**: n=11, predicted=67.5%, directional=72.73%, T1=81.82%, gap=+5.23, verdict=WELL_CALIBRATED_DIRECTIONAL

## Score Buckets
- **score_10_19**: n=4, predicted=14.5%, directional=50.00%, T1=0.00%, gap=+35.50, verdict=LOW_SAMPLE
- **score_20_29**: n=5, predicted=24.5%, directional=80.00%, T1=0.00%, gap=+55.50, verdict=LOW_SAMPLE
- **score_30_39**: n=18, predicted=34.5%, directional=55.56%, T1=0.00%, gap=+21.06, verdict=UNDER_CONFIDENT
- **score_40_49**: n=9, predicted=44.5%, directional=55.56%, T1=55.56%, gap=+11.06, verdict=LOW_SAMPLE
- **score_50_59**: n=8, predicted=54.5%, directional=87.50%, T1=87.50%, gap=+33.00, verdict=LOW_SAMPLE
- **score_60_69**: n=12, predicted=64.5%, directional=58.33%, T1=100.00%, gap=-6.17, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_70_79**: n=11, predicted=74.5%, directional=72.73%, T1=81.82%, gap=-1.77, verdict=WELL_CALIBRATED_DIRECTIONAL