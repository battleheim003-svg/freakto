==============================================================================================================
🧫 Freakto Root Cause Sample Accumulator v8.2.0
==============================================================================================================
Status                 : ROOT_CAUSE_PROMISING_LOW_SAMPLE_TRACKING
Run ID                 : root_cause_samples_20260712_114910
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 60 / 55
Root Cause Rows        : 9
Evaluated Cells        : 20
Unique Root Causes     : 1
Validation Status      : ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE
Candidates / Promising : 0 / 1
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=0 | research=4 | candidate=24

Root Cause Buckets:
- MACRO_POLICY_PRESSURE | BEARISH | rows=9 cells=20 | n24=4 hit24=75.0% avg24=0.2223% | maturity=MIN_SAMPLE_READY | MIXED_PROVISIONAL

Sample Gaps:
- MACRO_POLICY_PRESSURE: gap_min=0 | gap_research=10 | gap_candidate=70

Recommendations:
→ چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.
→ پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.
→ تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.

Warnings:
⚠️ Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.
⚠️ Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.
==============================================================================================================