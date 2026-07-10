# Freakto Market Replay Report v10.0.0

- Run ID: `market_replay_20260710_152233`
- Started UTC: `2026-07-10T15:22:33.765238+00:00`
- Finished UTC: `2026-07-10T15:22:42.375690+00:00`
- Status: `REPLAY_RESEARCH_NOT_VALIDATED`
- Replay mode: `REPLAY_SAFE_TECHNICAL_CORE`
- Leakage audit: `PASSED_NO_LOOKAHEAD`

## Summary

- Rows: 1076
- Complete rows: 1076
- Directional rows: 555
- Evaluation horizon: 1d (6 candles)
- Horizon win rate: 41.26%
- Avg gross: 0.0712%
- Avg net: -0.2288%
- Profit factor: 0.7726

## Chronological splits

- **TRAIN_60**: rows=645, directional=332, win24=39.76%, avg_net24=-0.256855%, profit_factor=0.7533
- **TEST_20**: rows=216, directional=115, win24=36.52%, avg_net24=-0.371505%, profit_factor=0.6612
- **VALIDATION_20**: rows=215, directional=108, win24=50.93%, avg_net24=0.009501%, profit_factor=1.0118

## Blockers

- میانگین Net Return در Test split مثبت نیست.

## Safety

- Market Replay نتیجه Backtest است و جای Forward/Paper را نمی‌گیرد.
- نسخه v10 به‌صورت پیش‌فرض Technical/Regime core را Replay می‌کند؛ خبر تاریخی فقط با context_file زمان‌دار وارد می‌شود.
- در کندلی که Stop و Target همزمان لمس شوند، ترتیب محافظه‌کارانه Stop-first ثبت می‌شود.
- هرگونه تنظیم وزن باید فقط با Validation/Test split و سپس Forward انجام شود.
