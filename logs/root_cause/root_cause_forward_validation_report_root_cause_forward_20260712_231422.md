==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_CANDIDATES_FOUND
Run ID                 : root_cause_forward_20260712_231422
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 62 / 58
Root Cause Rows        : 11
Evaluated Cells        : 28
Eligible Causes        : 1
Research Candidates    : 1
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=7 hit24=85.71% avg24=0.232% | n12=10 hit12=60.0% | score=18.3385 | ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE

Recent Validation Rows:
- 503dadce97c9976f | MACRO_POLICY_PRESSURE BEARISH | 4h=0.3364 correct=False | 12h=0.3387 correct=False | 24h=0.5361 correct=False
- b02ae7fe2b105ae9 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0567 correct=True | 12h=0.033 correct=False | 24h=-0.5747 correct=True
- 3a81916cf067dc15 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0111 correct=True | 12h=0.1067 correct=False | 24h=-0.5226 correct=True
- 00f41894c0e1eb8c | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0089 correct=True | 12h=-0.5612 correct=True | 24h=-0.2608 correct=True
- bd63b27e00fa757b | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.2023 correct=True | 12h=-0.3156 correct=True | 24h=-0.3786 correct=True
- 264ad8f589baac98 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1393 correct=True | 12h=-0.4502 correct=True | 24h=None correct=None
- 24d04734856aed0b | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.7244 correct=True | 12h=-0.6286 correct=True | 24h=-0.095 correct=True
- e0163ae62a4873df | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.5156 correct=True | 12h=-0.0632 correct=True | 24h=None correct=None
- 60decbe99ef52ab6 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2054 correct=False | 12h=0.5369 correct=False | 24h=None correct=None
- 73d723a8f7dabe21 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2488 correct=False | 12h=None correct=None | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================