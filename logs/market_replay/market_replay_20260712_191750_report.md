# Freakto Market Replay Report v10.3.0

- Run ID: `market_replay_20260712_191750`
- Started UTC: `2026-07-12T19:17:50.420828+00:00`
- Finished UTC: `2026-07-12T19:21:10.030500+00:00`
- Status: `REPLAY_RESEARCH_NOT_VALIDATED`
- Replay mode: `REPLAY_SAFE_TECHNICAL_CORE`
- Leakage audit: `PASSED_NO_LOOKAHEAD`

## Summary

- Rows: 19374
- Complete rows: 19374
- Directional rows: 7144
- Evaluation horizon: 1d (6 candles)
- Horizon win rate: 39.24%
- Avg gross: 0.1250%
- Avg net: -0.4592%
- Profit factor: 0.6876

## Chronological splits

- **TRAIN_60**: rows=11622, directional=4227, win24=38.61%, avg_net24=-0.440435%, profit_factor=0.7027
- **VALIDATION_20**: rows=3876, directional=1426, win24=41.87%, avg_net24=-0.291866%, profit_factor=0.798
- **TEST_20**: rows=3876, directional=1491, win24=38.5%, avg_net24=-0.672618%, profit_factor=0.54

## Blockers

- میانگین Net Return در Test split مثبت نیست.

## Safety

- Market Replay نتیجه Backtest است و جای Forward/Paper را نمی‌گیرد.
- نسخه v10 به‌صورت پیش‌فرض Technical/Regime core را Replay می‌کند؛ خبر تاریخی فقط با context_file زمان‌دار وارد می‌شود.
- در کندلی که Stop و Target همزمان لمس شوند، ترتیب محافظه‌کارانه Stop-first ثبت می‌شود.
- هرگونه تنظیم وزن باید فقط با Validation/Test split و سپس Forward انجام شود.
