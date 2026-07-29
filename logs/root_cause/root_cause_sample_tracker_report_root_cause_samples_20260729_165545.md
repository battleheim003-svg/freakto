==============================================================================================================
🧫 Freakto Root Cause Sample Accumulator v8.2.0
==============================================================================================================
Status                 : ROOT_CAUSE_SAMPLE_TARGET_REACHED_MIXED
Run ID                 : root_cause_samples_20260729_165545
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 121 / 119
Root Cause Rows        : 58
Evaluated Cells        : 174
Unique Root Causes     : 4
Validation Status      : ROOT_CAUSE_FORWARD_MIXED_OR_WEAK
Candidates / Promising : 0 / 0
Min/Research/Candidate : 10 / 30 / 90 cells
More decisions needed  : min=0 | research=0 | candidate=0

Root Cause Buckets:
- MACRO_POLICY_PRESSURE | BEARISH | rows=51 cells=153 | n24=51 hit24=58.82% avg24=-0.0354% | maturity=CANDIDATE_SAMPLE_READY | WEAK_OR_NEGATIVE_PROVISIONAL
- LIQUIDITY_VOLUME_FLOW | BEARISH | rows=3 cells=9 | n24=3 hit24=33.33% avg24=0.2551% | maturity=LOW_SAMPLE_ACCUMULATING | LOW_SAMPLE_KEEP_COLLECTING
- REGULATORY_RISK | BEARISH | rows=3 cells=9 | n24=3 hit24=0.0% avg24=-0.5968% | maturity=LOW_SAMPLE_ACCUMULATING | LOW_SAMPLE_KEEP_COLLECTING
- LIQUIDITY_VOLUME_FLOW | BULLISH | rows=1 cells=3 | n24=1 hit24=0.0% avg24=-1.6602% | maturity=LOW_SAMPLE_ACCUMULATING | LOW_SAMPLE_KEEP_COLLECTING

Sample Gaps:
- MACRO_POLICY_PRESSURE: gap_min=0 | gap_research=0 | gap_candidate=0
- LIQUIDITY_VOLUME_FLOW: gap_min=1 | gap_research=21 | gap_candidate=81
- REGULATORY_RISK: gap_min=1 | gap_research=21 | gap_candidate=81
- LIQUIDITY_VOLUME_FLOW: gap_min=7 | gap_research=27 | gap_candidate=87

Recommendations:
→ چرخه Forward را هر 4 ساعت یا با GitHub Actions اجرا کن تا Root Cause rows بیشتر شود.
→ پس از هر root_cause_dashboard.py، decision_evaluator.py و سپس root_cause_forward_validation_dashboard.py را اجرا کن.
→ تا وقتی حداقل 30-50 تصمیم دارای Root Cause جمع نشده، نتیجه فقط Research/Shadow بماند.

Warnings:
⚠️ Root Cause Sample Tracker فقط بلوغ نمونه‌ها را می‌سنجد؛ Paper/Live فعال نمی‌کند.
⚠️ Promotion واقعی فقط بعد از Forward validation پایدار و sample کافی مجاز است.
==============================================================================================================