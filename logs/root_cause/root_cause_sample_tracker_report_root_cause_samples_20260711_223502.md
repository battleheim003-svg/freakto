==============================================================================================================
🧫 Freakto Root Cause Sample Accumulator v8.2.0
==============================================================================================================
Status                 : ROOT_CAUSE_MIN_SAMPLE_READY
Run ID                 : root_cause_samples_20260711_223502
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 57 / 53
Root Cause Rows        : 6
Evaluated Cells        : 12
Unique Root Causes     : 1
Validation Status      : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Candidates / Promising : 0 / 0
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=0 | research=6 | candidate=26

Root Cause Buckets:
- MACRO_POLICY_PRESSURE | BEARISH | rows=6 cells=12 | n24=2 hit24=50.0% avg24=-0.104% | maturity=MIN_SAMPLE_READY | MIXED_PROVISIONAL

Sample Gaps:
- MACRO_POLICY_PRESSURE: gap_min=0 | gap_research=18 | gap_candidate=78

Recommendations:
→ چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.
→ پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.
→ تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.

Warnings:
⚠️ Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.
⚠️ Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.
==============================================================================================================