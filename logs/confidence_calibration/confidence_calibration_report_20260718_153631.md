# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-18T15:36:31.060314+00:00

- Quality: **CALIBRATION_MIXED**
- Samples: 79
- Overall Directional Win: 60.76%
- Overall Target 1 Hit: 44.30%
- Mean Calibration Error: 19.36 pts

## Warnings
- Calibration متوسط است؛ برخی confidence bucketها نیاز به داده بیشتر دارند.

## Blockers
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 79/100

## Confidence Label Buckets
- **Low**: n=33, predicted=25.0%, directional=63.64%, T1=21.21%, gap=+38.64, verdict=UNDER_CONFIDENT
- **nan**: n=18, predicted=50.0%, directional=44.44%, T1=0.00%, gap=-5.56, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium**: n=17, predicted=55.0%, directional=64.71%, T1=100.00%, gap=+9.71, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium-High**: n=11, predicted=67.5%, directional=72.73%, T1=100.00%, gap=+5.23, verdict=WELL_CALIBRATED_DIRECTIONAL

## Score Buckets
- **score_10_19**: n=4, predicted=14.5%, directional=50.00%, T1=0.00%, gap=+35.50, verdict=LOW_SAMPLE
- **score_20_29**: n=10, predicted=24.5%, directional=60.00%, T1=0.00%, gap=+35.50, verdict=UNDER_CONFIDENT
- **score_30_39**: n=22, predicted=34.5%, directional=59.09%, T1=0.00%, gap=+24.59, verdict=UNDER_CONFIDENT
- **score_40_49**: n=10, predicted=44.5%, directional=50.00%, T1=50.00%, gap=+5.50, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_50_59**: n=9, predicted=54.5%, directional=77.78%, T1=77.78%, gap=+23.28, verdict=LOW_SAMPLE
- **score_60_69**: n=13, predicted=64.5%, directional=53.85%, T1=92.31%, gap=-10.65, verdict=OVER_CONFIDENT
- **score_70_79**: n=11, predicted=74.5%, directional=72.73%, T1=100.00%, gap=-1.77, verdict=WELL_CALIBRATED_DIRECTIONAL