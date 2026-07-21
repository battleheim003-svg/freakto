# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-21T17:02:46.211506+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 93
- Overall Directional Win: 63.44%
- Overall Target 1 Hit: 37.63%
- Mean Calibration Error: 21.10 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 93/100

## Confidence Label Buckets
- **Low**: n=33, predicted=25.0%, directional=63.64%, T1=21.21%, gap=+38.64, verdict=UNDER_CONFIDENT
- **nan**: n=32, predicted=50.0%, directional=59.38%, T1=0.00%, gap=+9.38, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium**: n=17, predicted=55.0%, directional=64.71%, T1=100.00%, gap=+9.71, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium-High**: n=11, predicted=67.5%, directional=72.73%, T1=100.00%, gap=+5.23, verdict=WELL_CALIBRATED_DIRECTIONAL

## Score Buckets
- **score_10_19**: n=5, predicted=14.5%, directional=60.00%, T1=0.00%, gap=+45.50, verdict=LOW_SAMPLE
- **score_20_29**: n=11, predicted=24.5%, directional=63.64%, T1=0.00%, gap=+39.14, verdict=UNDER_CONFIDENT
- **score_30_39**: n=26, predicted=34.5%, directional=65.38%, T1=0.00%, gap=+30.88, verdict=UNDER_CONFIDENT
- **score_40_49**: n=15, predicted=44.5%, directional=53.33%, T1=33.33%, gap=+8.83, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_50_59**: n=11, predicted=54.5%, directional=81.82%, T1=63.64%, gap=+27.32, verdict=UNDER_CONFIDENT
- **score_60_69**: n=13, predicted=64.5%, directional=53.85%, T1=92.31%, gap=-10.65, verdict=OVER_CONFIDENT
- **score_70_79**: n=12, predicted=74.5%, directional=66.67%, T1=91.67%, gap=-7.83, verdict=WELL_CALIBRATED_DIRECTIONAL