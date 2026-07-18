==============================================================================================================
🧫 Freakto Root Cause Sample Accumulator v8.2.0
==============================================================================================================
Status                 : ROOT_CAUSE_VALIDATION_RESEARCH_CANDIDATES_FOUND
Run ID                 : root_cause_samples_20260718_200828
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 84 / 81
Root Cause Rows        : 33
Evaluated Cells        : 95
Unique Root Causes     : 1
Validation Status      : ROOT_CAUSE_FORWARD_CANDIDATES_FOUND
Candidates / Promising : 1 / 0
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=0 | research=0 | candidate=0

Root Cause Buckets:
- MACRO_POLICY_PRESSURE | BEARISH | rows=33 cells=95 | n24=30 hit24=66.67% avg24=0.1464% | maturity=CANDIDATE_SAMPLE_READY | PROMISING_RESEARCH_WATCHLIST

Sample Gaps:
- MACRO_POLICY_PRESSURE: gap_min=0 | gap_research=0 | gap_candidate=0

Recommendations:
→ چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.
→ پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.
→ تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.

Warnings:
⚠️ Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.
⚠️ Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.
==============================================================================================================