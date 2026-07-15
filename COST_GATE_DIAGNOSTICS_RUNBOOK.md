# Cost Gate Diagnostics & Geometry Parser Fix

Run:

```bat
python -m pytest
python -X utf8 cost_gate_diagnostics_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/cost_gate_diagnostics --cutoff 2026-07-09T12:00:00Z
python -X utf8 event_opportunity_v2_analysis.py --replay-root logs/multi_cycle_archive_v2 --output-dir logs/event_opportunity_v2 --cutoff 2026-07-09T12:00:00Z --horizon 6
```

The parser accepts numbers, JSON/Python lists and mappings, and textual ranges. The diagnostic threshold set is derived from Train geometry distributions only and is not promoted to runtime.
