==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Run ID                 : root_cause_forward_20260716_074955
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 73 / 71
Root Cause Rows        : 22
Evaluated Cells        : 63
Eligible Causes        : 1
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=20 hit24=70.0% avg24=0.0257% | n12=21 hit12=57.14% | score=15.0833 | WEAK_OR_NEGATIVE_FORWARD_EVIDENCE

Recent Validation Rows:
- 167a3ebec29a4bdd | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6927 correct=True | 12h=-1.9296 correct=True | 24h=-3.0093 correct=True
- dc38b3076363d2d6 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1308 correct=True | 12h=-1.101 correct=True | 24h=-0.6924 correct=True
- 2a6bfe932d977c20 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.5119 correct=True | 12h=-0.0676 correct=True | 24h=3.4034 correct=False
- c6a6ca52908a9047 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.069 correct=False | 12h=0.4132 correct=False | 24h=3.641 correct=False
- 184605283f795b80 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0332 correct=True | 12h=3.4733 correct=False | 24h=3.5455 correct=False
- e534f28fd7ae0e53 | MACRO_POLICY_PRESSURE BEARISH | 4h=3.0272 correct=False | 12h=3.4807 correct=False | 24h=3.0019 correct=False
- d5e46c8db1efde0a | MACRO_POLICY_PRESSURE BEARISH | 4h=0.7255 correct=False | 12h=-0.0226 correct=True | 24h=0.6363 correct=False
- b13ea6e944e2ae0b | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3754 correct=True | 12h=0.973 correct=False | 24h=-0.269 correct=True
- 8d15d8ed3dba1483 | MACRO_POLICY_PRESSURE BEARISH | 4h=1.0683 correct=False | 12h=0.0306 correct=False | 24h=None correct=None
- 305365dd1e8f147a | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.344 correct=True | 12h=None correct=None | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================