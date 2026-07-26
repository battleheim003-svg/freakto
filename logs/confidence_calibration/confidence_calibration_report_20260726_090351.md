# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-26T09:03:50.579149+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 107
- Overall Directional Win: 60.75%
- Overall Target 1 Hit: 32.71%
- Mean Calibration Error: 20.26 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.

## Confidence Label Buckets
- **Low**: n=33, predicted=25.0%, directional=63.64%, T1=21.21%, gap=+38.64, verdict=UNDER_CONFIDENT
- **nan**: n=46, predicted=50.0%, directional=54.35%, T1=0.00%, gap=+4.35, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium**: n=17, predicted=55.0%, directional=64.71%, T1=100.00%, gap=+9.71, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium-High**: n=11, predicted=67.5%, directional=72.73%, T1=100.00%, gap=+5.23, verdict=WELL_CALIBRATED_DIRECTIONAL

## Score Buckets
- **score_10_19**: n=6, predicted=14.5%, directional=50.00%, T1=0.00%, gap=+35.50, verdict=LOW_SAMPLE
- **score_20_29**: n=12, predicted=24.5%, directional=58.33%, T1=0.00%, gap=+33.83, verdict=UNDER_CONFIDENT
- **score_30_39**: n=27, predicted=34.5%, directional=62.96%, T1=0.00%, gap=+28.46, verdict=UNDER_CONFIDENT
- **score_40_49**: n=18, predicted=44.5%, directional=61.11%, T1=27.78%, gap=+16.61, verdict=UNDER_CONFIDENT
- **score_50_59**: n=13, predicted=54.5%, directional=84.62%, T1=53.85%, gap=+30.12, verdict=UNDER_CONFIDENT
- **score_60_69**: n=17, predicted=64.5%, directional=41.18%, T1=70.59%, gap=-23.32, verdict=OVER_CONFIDENT
- **score_70_79**: n=13, predicted=74.5%, directional=69.23%, T1=84.62%, gap=-5.27, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_90_99**: n=1, predicted=94.5%, directional=0.00%, T1=0.00%, gap=-94.50, verdict=LOW_SAMPLE