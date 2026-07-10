==============================================================================================================
🧠 Freakto Research Robustness & Intelligence Suite v8.2.0
==============================================================================================================
Status: RESEARCH_SUITE_WITH_BLOCKERS
Run ID: research_suite_20260710_112932

Sections:
- gate_robustness: NO_BACKTEST_DATA
- cost_adjusted_backtest: NO_BACKTEST_DATA
- meta_labeling: LOW_SAMPLE_META_LABELING
- ensemble_explainability: EXPLAINABILITY_READY
- data_enrichment: ENRICHMENT_CONNECTORS_PRESENT
- regime_research: NO_BACKTEST_DATA
- forward_regime_labeling: FORWARD_REGIME_LABELING_READY
- regime_gate_matrix: NO_BACKTEST_DATA
- regime_shadow_gates: REGIME_SHADOW_GATES_ACTIVE
- forward_shadow_coverage: FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND
- automatic_event_collector: AUTO_EVENT_COLLECTOR_LEDGER_ONLY
- causal_intelligence: CAUSAL_CONTEXT_WITH_BLOCKERS
- market_narrative: MARKET_NARRATIVE_WITH_CONFLICTS
- narrative_decision_conflict: NARRATIVE_DECISION_HIGH_CONFLICT
- root_cause_discovery: ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
- root_cause_forward_validation: NO_ROOT_CAUSE_ROWS_EVALUATED
- root_cause_sample_tracker: NO_ROOT_CAUSE_SAMPLES_YET
- evidence_graph: NO_EVIDENCE_GRAPH_ROWS
- cross_exchange_validation: NO_BACKTEST_DATA
- research_db: RESEARCH_DB_READY
- pipeline_health: PIPELINE_HEALTHY
- strict_readiness: STRICT_READINESS_RESEARCH_ONLY
- position_sizing_lab: NO_BACKTEST_DATA
- airdrop_shadow_research: AIRDROP_SHADOW_READY
- static_dashboard: STATIC_DASHBOARD_READY

Gate Robustness Highlights:

Regime-Gate Matrix Highlights:
- NO_BACKTEST_DATA | candidates=0 | horizon=24h

Forward Regime Labeling:
- FORWARD_REGIME_LABELING_READY | known=52 | unknown=0 | injected=0

Regime Shadow Gate Highlights:
- REGIME_SHADOW_GATES_ACTIVE | regime_gates=4 | signals=0 | eval=16
- REGIME_TRENDING_BEAR__RISK_MEDIUM: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%

Forward Shadow Coverage / Bull Probe:
- FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND | decisions=52 | shadow_signals=17 | eval_shadow=16
- BULL_STRUCTURE_SCORE_GE_10: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_STRUCTURE_SCORE_GE_10_LONG: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | bt_net=0.0%
- BULL_RISK_MEDIUM: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | bt_net=0.0%

Causal/Event Intelligence:
- CAUSAL_CONTEXT_WITH_BLOCKERS | sources_ok=12 | trusted_ok=12 | catalyst=44/100 | conflict=HIGH
- primary=MULTI_SOURCE_EVENT_CONSENSUS | verdict=CAUSAL_CONFLICT_RESEARCH_ONLY

Market Narrative Engine:
- MARKET_NARRATIVE_WITH_CONFLICTS | label=MIXED_NARRATIVE_CONFLICT | dir=BEARISH | theme=MACRO_POLICY | score=-23.4322
- accepted=7 | noise_filtered=0 | risk=HIGH | conflict=HIGH

Narrative/Decision Conflict:
- NARRATIVE_DECISION_HIGH_CONFLICT | side=LONG | narrative=BEARISH | alignment=CONFLICTING
- conflict=86/100 | adj=-35 | verdict=HIGH_CONFLICT_WATCHLIST_ONLY

Root Cause Discovery:
- ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS | primary=MACRO_POLICY_PRESSURE | dir=BEARISH | conf=MEDIUM | p=45.74%
- quality=HIGH | evidence=15 | verdict=PROBABLE_CAUSE_BUT_CONFLICTED

Root Cause Forward Validation:
- NO_ROOT_CAUSE_ROWS_EVALUATED | rows=0 | cells=0 | candidates=0 | low_sample=0

Strict Readiness:
- STRICT_READINESS_RESEARCH_ONLY | blockers=4
  ⛔ Backtest sample کمتر از 100 است.
  ⛔ Backtest net expectancy از نظر CI95 بالای صفر نیست.
  ⛔ Forward complete samples کمتر از 30 است.
  ⛔ پوشش regime کافی نیست؛ حداقل دو رژیم معتبر لازم است.

Pipeline Health:
- PIPELINE_HEALTHY | alerts=0

Suite Blockers:
⛔ gate_robustness: هیچ دیتای backtest کامل برای robust validation وجود ندارد.
⛔ cost_adjusted_backtest: Backtest data موجود نیست.
⛔ meta_labeling: برای meta-labeling حداقل 120 نمونه لازم است.
⛔ regime_research: Backtest data موجود نیست.
⛔ regime_gate_matrix: هیچ historical_backtest_evaluations کامل برای ساخت Regime-Gate Matrix پیدا نشد.
⛔ regime_shadow_gates: کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 16
⛔ forward_shadow_coverage: Shadow evaluated samples کمتر از 30 است: 16
⛔ causal_intelligence: Causal conflict بالا است؛ هر استفاده عملی باید downgrade شود و فقط Research بماند.
⛔ root_cause_forward_validation: هیچ ردیف decision_evaluations با root_cause_primary/root_cause_direction قابل ارزیابی پیدا نشد.
⛔ root_cause_sample_tracker: هنوز هیچ Root Cause row قابل ارزیابی وجود ندارد.
⛔ evidence_graph: هیچ decision_evaluations row با root_cause قابل ساخت گراف پیدا نشد؛ root_cause_dashboard و decision_evaluator را اجرا کن.
⛔ cross_exchange_validation: Backtest data موجود نیست.

Safety: هیچ بخش v6/v7/v8 سفارش واقعی ارسال نمی‌کند و Paper Trade جدید ایجاد نمی‌کند.
==============================================================================================================