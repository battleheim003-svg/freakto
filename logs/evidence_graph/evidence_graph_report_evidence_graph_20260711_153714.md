==============================================================================================================
🕸️ Freakto Evidence Graph Engine v9.0.0
==============================================================================================================
Status                 : EVIDENCE_GRAPH_ACTIVE_LOW_SAMPLE
Run ID                 : evidence_graph_20260711_153714
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 56 / 52
Graph Rows             : 1
Nodes / Edges / Paths  : 7 / 10 / 3
Graph Maturity         : LOW_SAMPLE_ACCUMULATING
Min/Research/Candidate : 10 / 30 / 90 evaluated cells

Top Evidence Paths:
- EVIDENCE_SOURCE:FEDERAL_RESERVE_PRESS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_HIT_24H | n=1 hit24=100.0% avg24=0.3281% | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:MANUAL_EVENTS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_HIT_24H | n=1 hit24=100.0% avg24=0.3281% | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:AUTO_EVENTS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_HIT_24H | n=1 hit24=100.0% avg24=0.3281% | LOW_SAMPLE_EDGE

Root Cause Learning Signals:
- MACRO_POLICY_PRESSURE | BEARISH | n24=1 hit24=100.0% avg24=0.3281% | LOW_SAMPLE_DO_NOT_RETUNE

Top Edges:
- NARRATIVE:MIXED_NARRATIVE_CONFLICT_BEARISH_MACRO_POLICY -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH (NARRATIVE_SUPPORTS_ROOT_CAUSE) | n=3 hit24=100.0% score=5.4281 | LOW_SAMPLE_EDGE
- ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> DECISION_CONTEXT:LONG_WATCHLIST_SCORE_70_79 (ROOT_CAUSE_CONTEXTUALIZES_DECISION) | n=3 hit24=100.0% score=5.4281 | LOW_SAMPLE_EDGE
- DECISION_CONTEXT:LONG_WATCHLIST_SCORE_70_79 -> OUTCOME:ROOT_CAUSE_HIT_24H (DECISION_OBSERVED_OUTCOME) | n=3 hit24=100.0% score=5.4281 | LOW_SAMPLE_EDGE
- ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_HIT_24H (ROOT_CAUSE_TESTED_BY_OUTCOME) | n=3 hit24=100.0% score=5.4281 | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:FEDERAL_RESERVE_PRESS -> NARRATIVE:MIXED_NARRATIVE_CONFLICT_BEARISH_MACRO_POLICY (SOURCE_SUPPORTS_NARRATIVE) | n=1 hit24=100.0% score=5.3614 | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:FEDERAL_RESERVE_PRESS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH (SOURCE_SUPPORTS_ROOT_CAUSE) | n=1 hit24=100.0% score=5.3614 | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:MANUAL_EVENTS -> NARRATIVE:MIXED_NARRATIVE_CONFLICT_BEARISH_MACRO_POLICY (SOURCE_SUPPORTS_NARRATIVE) | n=1 hit24=100.0% score=5.3614 | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:MANUAL_EVENTS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH (SOURCE_SUPPORTS_ROOT_CAUSE) | n=1 hit24=100.0% score=5.3614 | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:AUTO_EVENTS -> NARRATIVE:MIXED_NARRATIVE_CONFLICT_BEARISH_MACRO_POLICY (SOURCE_SUPPORTS_NARRATIVE) | n=1 hit24=100.0% score=5.3614 | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:AUTO_EVENTS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH (SOURCE_SUPPORTS_ROOT_CAUSE) | n=1 hit24=100.0% score=5.3614 | LOW_SAMPLE_EDGE

Blockers:
⛔ Evidence graph evaluated cells کمتر از حداقل است: 3/10

Recommendations:
→ چرخه Forward را منظم اجرا کن تا مسیرهای evidence به outcomeهای بیشتری وصل شوند.
→ مسیرهایی که چند هفته متوالی hit-rate و signed-return مثبت دارند بعداً می‌توانند وارد Evidence Weight Review شوند.
→ اگر یک منبع یا روایت در Forward چندبار fail شد، وزن آن باید فقط بعد از sample کافی بازبینی شود.

Warnings:
⚠️ Evidence Graph فقط رابطه‌های پژوهشی بین شواهد، روایت، علت و outcome را می‌سازد؛ سیگنال خرید/فروش نیست.
⚠️ تا وقتی sample کافی وجود نداشته باشد، هیچ وزن evidence نباید برای Paper/Live تغییر کند.
==============================================================================================================