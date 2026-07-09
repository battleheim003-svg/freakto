==============================================================================================================
🧠 Freakto Research Robustness & Intelligence Suite v6.2.0
==============================================================================================================
Status: RESEARCH_SUITE_WITH_BLOCKERS
Run ID: research_suite_20260708_171127

Sections:
- gate_robustness: ROBUST_GATES_FOUND
- cost_adjusted_backtest: COST_ADJUSTED_READY
- meta_labeling: META_LABEL_BUILDING
- ensemble_explainability: EXPLAINABILITY_READY
- data_enrichment: ENRICHMENT_CONNECTORS_PRESENT
- regime_research: REGIME_RESEARCH_READY
- regime_gate_matrix: REGIME_GATE_CANDIDATES_FOUND
- regime_shadow_gates: REGIME_SHADOW_GATES_ACTIVE
- cross_exchange_validation: SINGLE_PROVIDER_ONLY
- research_db: RESEARCH_DB_READY
- pipeline_health: PIPELINE_ATTENTION_REQUIRED
- strict_readiness: STRICT_READINESS_RESEARCH_ONLY
- position_sizing_lab: POSITION_SIZING_RESEARCH_READY
- airdrop_shadow_research: AIRDROP_SHADOW_READY
- static_dashboard: STATIC_DASHBOARD_READY

Gate Robustness Highlights:
- VOLUME_SCORE_GE_10: ROBUST_RESEARCH_CANDIDATE | n=34 | net=0.5631% | stability=60.0%
- QUALITY_STRUCTURE_RISK_MEDIUM: ROBUST_RESEARCH_CANDIDATE | n=41 | net=0.3069% | stability=60.0%
- QUALITY_VOLUME_HEDGE: LOW_SAMPLE | n=2 | net=1.5292% | stability=100.0%
- BNB_LONG_SCORE_GE_60: LOW_SAMPLE | n=11 | net=0.3533% | stability=75.0%
- SCORE_GE_80: LOW_SAMPLE | n=20 | net=0.2297% | stability=60.0%

Regime-Gate Matrix Highlights:
- REGIME_GATE_CANDIDATES_FOUND | candidates=4 | horizon=24h
- TRENDING_BEAR × STRUCTURE_SCORE_GE_10: n=47 | net=0.6404% | verdict=REGIME_RESEARCH_CANDIDATE
- TRENDING_BEAR × RISK_MEDIUM: n=37 | net=0.5946% | verdict=REGIME_RESEARCH_CANDIDATE
- TRENDING_BEAR × STRUCTURE_SCORE_GE_10 × SHORT: n=47 | net=0.6404% | verdict=REGIME_RESEARCH_CANDIDATE
- TRENDING_BEAR × RISK_MEDIUM × SHORT: n=37 | net=0.5946% | verdict=REGIME_RESEARCH_CANDIDATE

Regime Shadow Gate Highlights:
- REGIME_SHADOW_GATES_ACTIVE | regime_gates=4 | signals=0 | eval=14
- REGIME_TRENDING_BEAR__RISK_MEDIUM: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: SHADOW_BUILDING | signals=0 | eval=0 | avg=0.0%

Strict Readiness:
- STRICT_READINESS_RESEARCH_ONLY | blockers=2
  ⛔ Backtest net expectancy از نظر CI95 بالای صفر نیست.
  ⛔ Forward complete samples کمتر از 30 است.

Pipeline Health:
- PIPELINE_ATTENTION_REQUIRED | alerts=1

Suite Blockers:
⛔ meta_labeling: AUC یا sample هنوز برای استفاده عملی کافی نیست.
⛔ regime_gate_matrix: Baseline net return کلی هنوز مثبت نیست.
⛔ regime_shadow_gates: کل نمونه‌های ارزیابی‌شده Shadow کمتر از 30 است: 14
⛔ strict_readiness: Backtest net expectancy از نظر CI95 بالای صفر نیست.
⛔ strict_readiness: Forward complete samples کمتر از 30 است.

Safety: هیچ بخش v6/v6.1/v6.2 سفارش واقعی ارسال نمی‌کند و Paper Trade جدید ایجاد نمی‌کند.
==============================================================================================================