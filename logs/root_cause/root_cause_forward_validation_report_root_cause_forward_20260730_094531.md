==============================================================================================================
🧪 Freakto Root Cause Forward Validation v8.1.0
==============================================================================================================
Status                 : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Run ID                 : root_cause_forward_20260730_094531
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 123 / 121
Root Cause Rows        : 60
Evaluated Cells        : 178
Eligible Causes        : 5
Research Candidates    : 0
Promising Low Sample   : 0
Min Samples / Deadzone : 10 / 0.0%

Top Root-Cause Forward Results:
- MACRO_POLICY_PRESSURE | BEARISH | n24=51 hit24=58.82% avg24=-0.0354% | n12=51 hit12=54.9% | score=11.781 | WEAK_OR_NEGATIVE_FORWARD_EVIDENCE
- LIQUIDITY_VOLUME_FLOW | BEARISH | n24=3 hit24=33.33% avg24=0.2551% | n12=4 hit12=50.0% | score=1.817 | LOW_SAMPLE
- REGULATORY_RISK | BEARISH | n24=3 hit24=0.0% avg24=-0.5968% | n12=3 hit12=0.0% | score=-21.0453 | LOW_SAMPLE
- TECHNICAL_STRUCTURE_MOMENTUM | BEARISH | n24=0 hit24=0.0% avg24=0.0% | n12=1 hit12=0.0% | score=-21.5792 | LOW_SAMPLE
- LIQUIDITY_VOLUME_FLOW | BULLISH | n24=1 hit24=0.0% avg24=-1.6602% | n12=1 hit12=0.0% | score=-31.9344 | LOW_SAMPLE

Recent Validation Rows:
- 45193097b35fec28 | MACRO_POLICY_PRESSURE BEARISH | 4h=-0.1498 correct=True | 12h=0.7734 correct=False | 24h=-1.3158 correct=True
- 9ef1831d3e5e7db2 | LIQUIDITY_VOLUME_FLOW BEARISH | 4h=0.3758 correct=False | 12h=0.9957 correct=False | 24h=-0.9775 correct=True
- ce2152a38e8b04ed | LIQUIDITY_VOLUME_FLOW BEARISH | 4h=0.1925 correct=False | 12h=-0.0275 correct=True | 24h=0.1356 correct=False
- 23774c181fb4986c | REGULATORY_RISK BEARISH | 4h=0.4082 correct=False | 12h=1.379 correct=False | 24h=0.926 correct=False
- 225741368c3a0312 | REGULATORY_RISK BEARISH | 4h=1.0795 correct=False | 12h=0.8135 correct=False | 24h=0.4322 correct=False
- 225741368c3a0312 | REGULATORY_RISK BEARISH | 4h=1.0795 correct=False | 12h=0.8135 correct=False | 24h=0.4322 correct=False
- 7a2db4ab07a7dc1e | LIQUIDITY_VOLUME_FLOW BULLISH | 4h=-1.8623 correct=False | 12h=-2.2654 correct=False | 24h=-1.6602 correct=False
- b9bf53c1c6d053b3 | LIQUIDITY_VOLUME_FLOW BEARISH | 4h=-0.0476 correct=True | 12h=-0.2935 correct=True | 24h=0.0767 correct=False
- ca949ccc20e71d1f | LIQUIDITY_VOLUME_FLOW BEARISH | 4h=-0.5988 correct=True | 12h=0.2807 correct=False | 24h=None correct=None
- 3b8dbac4326c2ec5 | TECHNICAL_STRUCTURE_MOMENTUM BEARISH | 4h=0.6106 correct=False | 12h=0.6592 correct=False | 24h=None correct=None

Recommendations:
→ ابتدا decision_evaluator.py را اجرا کن تا market_return_after_* برای تصمیم‌ها ساخته شود.
→ Root Causeهایی که hit-rate پایدار و sample کافی دارند بعداً می‌توانند وارد Root-Cause Gate Simulator شوند.
→ تا قبل از sample کافی، نتیجه فقط Research/Shadow بماند و Paper/Live فعال نشود.

Warnings:
⚠️ Root Cause Forward Validation فقط رابطه علت‌های پژوهشی با outcome بعدی را می‌سنجد؛ سیگنال خرید/فروش نیست.
⚠️ این validation باید چند هفته/ماه sample جمع کند تا قابل اتکا شود.
==============================================================================================================