==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Run ID                 : root_cause_forward_20260711_201130
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 57 / 54
Root Cause Rows        : 6
Evaluated Cells        : 14
Eligible Causes        : 1
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=3 hit24=33.33% avg24=-0.1283% | n12=5 hit12=20.0% | score=2.8754 | LOW_SAMPLE

Recent Validation Rows:
- 8782f6983beb22b1 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6103 correct=True | 12h=-0.409 correct=True | 24h=-0.3281 correct=True
- 503dadce97c9976f | MACRO_POLICY_PRESSURE BEARISH | 4h=0.3364 correct=False | 12h=0.3387 correct=False | 24h=0.5361 correct=False
- b02ae7fe2b105ae9 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0567 correct=True | 12h=0.033 correct=False | 24h=0.1768 correct=False
- 3a81916cf067dc15 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0111 correct=True | 12h=0.1067 correct=False | 24h=None correct=None
- 00f41894c0e1eb8c | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0089 correct=True | 12h=0.1904 correct=False | 24h=None correct=None
- bd63b27e00fa757b | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.2023 correct=True | 12h=None correct=None | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================