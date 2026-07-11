==============================================================================================================
🧫 Freakto Root Cause Sample Accumulator v8.2.0
==============================================================================================================
Status                 : ROOT_CAUSE_SAMPLE_COLLECTION_ACTIVE_LOW_SAMPLE
Run ID                 : root_cause_samples_20260711_113538
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 55 / 52
Root Cause Rows        : 4
Evaluated Cells        : 8
Unique Root Causes     : 1
Validation Status      : ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE
Candidates / Promising : 0 / 1
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=1 | research=8 | candidate=28

Root Cause Buckets:
- MACRO_POLICY_PRESSURE | BEARISH | rows=4 cells=8 | n24=1 hit24=100.0% avg24=0.3409% | maturity=LOW_SAMPLE_ACCUMULATING | LOW_SAMPLE_KEEP_COLLECTING

Sample Gaps:
- MACRO_POLICY_PRESSURE: gap_min=2 | gap_research=22 | gap_candidate=82

Blockers:
⛔ Root Cause evaluated cells کمتر از حداقل است: 8/10

Recommendations:
→ چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.
→ پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.
→ تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.

Warnings:
⚠️ Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.
⚠️ Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.
==============================================================================================================