# Freakto Market Replay Report v10.0.0

- Run ID: `market_replay_20260710_153110`
- Started UTC: `2026-07-10T15:31:10.222167+00:00`
- Finished UTC: `2026-07-10T15:31:55.827120+00:00`
- Status: `REPLAY_RESEARCH_NOT_VALIDATED`
- Replay mode: `REPLAY_SAFE_TECHNICAL_CORE`
- Leakage audit: `PASSED_NO_LOOKAHEAD`

## Summary

- Rows: 6451
- Complete rows: 6451
- Directional rows: 2527
- Evaluation horizon: 1d (6 candles)
- Horizon win rate: 40.92%
- Avg gross: 0.0375%
- Avg net: -0.2625%
- Profit factor: 0.746

## Chronological splits

- **TRAIN_60**: rows=3870, directional=1526, win24=39.84%, avg_net24=-0.274316%, profit_factor=0.7462
- **TEST_20**: rows=1291, directional=523, win24=40.92%, avg_net24=-0.410723%, profit_factor=0.6276
- **VALIDATION_20**: rows=1290, directional=478, win24=44.35%, avg_net24=-0.062823%, profit_factor=0.9221

## Blockers

- میانگین Net Return در Test split مثبت نیست.

## Safety

- Market Replay نتیجه Backtest است و جای Forward/Paper را نمی‌گیرد.
- نسخه v10 به‌صورت پیش‌فرض Technical/Regime core را Replay می‌کند؛ خبر تاریخی فقط با context_file زمان‌دار وارد می‌شود.
- در کندلی که Stop و Target همزمان لمس شوند، ترتیب محافظه‌کارانه Stop-first ثبت می‌شود.
- هرگونه تنظیم وزن باید فقط با Validation/Test split و سپس Forward انجام شود.
