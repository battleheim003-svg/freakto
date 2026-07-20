==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_CANDIDATES_FOUND
Run ID                 : root_cause_forward_20260720_082645
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 90 / 88
Root Cause Rows        : 39
Evaluated Cells        : 115
Eligible Causes        : 1
Research Candidates    : 1
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=37 hit24=62.16% avg24=0.0627% | n12=39 hit12=56.41% | score=13.5565 | ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE

Recent Validation Rows:
- 16e7c62c85964757 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3686 correct=True | 12h=-0.2476 correct=True | 24h=0.6156 correct=False
- d397f2108ee4c3ee | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0119 correct=True | 12h=0.1637 correct=False | 24h=1.0813 correct=False
- 27c1a62dadf0ae27 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.0809 correct=False | 12h=0.8654 correct=False | 24h=1.0938 correct=False
- 1eda876ed7c82ff5 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.0946 correct=False | 12h=1.2098 correct=False | 24h=0.6369 correct=False
- 66cf83150f574075 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.4227 correct=False | 12h=0.2265 correct=False | 24h=-0.16 correct=True
- 66cf83150f574075 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.4227 correct=False | 12h=0.2265 correct=False | 24h=-0.16 correct=True
- be8b6299583c6b0a | MACRO_POLICY_PRESSURE BEARISH | 4h=0.0005 correct=False | 12h=-0.2042 correct=True | 24h=0.2457 correct=False
- a4c050f4ffee1f35 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3714 correct=True | 12h=-0.3856 correct=True | 24h=-0.6667 correct=True
- 96c993f864bcdef8 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.1674 correct=False | 12h=0.3962 correct=False | 24h=None correct=None
- 11648f97f4132c45 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.4105 correct=False | 12h=-0.2822 correct=True | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================