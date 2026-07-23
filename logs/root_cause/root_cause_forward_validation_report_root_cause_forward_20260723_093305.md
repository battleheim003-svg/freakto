==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Run ID                 : root_cause_forward_20260723_093305
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 100 / 98
Root Cause Rows        : 49
Evaluated Cells        : 145
Eligible Causes        : 1
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=47 hit24=57.45% avg24=-0.1347% | n12=49 hit12=55.1% | score=11.3854 | WEAK_OR_NEGATIVE_FORWARD_EVIDENCE

Recent Validation Rows:
- 3dd864bb08d25699 | MACRO_POLICY_PRESSURE BEARISH | 4h=1.1318 correct=False | 12h=1.3525 correct=False | 24h=2.9865 correct=False
- 3dd864bb08d25699 | MACRO_POLICY_PRESSURE BEARISH | 4h=1.1318 correct=False | 12h=1.3525 correct=False | 24h=2.9865 correct=False
- 76c73c1e767434c0 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6883 correct=True | 12h=-0.0316 correct=True | 24h=1.6667 correct=False
- c3cd14aaf48bfe86 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.1736 correct=False | 12h=1.6122 correct=False | 24h=1.9995 correct=False
- 1389bb6e5f0417b1 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2265 correct=False | 12h=0.3811 correct=False | 24h=-0.5316 correct=True
- eb912c226d6c9276 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3632 correct=True | 12h=-0.7205 correct=True | 24h=-0.9597 correct=True
- dc39f9b9d0fd19ca | MACRO_POLICY_PRESSURE BEARISH | 4h=0.1627 correct=False | 12h=-0.9093 correct=True | 24h=-0.786 correct=True
- 7bb3f489e724e429 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2553 correct=False | 12h=0.1244 correct=False | 24h=-0.6118 correct=True
- 54cfc321b1fa07cc | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1885 correct=True | 12h=-0.5847 correct=True | 24h=None correct=None
- 038f2a7b5bc821fe | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2969 correct=False | 12h=-0.7352 correct=True | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================