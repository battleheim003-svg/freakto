==============================================================================================================
🕸️ Freakto Evidence Graph Engine v9.0.0
==============================================================================================================
Status                 : NO_EVIDENCE_GRAPH_ROWS
Run ID                 : evidence_graph_20260711_072642
Evaluations File       : logs/decision_evaluations.csv
Rows / Complete        : 54 / 51
Graph Rows             : 0
Nodes / Edges / Paths  : 0 / 0 / 0
Graph Maturity         : NO_GRAPH_DATA
Min/Research/Candidate : 10 / 30 / 90 evaluated cells

Blockers:
⛔ هیچ decision_evaluations row با root_cause قابل ساخت گراف پیدا نشد؛ root_cause_dashboard و decision_evaluator را اجرا کن.

Recommendations:
→ چرخه Forward را منظم اجرا کن تا مسیرهای evidence به outcomeهای بیشتری وصل شوند.
→ مسیرهایی که چند هفته متوالی hit-rate و signed-return مثبت دارند بعداً می‌توانند وارد Evidence Weight Review شوند.
→ اگر یک منبع یا روایت در Forward چندبار fail شد، وزن آن باید فقط بعد از sample کافی بازبینی شود.

Warnings:
⚠️ Evidence Graph فقط رابطه‌های پژوهشی بین شواهد، روایت، علت و outcome را می‌سازد؛ سیگنال خرید/فروش نیست.
⚠️ تا وقتی sample کافی وجود نداشته باشد، هیچ وزن evidence نباید برای Paper/Live تغییر کند.
==============================================================================================================