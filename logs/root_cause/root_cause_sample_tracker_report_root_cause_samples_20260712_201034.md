==============================================================================================================
🧫 Freakto Root Cause Sample Accumulator v8.2.0
==============================================================================================================
Status                 : ROOT_CAUSE_VALIDATION_RESEARCH_CANDIDATES_FOUND
Run ID                 : root_cause_samples_20260712_201034
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 62 / 58
Root Cause Rows        : 11
Evaluated Cells        : 28
Unique Root Causes     : 1
Validation Status      : ROOT_CAUSE_FORWARD_CANDIDATES_FOUND
Candidates / Promising : 1 / 0
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=0 | research=1 | candidate=21

Root Cause Buckets:
- MACRO_POLICY_PRESSURE | BEARISH | rows=11 cells=28 | n24=7 hit24=85.71% avg24=0.232% | maturity=MIN_SAMPLE_READY | MIXED_PROVISIONAL

Sample Gaps:
- MACRO_POLICY_PRESSURE: gap_min=0 | gap_research=2 | gap_candidate=62

Recommendations:
→ چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.
→ پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.
→ تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.

Warnings:
⚠️ Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.
⚠️ Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.
==============================================================================================================