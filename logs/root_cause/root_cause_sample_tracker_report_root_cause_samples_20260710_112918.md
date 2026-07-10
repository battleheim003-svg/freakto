==============================================================================================================
🧫 Freakto Root Cause Sample Accumulator v8.2.0
==============================================================================================================
Status                 : NO_ROOT_CAUSE_SAMPLES_YET
Run ID                 : root_cause_samples_20260710_112918
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 51 / 49
Root Cause Rows        : 0
Evaluated Cells        : 0
Unique Root Causes     : 0
Validation Status      : NO_ROOT_CAUSE_ROWS_EVALUATED
Candidates / Promising : 0 / 0
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=4 | research=10 | candidate=30

Blockers:
⛔ هنوز هیچ Root Cause row قابل ارزیابی وجود ندارد.

Recommendations:
→ چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.
→ پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.
→ تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.

Warnings:
⚠️ Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.
⚠️ Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.
==============================================================================================================