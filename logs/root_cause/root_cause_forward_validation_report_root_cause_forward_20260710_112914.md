==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : NO_ROOT_CAUSE_ROWS_EVALUATED
Run ID                 : root_cause_forward_20260710_112914
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 51 / 49
Root Cause Rows        : 0
Evaluated Cells        : 0
Eligible Causes        : 0
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Blockers:
⛔ هیچ ردیف decision_evaluations با root_cause_primary/root_cause_direction قابل ارزیابی پیدا نشد.

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================