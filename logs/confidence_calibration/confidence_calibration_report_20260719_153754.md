# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-19T15:37:53.468401+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 84
- Overall Directional Win: 63.10%
- Overall Target 1 Hit: 41.67%
- Mean Calibration Error: 20.39 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 84/100

## Confidence Label Buckets
- **Low**: n=33, predicted=25.0%, directional=63.64%, T1=21.21%, gap=+38.64, verdict=UNDER_CONFIDENT
- **nan**: n=23, predicted=50.0%, directional=56.52%, T1=0.00%, gap=+6.52, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium**: n=17, predicted=55.0%, directional=64.71%, T1=100.00%, gap=+9.71, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium-High**: n=11, predicted=67.5%, directional=72.73%, T1=100.00%, gap=+5.23, verdict=WELL_CALIBRATED_DIRECTIONAL

## Score Buckets
- **score_10_19**: n=5, predicted=14.5%, directional=60.00%, T1=0.00%, gap=+45.50, verdict=LOW_SAMPLE
- **score_20_29**: n=11, predicted=24.5%, directional=63.64%, T1=0.00%, gap=+39.14, verdict=UNDER_CONFIDENT
- **score_30_39**: n=23, predicted=34.5%, directional=60.87%, T1=0.00%, gap=+26.37, verdict=UNDER_CONFIDENT
- **score_40_49**: n=10, predicted=44.5%, directional=50.00%, T1=50.00%, gap=+5.50, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_50_59**: n=11, predicted=54.5%, directional=81.82%, T1=63.64%, gap=+27.32, verdict=UNDER_CONFIDENT
- **score_60_69**: n=13, predicted=64.5%, directional=53.85%, T1=92.31%, gap=-10.65, verdict=OVER_CONFIDENT
- **score_70_79**: n=11, predicted=74.5%, directional=72.73%, T1=100.00%, gap=-1.77, verdict=WELL_CALIBRATED_DIRECTIONAL