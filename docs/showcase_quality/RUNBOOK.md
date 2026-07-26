# Showcase Quality & Win-rate Runbook

## Safety boundary

This feature is an isolated Research/Showcase layer. It does not modify the
Decision Engine, the main Market Replay, the main Backtest, or
`decision_evaluator.py`. Its trades remain `official_evidence_eligible=false`
and cannot enable live orders or real capital.

## What changed

### Independent quality profiles

- `WIN_RATE` (dashboard default): rejects low-quality recommendation classes,
  requires positive cost-adjusted economics, limits concurrent positions to
  four, and applies rolling symbol/side and side-level outcome gates.
- `BALANCED`: moderate quality filters and up to seven concurrent positions.
- `VOLUME`: preserves exploratory high-volume behaviour for data collection;
  it is not intended as the quality benchmark.

Risk tolerance and technical-analysis depth remain independent. For a quality
test, use technical depth `100`, quality `WIN_RATE`, and risk tolerance `20-35`.
The dashboard marks any other combination as not aligned with this runbook;
that warning is descriptive and never enables Live execution.

### Technical participation and breadth

- `technical_confluence_pct` is the dominant directional vote divided by the
  complete indicator set, including neutral indicators. It therefore measures
  actual participation instead of silently dropping abstentions.
- `directional_agreement_pct` is reported separately and divides the dominant
  vote only by directional votes.
- At least half of the configured indicators must cast a directional vote.
  Ties and insufficient breadth become `NEUTRAL`/`MONITOR` and are rejected by
  the `WIN_RATE` and `BALANCED` quality profiles.
- The active TechnicalV2 adapter keeps its ATR-derived entry/stop/target
  geometry. The isolated legacy Showcase technical path now uses profile-based
  ATR geometry when ATR is valid and falls back safely when it is not.

### Causal outcome gate

The outcome gate uses only trades closed before the candidate decision. Manual
`SESSION_STOP` exits are excluded from learning. A symbol/side bucket is not
quarantined until it has the configured minimum sample, and a healthy mature
symbol/side bucket can override a weak global side. Diagnostics include sample
count, win rate, 90% Wilson lower bound, Profit Factor, and net Paper PnL.

### Replay execution correctness

- `AUTO` chooses the finest complete local dataset in this order: `15m`, `1h`,
  then `4h`. The current repository falls back to `4h` until finer crypto cache
  files are available.
- Replay Stop/Target checks use the next bar's OHLC range rather than Close
  only. If both barriers occur in one bar, STOP-first is used conservatively.
- Barrier fills occur at the barrier, or at the bar open for a gap, rather than
  at a later Close that can exaggerate slippage.
- Technical market regime is preserved instead of being overwritten by the
  execution-source label.

### Exit protection

- Break-even arms only after a completed post-entry bar reaches `0.75R`; the
  updated stop becomes effective from the following bar and includes modeled
  round-trip fees.
- Every fresh trade records maximum favourable excursion (`mfe_r`). Break-even
  calibration stays at `0.75R` until at least 50 losing trades have MFE data;
  after that threshold the dashboard reports a review candidate but never
  changes the setting automatically.
- A strong, sufficiently confident opposite signal closes the Paper position
  with `SIGNAL_INVALIDATED`.
- Geometry `expiry_bars` controls Replay time exits; wall-clock holding time is
  retained only for public live-data Showcase sessions.

## Dashboard interpretation

`سلامت عملکرد جلسه` reports strategy exits only:

- Win rate
- Profit Factor
- expectancy per trade
- break-even Win rate implied by average win/loss
- causal Quality Gate comparison

The comparison is Research-only and is not a profitability claim. Promotion
requires both positive expectancy and Profit Factor above 1 on unseen forward
samples; improving Win rate alone is insufficient.

The dashboard also shows session maturity (organic exits toward 50), separate
LONG/SHORT gate maturity, and MFE calibration maturity. Historical records
created before MFE instrumentation do not count toward the MFE sample.

For a read-only causal walk-forward report across multiple profiles:

```powershell
.\.venv\Scripts\python.exe -m freakto.showcase_paper.performance_cli `
  --session logs\showcase_paper\session.json `
  --profiles BALANCED WIN_RATE
```

The report preserves chronological order, excludes manual `SESSION_STOP`
learning exits, and segments rejection reasons by symbol and side.

## Operating sequence

1. Stop any worker started before this feature was installed.
2. Refresh the dashboard once.
3. Open `فرآیندها -> اعتبارسنجی و Paper`.
4. Select quality `تمرکز بر Win rate`, analysis depth `100`, risk `20-35`.
5. Keep Replay timeframe on `AUTO`.
6. Start a fresh Showcase session and collect at least 50 organic exits.
7. Review Win rate, PF, expectancy, rejected symbol/side buckets, LONG/SHORT
   maturity, and losing-trade MFE.
8. Compare against `VOLUME` only through causal walk-forward and forward Paper
   reports; do not compare cherry-picked screenshots.

## Fail-closed rules

- `PF <= 1` or negative expectancy: keep Research-only.
- Too few samples: keep collecting; do not loosen the gate to manufacture wins.
- Calibration `NEEDS_REVIEW`: confidence is descriptive, not a promotion gate.
- Missing finer Replay data: dashboard reports the actual fallback timeframe.
