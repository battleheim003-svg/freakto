==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Run ID                 : root_cause_forward_20260725_073719
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 106 / 103
Root Cause Rows        : 53
Evaluated Cells        : 158
Eligible Causes        : 2
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=51 hit24=58.82% avg24=-0.0354% | n12=51 hit12=54.9% | score=11.781 | WEAK_OR_NEGATIVE_FORWARD_EVIDENCE
- LIQUIDITY_VOLUME_FLOW | BEARISH | n24=1 hit24=100.0% avg24=0.9775% | n12=2 hit12=50.0% | score=2.2245 | LOW_SAMPLE

Recent Validation Rows:
- 1389bb6e5f0417b1 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2265 correct=False | 12h=0.3811 correct=False | 24h=-0.5316 correct=True
- eb912c226d6c9276 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.3632 correct=True | 12h=-0.7205 correct=True | 24h=-0.9597 correct=True
- dc39f9b9d0fd19ca | MACRO_POLICY_PRESSURE BEARISH | 4h=0.1627 correct=False | 12h=-0.9093 correct=True | 24h=-0.786 correct=True
- 7bb3f489e724e429 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2553 correct=False | 12h=0.1244 correct=False | 24h=-0.6118 correct=True
- 54cfc321b1fa07cc | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1885 correct=True | 12h=-0.5847 correct=True | 24h=-1.6663 correct=True
- 038f2a7b5bc821fe | MACRO_POLICY_PRESSURE BEARISH | 4h=0.2969 correct=False | 12h=-0.7352 correct=True | 24h=-1.6282 correct=True
- 6ab31caf8aa357f1 | MACRO_POLICY_PRESSURE BEARISH | 4h=0.1777 correct=False | 12h=-0.8996 correct=True | 24h=0.0871 correct=False
- 45193097b35fec28 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1498 correct=True | 12h=0.7734 correct=False | 24h=-1.3158 correct=True
- 9ef1831d3e5e7db2 | LIQUIDITY_VOLUME_FLOW BEARISH | 4h=0.3758 correct=False | 12h=0.9957 correct=False | 24h=-0.9775 correct=True
- ce2152a38e8b04ed | LIQUIDITY_VOLUME_FLOW BEARISH | 4h=0.1925 correct=False | 12h=-0.0275 correct=True | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================