==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_CANDIDATES_FOUND
Run ID                 : root_cause_forward_20260714_125254
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 68 / 65
Root Cause Rows        : 17
Evaluated Cells        : 47
Eligible Causes        : 1
Research Candidates    : 1
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=14 hit24=92.86% avg24=1.0338% | n12=16 hit12=68.75% | score=24.6421 | ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE

Recent Validation Rows:
- 24d04734856aed0b | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.7244 correct=True | 12h=-0.6286 correct=True | 24h=-0.095 correct=True
- e0163ae62a4873df | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.5156 correct=True | 12h=-0.0632 correct=True | 24h=-2.1886 correct=True
- 60decbe99ef52ab6 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2054 correct=False | 12h=0.5369 correct=False | 24h=-1.403 correct=True
- 73d723a8f7dabe21 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2488 correct=False | 12h=-0.3641 correct=True | 24h=-1.7338 correct=True
- 167a3ebec29a4bdd | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6927 correct=True | 12h=-1.9296 correct=True | 24h=-3.0093 correct=True
- 167a3ebec29a4bdd | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6927 correct=True | 12h=-1.9296 correct=True | 24h=-3.0093 correct=True
- dc38b3076363d2d6 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1308 correct=True | 12h=-1.101 correct=True | 24h=-0.6924 correct=True
- 2a6bfe932d977c20 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.5119 correct=True | 12h=-0.0676 correct=True | 24h=None correct=None
- c6a6ca52908a9047 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.069 correct=False | 12h=0.4132 correct=False | 24h=None correct=None
- 184605283f795b80 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.0332 correct=True | 12h=None correct=None | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================