==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_LOW_SAMPLE
Run ID                 : root_cause_forward_20260709_223005
Evaluations File       : logs\decision_evaluations.csv
Rows / Complete        : 32 / 32
Root Cause Rows        : 1
Evaluated Cells        : 3
Eligible Causes        : 1
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=1 hit24=0.0% avg24=-1.7776% | n12=1 hit12=0.0% | score=-27.5747 | LOW_SAMPLE

Recent Validation Rows:
- 0678ab66434e5aeb | MACRO_POLICY_PRESSURE BEARISH | 4h=1.6307 correct=False | 12h=0.7447 correct=False | 24h=1.7776 correct=False

Blockers:
⛔ تعداد سلول‌های ارزیابی‌شده کمتر از حداقل sample است: 3/10

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================