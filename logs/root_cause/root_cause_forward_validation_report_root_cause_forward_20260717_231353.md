==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_CANDIDATES_FOUND
Run ID                 : root_cause_forward_20260717_231353
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 79 / 77
Root Cause Rows        : 28
Evaluated Cells        : 81
Eligible Causes        : 1
Research Candidates    : 1
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=26 hit24=76.92% avg24=0.2897% | n12=27 hit12=62.96% | score=18.0747 | ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE

Recent Validation Rows:
- d5e46c8db1efde0a | MACRO_POLICY_PRESSURE BEARISH | 4h=0.7255 correct=False | 12h=-0.0226 correct=True | 24h=0.6363 correct=False
- b13ea6e944e2ae0b | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3754 correct=True | 12h=0.973 correct=False | 24h=-0.269 correct=True
- 8d15d8ed3dba1483 | MACRO_POLICY_PRESSURE BEARISH | 4h=1.0683 correct=False | 12h=0.0306 correct=False | 24h=-0.7402 correct=True
- 305365dd1e8f147a | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.344 correct=True | 12h=-1.1385 correct=True | 24h=-1.0821 correct=True
- 2c326ae272816d94 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.593 correct=True | 12h=0.1343 correct=False | 24h=-1.6197 correct=True
- 4b33e11b09ee5d63 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.7046 correct=False | 12h=-0.6487 correct=True | 24h=-1.4909 correct=True
- 868534a901188736 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6698 correct=True | 12h=-1.7517 correct=True | 24h=-1.9251 correct=True
- 80ec9090403c9cc5 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6785 correct=True | 12h=-2.2387 correct=True | 24h=-0.1612 correct=True
- 9c7ccc7f7a913912 | MACRO_POLICY_PRESSURE BEARISH | 4h=-1.1622 correct=True | 12h=-0.1765 correct=True | 24h=None correct=None
- 6ee47d678b5959fb | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2607 correct=False | 12h=None correct=None | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================