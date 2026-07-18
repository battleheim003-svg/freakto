# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-18T07:13:44.290487+00:00

- Quality: **CALIBRATION_MIXED**
- Samples: 78
- Overall Directional Win: 60.26%
- Overall Target 1 Hit: 44.87%
- Mean Calibration Error: 19.44 pts

## Warnings
- Calibration متوسط است؛ برخی confidence bucketها نیاز به داده بیشتر دارند.

## Blockers
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 78/100

## Confidence Label Buckets
- **Low**: n=33, predicted=25.0%, directional=63.64%, T1=21.21%, gap=+38.64, verdict=UNDER_CONFIDENT
- **nan**: n=17, predicted=50.0%, directional=41.18%, T1=0.00%, gap=-8.82, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium**: n=17, predicted=55.0%, directional=64.71%, T1=100.00%, gap=+9.71, verdict=WELL_CALIBRATED_DIRECTIONAL
- **Medium-High**: n=11, predicted=67.5%, directional=72.73%, T1=100.00%, gap=+5.23, verdict=WELL_CALIBRATED_DIRECTIONAL

## Score Buckets
- **score_10_19**: n=4, predicted=14.5%, directional=50.00%, T1=0.00%, gap=+35.50, verdict=LOW_SAMPLE
- **score_20_29**: n=9, predicted=24.5%, directional=55.56%, T1=0.00%, gap=+31.06, verdict=LOW_SAMPLE
- **score_30_39**: n=22, predicted=34.5%, directional=59.09%, T1=0.00%, gap=+24.59, verdict=UNDER_CONFIDENT
- **score_40_49**: n=10, predicted=44.5%, directional=50.00%, T1=50.00%, gap=+5.50, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_50_59**: n=9, predicted=54.5%, directional=77.78%, T1=77.78%, gap=+23.28, verdict=LOW_SAMPLE
- **score_60_69**: n=13, predicted=64.5%, directional=53.85%, T1=92.31%, gap=-10.65, verdict=OVER_CONFIDENT
- **score_70_79**: n=11, predicted=74.5%, directional=72.73%, T1=100.00%, gap=-1.77, verdict=WELL_CALIBRATED_DIRECTIONAL