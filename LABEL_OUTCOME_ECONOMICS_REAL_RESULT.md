# Freakto Label & Outcome Economics — Real Replay Result

## Dataset

- Replay source: `logs/market_replay/market_replay_evaluations.csv`
- Selected independent run: `market_replay_20260711_192507`
- Rows loaded: `78,452`
- Directional complete rows used: `14,174`
- Older replay runs ignored: `3`
- Mode: `RESEARCH_AUDIT_ONLY`

## Final status

```text
Status                  : COMPLETE_NO_POLICY_CHANGE
Canonical policy        : FIXED_CLOSE_6C_NET
Recommended replacement : None
Policy change applied   : False
Paper/Live enabled      : False
```

No alternative label or exit policy preserved positive, sufficiently sampled and chronologically stable net edge.

## Fixed-close horizon comparison

| Horizon | Coverage | Gross expectancy | Net expectancy | Net win rate | Net PF |
|---:|---:|---:|---:|---:|---:|
| 1 candle | 100.00% | +0.045424% | -0.543044% | 25.98% | 0.356940 |
| 3 candles | 100.00% | +0.095349% | -0.493119% | 34.46% | 0.575613 |
| 6 candles | 100.00% | +0.150099% | -0.438369% | 38.65% | 0.708966 |
| 12 candles | 91.32% | +0.300295% | -0.289699% | 42.43% | 0.852142 |
| Adaptive | 100.00% | +0.267854% | -0.320614% | 41.54% | 0.831514 |

The gross signal was mildly positive at every available horizon, but the average execution-cost drag of about `0.588468%` converted each all-directional policy into a negative net result.

## First-touch Target-1/Stop comparison

| Policy | n | Win rate | Expectancy | PF |
|---|---:|---:|---:|---:|
| 6C Stop-first | 14,174 | 51.04% | -0.534581% | 0.537436 |
| 6C Target-first bound | 14,174 | 51.99% | -0.496360% | 0.560498 |
| 12C Stop-first | 14,011 | 55.63% | -0.518273% | 0.572366 |
| 12C Target-first bound | 14,011 | 56.61% | -0.479304% | 0.595556 |

First-touch increased the observed win rate, but worsened expectancy compared with fixed-close labels. The payoff geometry explains why.

## Planned trade economics

All-directional mean values:

```text
Round-trip execution cost : 0.588468%
Target-1 gross reward     : 1.870319%
Target-1 net reward       : 1.281851%
Stop gross loss           : 2.245213%
Stop net loss             : 2.833681%
Gross reward/risk         : 0.834454
Net reward/risk           : 0.424390
Net break-even win rate   : 70.57%
```

The mean Target-1 win after costs earns only about `0.424` units for every unit lost at Stop. A first-touch system therefore requires an average win rate around `70.57%`, materially above the observed 12-candle first-touch win rate.

## Label consistency and path dependence

```text
Recorded win vs canonical net-sign mismatches : 0
Outcome label vs canonical net-sign mismatches : 0
Target-1 hit but canonical net loss            : 3,800 (26.81%)
Stop hit but canonical net win                 : 1,126 (7.94%)
Target-1 and Stop both touched                 : 3,547 (25.02%)
Same-candle Stop/Target ambiguity              : 137 (0.97%)
```

The recorder's canonical WIN/LOSS label is internally consistent. The problem is not a sign-label bug. A Target hit must not be treated as equivalent to a profitable outcome because both levels can be touched and the fixed-horizon close can still be negative.

## Intrabar ambiguity sensitivity

At the 12-candle first-touch horizon:

```text
Stop-first expectancy        : -0.518273%
Target-first expectancy      : -0.479304%
Overall sensitivity          : +0.038968 percentage points
Ambiguous-trade mean spread  : 3.985300 percentage points
```

Same-candle ambiguity matters for individual trades, but affects fewer than 1% of rows and cannot explain the system-wide negative edge.

## Side-specific finding

`LONG + FIXED_CLOSE_12C_NET` was approximately break-even:

```text
Samples       : 6,821
Expectancy    : +0.011982%
Profit factor : 1.006493
Positive folds: 2 / 4
```

It was positive in the first two chronological folds and negative in the final two. This is temporally unstable and does not satisfy the minimum PF, stability or promotion criteria.

SHORT remained negative at every tested fixed horizon; its 12-candle net expectancy was `-0.625770%` with PF `0.700068`.

## Conclusion

The negative result is not primarily caused by the six-candle label or by same-candle Target/Stop ordering. The main causes are:

1. execution costs larger than the gross edge;
2. weak planned Target-1/Stop payoff geometry after costs;
3. SHORT underperformance;
4. temporal deterioration of the isolated LONG 12-candle result.

Changing the canonical label would conceal rather than solve these problems. Canonical labels, score weights, Paper and Live settings remain unchanged.
