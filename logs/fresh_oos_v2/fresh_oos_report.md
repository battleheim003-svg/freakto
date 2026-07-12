# Freakto Fresh OOS Replay & Feature Store v2

- Status: `READY_AWAITING_FRESH_DATA`
- Mode: `FRESH_OOS_FIXED_BENCHMARK_ONLY`
- Development dataset: `7eb70bc7f68045dfa5a7`
- Development cutoff: `2026-07-09T12:00:00+00:00`
- Fresh rows: `0`
- Fresh directional rows: `0`
- Fixed score threshold: `70.0`
- Promotion applied: `False`
- Paper/Live enabled: `False`

## Fixed benchmark

- Samples: `0`
- Expectancy: `0.000000%`
- Profit factor: `0.0`
- Positive folds: `0/4`

## Blockers
- fresh directional sample count 0 is below required 300

## Warnings
- BTC/USDT has only 0 fresh directional rows
- ETH/USDT has only 0 fresh directional rows
- SOL/USDT has only 0 fresh directional rows
- missing requested symbol/timeframe pairs: ['BTC/USDT|4h', 'ETH/USDT|4h', 'SOL/USDT|4h']

## Safety

The fresh dataset is never used for threshold or weight selection. This pipeline is research-only and does not enable Paper or Live trading.
