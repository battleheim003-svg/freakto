==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_CANDIDATES_FOUND
Run ID                 : root_cause_forward_20260714_072800
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 67 / 64
Root Cause Rows        : 16
Evaluated Cells        : 44
Eligible Causes        : 1
Research Candidates    : 1
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=13 hit24=92.31% avg24=1.06% | n12=15 hit12=73.33% | score=25.1837 | ROOT_CAUSE_FORWARD_RESEARCH_CANDIDATE

Recent Validation Rows:
- 264ad8f589baac98 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1393 correct=True | 12h=-0.4502 correct=True | 24h=-0.8127 correct=True
- 24d04734856aed0b | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.7244 correct=True | 12h=-0.6286 correct=True | 24h=-0.095 correct=True
- e0163ae62a4873df | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.5156 correct=True | 12h=-0.0632 correct=True | 24h=-2.1886 correct=True
- 60decbe99ef52ab6 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2054 correct=False | 12h=0.5369 correct=False | 24h=-1.403 correct=True
- 73d723a8f7dabe21 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2488 correct=False | 12h=-0.3641 correct=True | 24h=-1.7338 correct=True
- 167a3ebec29a4bdd | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6927 correct=True | 12h=-1.9296 correct=True | 24h=-3.0093 correct=True
- 167a3ebec29a4bdd | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.6927 correct=True | 12h=-1.9296 correct=True | 24h=-3.0093 correct=True
- dc38b3076363d2d6 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1308 correct=True | 12h=-1.101 correct=True | 24h=None correct=None
- 2a6bfe932d977c20 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.5119 correct=True | 12h=-0.0676 correct=True | 24h=None correct=None
- c6a6ca52908a9047 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.069 correct=False | 12h=None correct=None | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================