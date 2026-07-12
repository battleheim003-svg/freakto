# Freakto Market Replay Report v10.3.0

- Run ID: `market_replay_20260712_182537`
- Started UTC: `2026-07-12T18:25:37.961989+00:00`
- Finished UTC: `2026-07-12T18:28:12.310621+00:00`
- Status: `REPLAY_RESEARCH_NOT_VALIDATED`
- Replay mode: `REPLAY_SAFE_TECHNICAL_CORE`
- Leakage audit: `PASSED_NO_LOOKAHEAD`

## Summary

- Rows: 19335
- Complete rows: 19335
- Directional rows: 7134
- Evaluation horizon: 1d (6 candles)
- Horizon win rate: 39.28%
- Avg gross: 0.1268%
- Avg net: -0.4575%
- Profit factor: 0.6887

## Chronological splits

- **TRAIN_60**: rows=11601, directional=4216, win24=38.64%, avg_net24=-0.440171%, profit_factor=0.7033
- **VALIDATION_20**: rows=3867, directional=1425, win24=42.04%, avg_net24=-0.276468%, profit_factor=0.807
- **TEST_20**: rows=3867, directional=1493, win24=38.45%, avg_net24=-0.679229%, profit_factor=0.5371

## Blockers

- میانگین Net Return در Test split مثبت نیست.

## Safety

- Market Replay نتیجه Backtest است و جای Forward/Paper را نمی‌گیرد.
- نسخه v10 به‌صورت پیش‌فرض Technical/Regime core را Replay می‌کند؛ خبر تاریخی فقط با context_file زمان‌دار وارد می‌شود.
- در کندلی که Stop و Target همزمان لمس شوند، ترتیب محافظه‌کارانه Stop-first ثبت می‌شود.
- هرگونه تنظیم وزن باید فقط با Validation/Test split و سپس Forward انجام شود.
