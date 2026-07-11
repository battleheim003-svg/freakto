# Freakto Market Replay Report v10.3.0

- Run ID: `market_replay_20260711_192507`
- Started UTC: `2026-07-11T19:25:07.720224+00:00`
- Finished UTC: `2026-07-11T19:35:39.860718+00:00`
- Status: `REPLAY_RESEARCH_NOT_VALIDATED`
- Replay mode: `REPLAY_SAFE_TECHNICAL_CORE`
- Leakage audit: `PASSED_NO_LOOKAHEAD`

## Summary

- Rows: 38670
- Complete rows: 38670
- Directional rows: 14174
- Evaluation horizon: 1d (6 candles)
- Horizon win rate: 38.65%
- Avg gross: 0.1501%
- Avg net: -0.4384%
- Profit factor: 0.709

## Chronological splits

- **TRAIN_60**: rows=23202, directional=8236, win24=38.08%, avg_net24=-0.395283%, profit_factor=0.7401
- **VALIDATION_20**: rows=7734, directional=2864, win24=40.96%, avg_net24=-0.323387%, profit_factor=0.7864
- **TEST_20**: rows=7734, directional=3074, win24=38.03%, avg_net24=-0.660934%, profit_factor=0.5469

## Blockers

- میانگین Net Return در Test split مثبت نیست.

## Safety

- Market Replay نتیجه Backtest است و جای Forward/Paper را نمی‌گیرد.
- نسخه v10 به‌صورت پیش‌فرض Technical/Regime core را Replay می‌کند؛ خبر تاریخی فقط با context_file زمان‌دار وارد می‌شود.
- در کندلی که Stop و Target همزمان لمس شوند، ترتیب محافظه‌کارانه Stop-first ثبت می‌شود.
- هرگونه تنظیم وزن باید فقط با Validation/Test split و سپس Forward انجام شود.
