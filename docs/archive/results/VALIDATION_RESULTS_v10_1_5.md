# Freakto v10.1.5 — Validation Result on the supplied Replay ledger

Dataset:

- Total replay rows: **39,782**
- Directional rows recorded: **14,746**
- Neutral rows: **25,036**
- Complete rows: **39,782**
- Primary horizon: **6 candles = 1 day on 4h timeframe**
- Gross source: `gross_signed_return_after_6c_pct`
- Net source: `net_signed_return_after_6c_pct`
- Backfill result: `CANONICAL_METRICS_RECORDED`

## Threshold results on chronological Test split

| Threshold | Test samples | Win rate | Avg net return | Profit factor | Verdict |
|---:|---:|---:|---:|---:|---|
| 40 | 3,201 | 41.17% | -0.395037% | 0.6941 | Reject: Test net non-positive |
| 50 | 3,201 | 41.17% | -0.395037% | 0.6941 | Reject: Test net non-positive |
| 60 | 1,685 | 39.11% | -0.488325% | 0.6384 | Reject: Test net non-positive |
| 70 | 681 | 36.12% | -0.546091% | 0.5950 | Overfit: Train positive / Test negative |
| 80 | 174 | 29.89% | -0.739765% | 0.4790 | Reject: Test net non-positive |
| 90 | 7 | 42.86% | +0.924178% | 2.1719 | Low Test sample |

## Conclusion

No robust Threshold candidate passed both Validation and Test with sufficient sample. Score >= 90 is positive in Test, but only has 7 Test samples and cannot be promoted. No Decision Engine, Paper, or Live settings should be changed from this result.
