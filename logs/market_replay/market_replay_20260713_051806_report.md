# Freakto Market Replay Report v10.3.0

- Run ID: `market_replay_20260713_051806`
- Started UTC: `2026-07-13T05:18:06.945582+00:00`
- Finished UTC: `2026-07-13T05:20:57.049093+00:00`
- Status: `REPLAY_RESEARCH_NOT_VALIDATED`
- Replay mode: `REPLAY_SAFE_TECHNICAL_CORE`
- Leakage audit: `PASSED_NO_LOOKAHEAD`

## Summary

- Rows: 19383
- Complete rows: 19383
- Directional rows: 7148
- Evaluation horizon: 1d (6 candles)
- Horizon win rate: 39.23%
- Avg gross: 0.1250%
- Avg net: -0.4593%
- Profit factor: 0.6875

## Chronological splits

- **TRAIN_60**: rows=11628, directional=4230, win24=38.58%, avg_net24=-0.443042%, profit_factor=0.7014
- **TEST_20**: rows=3879, directional=1492, win24=38.54%, avg_net24=-0.66807%, profit_factor=0.5416
- **VALIDATION_20**: rows=3876, directional=1426, win24=41.87%, avg_net24=-0.288992%, profit_factor=0.7996

## Blockers

- میانگین Net Return در Test split مثبت نیست.

## Safety

- Market Replay نتیجه Backtest است و جای Forward/Paper را نمی‌گیرد.
- نسخه v10 به‌صورت پیش‌فرض Technical/Regime core را Replay می‌کند؛ خبر تاریخی فقط با context_file زمان‌دار وارد می‌شود.
- در کندلی که Stop و Target همزمان لمس شوند، ترتیب محافظه‌کارانه Stop-first ثبت می‌شود.
- هرگونه تنظیم وزن باید فقط با Validation/Test split و سپس Forward انجام شود.
