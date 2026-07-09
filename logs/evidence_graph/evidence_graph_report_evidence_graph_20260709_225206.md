==============================================================================================================
🕸️ Freakto Evidence Graph Engine v9.0.0
==============================================================================================================
Status                 : EVIDENCE_GRAPH_ACTIVE_LOW_SAMPLE
Run ID                 : evidence_graph_20260709_225206
Evaluations File       : logs\decision_evaluations.csv
Rows / Complete        : 32 / 32
Graph Rows             : 1
Nodes / Edges / Paths  : 5 / 6 / 1
Graph Maturity         : LOW_SAMPLE_ACCUMULATING
Min/Research/Candidate : 10 / 30 / 90 evaluated cells

Top Evidence Paths:
- EVIDENCE_SOURCE:FEDERAL_RESERVE_PRESS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_MISS_24H | n=1 hit24=0.0% avg24=-1.7776% | LOW_SAMPLE_EDGE

Root Cause Learning Signals:
- MACRO_POLICY_PRESSURE | BEARISH | n24=1 hit24=0.0% avg24=-1.7776% | LOW_SAMPLE_DO_NOT_RETUNE

Top Edges:
- EVIDENCE_SOURCE:FEDERAL_RESERVE_PRESS -> NARRATIVE:NO_NARRATIVE_NEUTRAL_NO_THEME (SOURCE_SUPPORTS_NARRATIVE) | n=1 hit24=0.0% score=-6.7443 | LOW_SAMPLE_EDGE
- EVIDENCE_SOURCE:FEDERAL_RESERVE_PRESS -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH (SOURCE_SUPPORTS_ROOT_CAUSE) | n=1 hit24=0.0% score=-6.7443 | LOW_SAMPLE_EDGE
- NARRATIVE:NO_NARRATIVE_NEUTRAL_NO_THEME -> ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH (NARRATIVE_SUPPORTS_ROOT_CAUSE) | n=1 hit24=0.0% score=-6.7443 | LOW_SAMPLE_EDGE
- ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> DECISION_CONTEXT:NEUTRAL_MONITOR_ONLY_SCORE_10_19 (ROOT_CAUSE_CONTEXTUALIZES_DECISION) | n=1 hit24=0.0% score=-6.7443 | LOW_SAMPLE_EDGE
- DECISION_CONTEXT:NEUTRAL_MONITOR_ONLY_SCORE_10_19 -> OUTCOME:ROOT_CAUSE_MISS_24H (DECISION_OBSERVED_OUTCOME) | n=1 hit24=0.0% score=-6.7443 | LOW_SAMPLE_EDGE
- ROOT_CAUSE:MACRO_POLICY_PRESSURE_BEARISH -> OUTCOME:ROOT_CAUSE_MISS_24H (ROOT_CAUSE_TESTED_BY_OUTCOME) | n=1 hit24=0.0% score=-6.7443 | LOW_SAMPLE_EDGE

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