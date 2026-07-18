==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_CANDIDATES_FOUND
Run ID                 : root_cause_forward_20260718_231620
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 84 / 81
Root Cause Rows        : 33
Evaluated Cells        : 95
Eligible Causes        : 1
Research Candidates    : 1
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=30 hit24=66.67% avg24=0.1464% | n12=32 hit12=59.38% | score=15.7704 | ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE

Recent Validation Rows:
- 4b33e11b09ee5d63 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.7046 correct=False | 12h=-0.6487 correct=True | 24h=-1.4909 correct=True
- 868534a901188736 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6698 correct=True | 12h=-1.7517 correct=True | 24h=-1.9251 correct=True
- 80ec9090403c9cc5 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6785 correct=True | 12h=-2.2387 correct=True | 24h=-0.1612 correct=True
- 9c7ccc7f7a913912 | MACRO_POLICY_PRESSURE BEARISH | 4h=-1.1622 correct=True | 12h=-0.1765 correct=True | 24h=0.7002 correct=False
- 6ee47d678b5959fb | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2607 correct=False | 12h=1.0066 correct=False | 24h=1.211 correct=False
- 16e7c62c85964757 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3686 correct=True | 12h=-0.2476 correct=True | 24h=0.6156 correct=False
- 16e7c62c85964757 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3686 correct=True | 12h=-0.2476 correct=True | 24h=0.6156 correct=False
- d397f2108ee4c3ee | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0119 correct=True | 12h=0.1637 correct=False | 24h=None correct=None
- 27c1a62dadf0ae27 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.0809 correct=False | 12h=0.8654 correct=False | 24h=None correct=None
- 1eda876ed7c82ff5 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.0946 correct=False | 12h=None correct=None | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================