# Freakto v9.0.0 - Evidence Graph Engine Runbook

این ماژول Research-only است و هیچ Paper/Live/Order فعال نمی‌کند.

## هدف

Evidence Graph بین این اجزا رابطه می‌سازد:

```text
Evidence Source -> Market Narrative -> Root Cause -> Decision Context -> Forward Outcome
```

با این کار Freakto فقط نمی‌گوید «علت احتمالی چیست»، بلکه مسیر شواهد تا outcome را قابل ردیابی می‌کند.

## اجرای پیشنهادی

```cmd
python root_cause_dashboard.py --compact
python decision_evaluator.py
python root_cause_forward_validation_dashboard.py --compact
python root_cause_sample_dashboard.py --compact
python evidence_graph_dashboard.py --compact
```

## خروجی‌ها

```text
logs/evidence_graph/evidence_graph_*.json
logs/evidence_graph/evidence_graph_report_*.md
logs/evidence_graph/evidence_graph_nodes_*.csv
logs/evidence_graph/evidence_graph_edges_*.csv
logs/evidence_graph/evidence_graph_paths_*.csv
logs/evidence_graph/evidence_graph_observations.csv
```

## تفسیر

- `LOW_SAMPLE_EDGE`: هنوز sample کافی نیست.
- `MIN_SAMPLE_PROMISING_EDGE`: حداقل sample دارد و مسیر امیدوارکننده است.
- `RESEARCH_POSITIVE_EDGE`: sample پژوهشی کافی دارد و مسیر مثبت است.
- `WEAK_OR_NEGATIVE_EDGE`: مسیر با sample کافی ضعیف یا منفی بوده است.

تا قبل از چند هفته/ماه Forward validation، از این خروجی برای ورود استفاده نکن.
