# Multi-Cycle Feature Decay & Regime Drift — Implementation Result

## Status

```text
IMPLEMENTATION_COMPLETE
RESEARCH_DIAGNOSTIC_ONLY
PROMOTION_APPLIED = False
PAPER_LIVE_ENABLED = False
```

## Validation completed in the build environment

```text
New tests                         : 16 passed
Related multi-cycle test suite    : 37 passed
Python compile                    : passed
Synthetic end-to-end integration : passed
```

The synthetic integration used 9,000 directional decisions across 2018–2026,
three symbols, two sides, and four regimes. It confirmed that the analyzer can:

- select FULL instead of double-counting nested windows;
- create `LEGACY`, `TRANSITION`, and `RECENT` eras;
- identify a component that becomes harmful recently;
- align `risk_penalty` in the intended inverse direction;
- identify severe component distribution drift;
- classify decayed regime/side cells;
- produce all CSV, JSON, and Markdown artifacts;
- remain `COMPLETE_NO_PROMOTION` with Paper/Live disabled.

## Real-data execution

The build environment does not contain the user's local generated files under:

```text
logs/multi_cycle_archive_v2/replays/
```

Therefore no real Freakto feature-decay claims are made in this document. The
real results are produced locally with:

```bat
python -X utf8 multi_cycle_feature_decay_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/multi_cycle_feature_decay --cutoff 2026-07-09T12:00:00Z
```

The local Markdown and JSON reports are the source of truth for actual Feature,
Regime, Side, and Symbol findings.

## Important methodological correction

The nested `3Y`, `5Y`, and `FULL` archives are not independent samples. Treating
them as separate confirmations would overstate evidence. The implementation
uses non-overlapping eras from FULL for primary inference and labels the nested
window output as a cross-check only.

## Files added

```text
engine/multi_cycle_feature_decay.py
engine/regime_drift.py
multi_cycle_feature_decay_analysis.py
tests/test_multi_cycle_feature_decay.py
tests/test_regime_drift.py
MULTI_CYCLE_FEATURE_DECAY_RUNBOOK.md
MULTI_CYCLE_FEATURE_DECAY_IMPLEMENTATION_RESULT.md
CHANGED_FILES.txt
```
