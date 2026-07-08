# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-08T17:15:39.271982+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 42
- Overall Directional Win: 76.19%
- Overall Target 1 Hit: 57.14%
- Mean Calibration Error: 29.17 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 42/100

## Confidence Label Buckets
- **Low**: n=19, predicted=25.0%, directional=68.42%, T1=15.79%, gap=+43.42, verdict=UNDER_CONFIDENT
- **Medium**: n=15, predicted=55.0%, directional=73.33%, T1=86.67%, gap=+18.33, verdict=UNDER_CONFIDENT
- **Medium-High**: n=8, predicted=67.5%, directional=100.00%, T1=100.00%, gap=+32.50, verdict=LOW_SAMPLE

## Score Buckets
- **score_10_19**: n=3, predicted=14.5%, directional=66.67%, T1=0.00%, gap=+52.17, verdict=LOW_SAMPLE
- **score_20_29**: n=1, predicted=24.5%, directional=0.00%, T1=0.00%, gap=-24.50, verdict=LOW_SAMPLE
- **score_30_39**: n=11, predicted=34.5%, directional=72.73%, T1=0.00%, gap=+38.23, verdict=UNDER_CONFIDENT
- **score_40_49**: n=2, predicted=44.5%, directional=50.00%, T1=50.00%, gap=+5.50, verdict=LOW_SAMPLE
- **score_50_59**: n=7, predicted=54.5%, directional=85.71%, T1=100.00%, gap=+31.21, verdict=LOW_SAMPLE
- **score_60_69**: n=10, predicted=64.5%, directional=70.00%, T1=80.00%, gap=+5.50, verdict=WELL_CALIBRATED_DIRECTIONAL
- **score_70_79**: n=8, predicted=74.5%, directional=100.00%, T1=100.00%, gap=+25.50, verdict=LOW_SAMPLE