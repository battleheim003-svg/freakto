==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Run ID                 : root_cause_forward_20260727_124342
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 115 / 113
Root Cause Rows        : 56
Evaluated Cells        : 166
Eligible Causes        : 3
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=51 hit24=58.82% avg24=-0.0354% | n12=51 hit12=54.9% | score=11.781 | WEAK_OR_NEGATIVE_FORWARD_EVIDENCE
- LIQUIDITY_VOLUME_FLOW | BEARISH | n24=2 hit24=50.0% avg24=0.421% | n12=2 hit12=50.0% | score=-4.7595 | LOW_SAMPLE
- REGULATORY_RISK | BEARISH | n24=1 hit24=0.0% avg24=-0.926% | n12=3 hit12=0.0% | score=-22.5899 | LOW_SAMPLE

Recent Validation Rows:
- 7bb3f489e724e429 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2553 correct=False | 12h=0.1244 correct=False | 24h=-0.6118 correct=True
- 54cfc321b1fa07cc | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1885 correct=True | 12h=-0.5847 correct=True | 24h=-1.6663 correct=True
- 038f2a7b5bc821fe | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2969 correct=False | 12h=-0.7352 correct=True | 24h=-1.6282 correct=True
- 6ab31caf8aa357f1 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.1777 correct=False | 12h=-0.8996 correct=True | 24h=0.0871 correct=False
- 45193097b35fec28 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1498 correct=True | 12h=0.7734 correct=False | 24h=-1.3158 correct=True
- 9ef1831d3e5e7db2 | LIQUIDITY_VOLUME_FLOW BEARISH | 4h=0.3758 correct=False | 12h=0.9957 correct=False | 24h=-0.9775 correct=True
- ce2152a38e8b04ed | LIQUIDITY_VOLUME_FLOW BEARISH | 4h=0.1925 correct=False | 12h=-0.0275 correct=True | 24h=0.1356 correct=False
- 23774c181fb4986c | REGULATORY_RISK BEARISH | 4h=0.4082 correct=False | 12h=1.379 correct=False | 24h=0.926 correct=False
- 225741368c3a0312 | REGULATORY_RISK BEARISH | 4h=1.0795 correct=False | 12h=0.8135 correct=False | 24h=None correct=None
- 225741368c3a0312 | REGULATORY_RISK BEARISH | 4h=1.0795 correct=False | 12h=0.8135 correct=False | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================