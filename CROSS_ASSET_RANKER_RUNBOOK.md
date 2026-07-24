# Cross-Asset Opportunity Ranker Runbook

Status: research-only, activation blocked
Decision Engine output: none
Paper/Live integration: none
Core changes: none

## Activation prerequisite

At least two asset classes must independently provide:

- `data_quality_status=PASSED`;
- `calibration_status=VALIDATED`;
- a named calibration version;
- at least the configured calibration sample count;
- calibrated success probability, expected gross return, expected cost, and
  confidence measured on causally separated data.

Forex and gold currently remain `RESEARCH_DATA_ONLY`, so this prerequisite is
not yet met with real project data.

## Ranking contract

The input CSV requires:

```text
period_utc,symbol,asset_class,side,raw_score,calibrated_probability,confidence,expected_gross_return_bps,expected_cost_bps,calibration_status,calibration_version,calibration_samples,data_quality_status
```

The ranker compares expected net return discounted by confidence. Calibrated
probability is a minimum gate and tie-breaker; it is not converted to a
fabricated return estimate. If the top eligible row has non-positive expected
net return or inadequate probability, the period explicitly returns
`NO_SELECTION`.

```text
python -X utf8 cross_asset_opportunity_ranker.py rank --input <standardized.csv> --output <report.json> --rankings-csv <rankings.csv>
```

## Historical wrapper

Evaluation requires outcomes observed strictly after the ranking period. It
compares the research selection with an equal-weight benchmark of every
eligible ranked opportunity in the same period.

```text
python -X utf8 cross_asset_opportunity_ranker.py evaluate --rankings <rankings.csv> --outcomes <outcomes.csv>
```

`PASSED` means only that the configured completed-period sample exists. It is
not a profitability, Paper, or Live approval.

## Forward ledger

`CrossAssetForwardTracker` stores ranking observations and later realized
outcomes append-only in a separate SQLite database. It rejects outcomes without
a prior ranking, outcomes observed at or before the ranking period, negative
costs, and missing evidence references.
