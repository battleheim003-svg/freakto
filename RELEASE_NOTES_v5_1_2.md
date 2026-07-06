# Freakto v5.1.2 — Decision Log Schema Repair Patch

## Why
Older `logs/decisions.csv` files may have a shorter header than newer v4.7+ decision rows. When a newer row is appended under an older header, `pandas.read_csv` can fail during `decision_evaluator.py`, which blocks the Forward Test cycle.

## Added
- `engine/csv_utils.py`
- `decision_log_repair.py`

## Changed
- `decision_logger.py` now migrates `decisions.csv` header before appending new rows.
- `decision_evaluator.py` now falls back to lenient CSV reading for mixed-schema logs.
- `engine/forward_test.py` now runs `decision_log_repair.py` before `decision_evaluator.py`.
- `forward_test_dashboard.py` version updated to v5.1.2.

## Test
```cmd
python decision_log_repair.py
python decision_evaluator.py
python forward_test_dashboard.py --plan
python forward_test_dashboard.py --cycle --validate --continue-on-error --send
```

No live orders are sent. This patch only repairs local log compatibility for data collection.
