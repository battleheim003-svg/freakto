==============================================================================================================
🧠 Freakto Research Robustness & Intelligence Suite v10.0.0
==============================================================================================================
Status: RESEARCH_SUITE_WITH_BLOCKERS
Run ID: research_suite_20260710_233823

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
- causal_intelligence: CAUSAL_CONTEXT_INTERNAL_ONLY
- market_narrative: MARKET_NARRATIVE_WITH_CONFLICTS
- narrative_decision_conflict: NARRATIVE_CONTEXT_ONLY
- root_cause_discovery: ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS
- root_cause_forward_validation: ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE
- root_cause_sample_tracker: ROOT_CAUSE_SAMPLE_COLLECTION_ACTIVE_LOW_SAMPLE
- evidence_graph: NO_EVIDENCE_GRAPH_ROWS
- market_replay: NO_REPLAY_ROWS
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
- FORWARD_REGIME_LABELING_READY | known=54 | unknown=0 | injected=0

Regime Shadow Gate Highlights:
- REGIME_SHADOW_GATES_ACTIVE | regime_gates=4 | signals=0 | eval=16
- REGIME_TRENDING_BEAR__RISK_MEDIUM: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%

Forward Shadow Coverage / Bull Probe:
- FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND | decisions=54 | shadow_signals=19 | eval_shadow=16
- BULL_STRUCTURE_SCORE_GE_10: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_STRUCTURE_SCORE_GE_10_LONG: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | bt_net=0.0%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | bt_net=0.0%
- BULL_RISK_MEDIUM: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | bt_net=0.0%

Causal/Event Intelligence:
- CAUSAL_CONTEXT_INTERNAL_ONLY | sources_ok=13 | trusted_ok=13 | catalyst=32/100 | conflict=LOW
- primary=MULTI_SOURCE_EVENT_CONSENSUS | verdict=CAUSAL_CONTEXT_WEAK_OR_RISKY

Market Narrative Engine:
- MARKET_NARRATIVE_WITH_CONFLICTS | label=MIXED_NARRATIVE_CONFLICT | dir=BEARISH | theme=MACRO_POLICY | score=-21.7979
- accepted=7 | noise_filtered=0 | risk=HIGH | conflict=LOW

Narrative/Decision Conflict:
- NARRATIVE_CONTEXT_ONLY | side=NEUTRAL | narrative=BEARISH | alignment=CONTEXT_ONLY
- conflict=62/100 | adj=-12 | verdict=NEUTRAL_DECISION_CONTEXT_ONLY

Market Replay v10:
- NO_REPLAY_ROWS | rows=0 | complete=0 | directional=0
- test/research audit=FAILED_NO_REPLAY_ROWS | avg_net24=0.0% | PF=0.0

Root Cause Discovery:
- ROOT_CAUSE_MIXED_WITH_CONTRADICTIONS | primary=MACRO_POLICY_PRESSURE | dir=BEARISH | conf=MEDIUM | p=42.35%
- quality=HIGH | evidence=16 | verdict=PROBABLE_CAUSE_BUT_CONFLICTED

Root Cause Forward Validation:
- ROOT_CAUSE_FORWARD_PROMISING_LOW_SAMPLE | rows=2 | cells=3 | candidates=0 | low_sample=1
- MACRO_POLICY_PRESSURE BEARISH: n24=0 hit24=0.0% avg24=0.0% | FORWARD_PROMISING_LOW_SAMPLE

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
⛔ root_cause_sample_tracker: Root Cause evaluated cells کمتر از حداقل است: 3/10
⛔ evidence_graph: هیچ decision_evaluations row با root_cause قابل ساخت گراف پیدا نشد؛ root_cause_dashboard و decision_evaluator را اجرا کن.
⛔ market_replay: هیچ ردیف Market Replay ساخته نشد.
⛔ cross_exchange_validation: Backtest data موجود نیست.
⛔ strict_readiness: Backtest sample کمتر از 100 است.

Safety: هیچ بخش v6 تا v10 سفارش واقعی ارسال نمی‌کند؛ Market Replay نیز فقط Research/Backtest است.
==============================================================================================================