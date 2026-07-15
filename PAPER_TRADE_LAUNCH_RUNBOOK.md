# Freakto Paper Trade Launch Suite v2

## Purpose

This suite completes the engineering path to safe paper trading while preserving the statistical blockers discovered in Research.

It has two separate modes:

1. `RESEARCH` — observation-only paper collection. Virtual capital allocation is always zero. This mode is intended to validate signal flow, event detection, execution assumptions, duplicate handling and evaluation operations.
2. `STRATEGY` — paper validation of a frozen deterministic event policy. This remains blocked until Development stability and untouched Fresh OOS requirements pass.

No file in this suite can send a real exchange order.

## Current expected status

Based on the latest results:

- Event rows: 3,589
- Cost-gated rows: 816
- Meta Holdout samples: 45
- Meta walk-forward positive fraction: 50%
- Fresh OOS: still accumulating

The expected initial result is:

```text
READY_FOR_RESEARCH_PAPER_COLLECTION
Strategy paper ready: False
Live orders enabled: False
```

## Install and test

```bat
.venv\Scripts\activate
python -m pytest
```

The package adds 11 tests, so a project with 208 tests should collect approximately 219 tests.

## Refresh research artifacts

```bat
python -X utf8 cost_gate_diagnostics_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/cost_gate_diagnostics --cutoff 2026-07-09T12:00:00Z

python -X utf8 event_opportunity_v2_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/event_opportunity_v2 --cutoff 2026-07-09T12:00:00Z --horizon 6
```

## Consolidated preflight

```bat
python -X utf8 paper_trade_launch_dashboard.py --preflight
```

The preflight evaluates:

- Event Universe availability
- Cost-gate diagnostics availability
- Minimum Event and Cost-gated sample counts
- Deterministic candidate Holdout performance
- Fixed-policy chronological walk-forward stability
- Fresh OOS sample count and economics
- Live-order hard disablement

## Start research paper collection

Research mode does not claim that the strategy has a validated edge. It records zero-allocation virtual observations only.

```bat
python -X utf8 paper_trade_launch_dashboard.py --arm-research
```

After each closed 4h candle:

```bat
python -X utf8 monitor.py --once
python -X utf8 paper_trade_launch_dashboard.py --scan --decision-file logs/decisions.csv
python -X utf8 paper_trade_launch_dashboard.py --evaluate
python -X utf8 paper_trade_launch_dashboard.py --status
```

The scanner applies:

- causal Event detection from decision-time fields only;
- robust Entry/Stop/Target parsing;
- fixed Cost Gate;
- stale-signal rejection;
- duplicate rejection;
- maximum open trades;
- maximum open trades per Symbol;
- maximum total virtual risk;
- zero real-capital allocation.

## Strategy paper mode

This command remains fail-closed until all Development and Fresh OOS gates pass:

```bat
python -X utf8 paper_trade_launch_dashboard.py --arm-strategy
```

The default strategy requirements include:

- deterministic Holdout samples >= 100;
- positive Holdout expectancy;
- Holdout profit factor >= 1.05;
- Holdout bootstrap CI lower bound > 0;
- at least three valid chronological folds;
- at least two-thirds positive walk-forward folds;
- Fresh OOS directional rows >= 300;
- Fresh selected samples >= 50;
- positive Fresh OOS expectancy and PF >= 1.

No threshold is selected on Fresh OOS.

## Disarm

```bat
python -X utf8 paper_trade_launch_dashboard.py --disarm
```

## Output files

```text
logs/paper_launch_v2/paper_launch_readiness.json
logs/paper_launch_v2/paper_launch_readiness.md
logs/paper_launch_v2/deterministic_candidate_assessments.csv
logs/paper_launch_v2/deterministic_candidate_walk_forward.csv
logs/paper_launch_v2/arm_state.json
logs/paper_launch_v2/paper_observation_last_run.json
logs/paper_trades.csv
logs/paper_trade_evaluations.csv
```

## Safety contract

- No exchange order API is imported or invoked.
- `allocation_pct` is zero in Research mode.
- Real capital and live orders are hard-coded disabled.
- Arming is explicit and reversible.
- Readiness is recalculated before each scan.
- A Strategy arm is rejected if readiness later regresses.
- Paper results never authorize Live trading automatically.
