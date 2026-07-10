==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE
Run ID                 : root_cause_forward_20260710_181157
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 52 / 50
Root Cause Rows        : 1
Evaluated Cells        : 1
Eligible Causes        : 1
Research Candidates    : 0
Promising Low Sample   : 1
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=0 hit24=0.0% avg24=0.0% | n12=0 hit12=0.0% | score=23.3824 | FORWARD_PROMISING_LOW_SAMPLE

Recent Validation Rows:
- 8782f6983beb22b1 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6103 correct=True | 12h=None correct=None | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================