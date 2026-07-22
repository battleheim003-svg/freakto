==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Run ID                 : root_cause_forward_20260722_093912
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 97 / 95
Root Cause Rows        : 46
Evaluated Cells        : 136
Eligible Causes        : 1
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=44 hit24=54.55% avg24=-0.1974% | n12=46 hit12=54.35% | score=10.8898 | WEAK_OR_NEGATIVE_FORWARD_EVIDENCE

Recent Validation Rows:
- a4c050f4ffee1f35 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3714 correct=True | 12h=-0.3856 correct=True | 24h=-0.6667 correct=True
- 96c993f864bcdef8 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.1674 correct=False | 12h=0.3962 correct=False | 24h=0.8321 correct=False
- 11648f97f4132c45 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.4105 correct=False | 12h=-0.2822 correct=True | 24h=1.0664 correct=False
- 3dd864bb08d25699 | MACRO_POLICY_PRESSURE BEARISH | 4h=1.1318 correct=False | 12h=1.3525 correct=False | 24h=2.9865 correct=False
- 3dd864bb08d25699 | MACRO_POLICY_PRESSURE BEARISH | 4h=1.1318 correct=False | 12h=1.3525 correct=False | 24h=2.9865 correct=False
- 76c73c1e767434c0 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6883 correct=True | 12h=-0.0316 correct=True | 24h=1.6667 correct=False
- c3cd14aaf48bfe86 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.1736 correct=False | 12h=1.6122 correct=False | 24h=1.9995 correct=False
- 1389bb6e5f0417b1 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2265 correct=False | 12h=0.3811 correct=False | 24h=-0.5316 correct=True
- eb912c226d6c9276 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3632 correct=True | 12h=-0.7205 correct=True | 24h=None correct=None
- dc39f9b9d0fd19ca | MACRO_POLICY_PRESSURE BEARISH | 4h=0.1627 correct=False | 12h=-0.9093 correct=True | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================