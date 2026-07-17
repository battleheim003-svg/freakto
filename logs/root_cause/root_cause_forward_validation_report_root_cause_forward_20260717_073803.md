==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_CANDIDATES_FOUND
Run ID                 : root_cause_forward_20260717_073803
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 77 / 74
Root Cause Rows        : 26
Evaluated Cells        : 74
Eligible Causes        : 1
Research Candidates    : 1
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=23 hit24=73.91% avg24=0.172% | n12=25 hit12=60.0% | score=16.9189 | ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE

Recent Validation Rows:
- 184605283f795b80 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0332 correct=True | 12h=3.4733 correct=False | 24h=3.5455 correct=False
- e534f28fd7ae0e53 | MACRO_POLICY_PRESSURE BEARISH | 4h=3.0272 correct=False | 12h=3.4807 correct=False | 24h=3.0019 correct=False
- d5e46c8db1efde0a | MACRO_POLICY_PRESSURE BEARISH | 4h=0.7255 correct=False | 12h=-0.0226 correct=True | 24h=0.6363 correct=False
- b13ea6e944e2ae0b | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3754 correct=True | 12h=0.973 correct=False | 24h=-0.269 correct=True
- 8d15d8ed3dba1483 | MACRO_POLICY_PRESSURE BEARISH | 4h=1.0683 correct=False | 12h=0.0306 correct=False | 24h=-0.7402 correct=True
- 305365dd1e8f147a | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.344 correct=True | 12h=-1.1385 correct=True | 24h=-1.0821 correct=True
- 2c326ae272816d94 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.593 correct=True | 12h=0.1343 correct=False | 24h=-1.6197 correct=True
- 4b33e11b09ee5d63 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.7046 correct=False | 12h=-0.6487 correct=True | 24h=None correct=None
- 868534a901188736 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6698 correct=True | 12h=-1.7517 correct=True | 24h=None correct=None
- 80ec9090403c9cc5 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6785 correct=True | 12h=None correct=None | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================