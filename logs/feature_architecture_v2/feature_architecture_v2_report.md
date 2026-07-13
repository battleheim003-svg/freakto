# Freakto Feature Architecture v2 & Baseline Benchmark Suite

- Status: `COMPLETE_NO_DEVELOPMENT_CANDIDATE`
- Mode: `BASELINE_BENCHMARK_DEVELOPMENT_ONLY`
- Replay window: `FULL`
- Rows loaded/usable: `48535 / 16150`
- Development candidate: `None`
- Promotion applied: `False`
- Paper/Live enabled: `False`

## Safety contract

Aggregate score is not a model input. Structure is a gate. LONG and SHORT are fitted independently. No result in this report authorizes runtime promotion; untouched Fresh OOS and Forward/Paper confirmation are mandatory.

## Key findings
- Best architecture Holdout variant was ARCH_V2_BASE with n=171, expectancy=-0.254832% and PF=0.799966.
- Best simple Holdout baseline was CHAMPION_SCORE_GE_70 with expectancy=-0.257805% and PF=0.824675.
- Aggregate score was excluded from Feature Architecture v2 model inputs; LONG and SHORT models were fitted independently.
- Structure was used as an entry gate rather than an additive score; Momentum was capped or removed in declared variants.

## Blockers
- No Feature Architecture v2 variant beat simple baselines with positive, confidence-supported, walk-forward-stable Holdout edge.

## Warnings
- All model and baseline results are development diagnostics only; Fresh OOS remains untouched.
