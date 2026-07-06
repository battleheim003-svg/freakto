# Freakto Confidence Calibration Engine v5.0

Created UTC: 2026-07-06T13:25:55.905765+00:00

- Quality: **CALIBRATION_WEAK**
- Samples: 30
- Overall Directional Win: 70.00%
- Overall Target 1 Hit: 76.67%
- Mean Calibration Error: 24.97 pts

## Blockers
- Confidence داخلی با outcome واقعی فاصله زیادی دارد.
- برای استفاده عملی، حداقل 100 ارزیابی لازم است: 30/100

## Confidence Label Buckets
- **Low**: n=9, predicted=25.0%, directional=22.22%, T1=22.22%, gap=-2.78, verdict=LOW_SAMPLE
- **Medium**: n=13, predicted=55.0%, directional=84.62%, T1=100.00%, gap=+29.62, verdict=UNDER_CONFIDENT
- **Medium-High**: n=8, predicted=67.5%, directional=100.00%, T1=100.00%, gap=+32.50, verdict=LOW_SAMPLE

## Score Buckets
- **score_10_19**: n=1, predicted=14.5%, directional=0.00%, T1=0.00%, gap=-14.50, verdict=LOW_SAMPLE
- **score_30_39**: n=6, predicted=34.5%, directional=0.00%, T1=0.00%, gap=-34.50, verdict=LOW_SAMPLE
- **score_50_59**: n=7, predicted=54.5%, directional=85.71%, T1=100.00%, gap=+31.21, verdict=LOW_SAMPLE
- **score_60_69**: n=8, predicted=64.5%, directional=87.50%, T1=100.00%, gap=+23.00, verdict=LOW_SAMPLE
- **score_70_79**: n=8, predicted=74.5%, directional=100.00%, T1=100.00%, gap=+25.50, verdict=LOW_SAMPLE