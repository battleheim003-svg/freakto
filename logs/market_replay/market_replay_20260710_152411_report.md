# Freakto Market Replay Report v10.0.0

- Run ID: `market_replay_20260710_152411`
- Started UTC: `2026-07-10T15:24:11.500739+00:00`
- Finished UTC: `2026-07-10T15:30:34.837929+00:00`
- Status: `REPLAY_RESEARCH_NOT_VALIDATED`
- Replay mode: `REPLAY_SAFE_TECHNICAL_CORE`
- Leakage audit: `PASSED_NO_LOOKAHEAD`

## Summary

- Rows: 38706
- Complete rows: 38706
- Directional rows: 14191
- Evaluation horizon: 1d (6 candles)
- Horizon win rate: 42.56%
- Avg gross: 0.1499%
- Avg net: -0.1501%
- Profit factor: 0.8875

## Chronological splits

- **TRAIN_60**: rows=23220, directional=8248, win24=42.02%, avg_net24=-0.098209%, profit_factor=0.9268
- **TEST_20**: rows=7746, directional=3086, win24=41.35%, avg_net24=-0.395914%, profit_factor=0.6951
- **VALIDATION_20**: rows=7740, directional=2857, win24=45.4%, avg_net24=-0.03443%, profit_factor=0.9745

## Blockers

- میانگین Net Return در Test split مثبت نیست.

## Safety

- Market Replay نتیجه Backtest است و جای Forward/Paper را نمی‌گیرد.
- نسخه v10 به‌صورت پیش‌فرض Technical/Regime core را Replay می‌کند؛ خبر تاریخی فقط با context_file زمان‌دار وارد می‌شود.
- در کندلی که Stop و Target همزمان لمس شوند، ترتیب محافظه‌کارانه Stop-first ثبت می‌شود.
- هرگونه تنظیم وزن باید فقط با Validation/Test split و سپس Forward انجام شود.
