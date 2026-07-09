==============================================================================================================
🧫 Freakto Root Cause Sample Accumulator v8.2.0
==============================================================================================================
Status                 : ROOT_CAUSE_SAMPLE_COLLECTION_ACTIVE_LOW_SAMPLE
Run ID                 : root_cause_samples_20260709_223006
Evaluations File       : logs\decision_evaluations.csv
Rows / Complete        : 32 / 32
Root Cause Rows        : 1
Evaluated Cells        : 3
Unique Root Causes     : 1
Validation Status      : ROOT_CAUSE_FORWARD_LOW_SAMPLE
Candidates / Promising : 0 / 0
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=3 | research=9 | candidate=29

Root Cause Buckets:
- MACRO_POLICY_PRESSURE | BEARISH | rows=1 cells=3 | n24=1 hit24=0.0% avg24=-1.7776% | maturity=LOW_SAMPLE_ACCUMULATING | LOW_SAMPLE_KEEP_COLLECTING

Sample Gaps:
- MACRO_POLICY_PRESSURE: gap_min=7 | gap_research=27 | gap_candidate=87

Blockers:
⛔ Root Cause evaluated cells کمتر از حداقل است: 3/10

Recommendations:
→ چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.
→ پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.
→ تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.

Warnings:
⚠️ Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.
⚠️ Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.
==============================================================================================================