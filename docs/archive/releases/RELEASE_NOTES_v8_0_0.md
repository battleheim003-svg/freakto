# Release Notes — Freakto v8.0.0

## Root Cause Discovery Engine

این نسخه موتور کشف علت را به پروژه اضافه می‌کند.

### اضافه شد

```text
engine/root_cause_discovery.py
root_cause_dashboard.py
ROOT_CAUSE_DISCOVERY_RUNBOOK.md
RELEASE_NOTES_v8_0_0.md
```

### آپدیت شد

```text
monitor.py
decision_logger.py
decision_log_repair.py
decision_evaluator.py
engine/forward_test.py
engine/research_upgrade_suite.py
.github/workflows/freakto-forward-test.yml
.github/workflows/freakto-health-check.yml
README_NEXT_STEPS.md
FORWARD_TEST_RUNBOOK.md
CAUSAL_INTELLIGENCE_RUNBOOK.md
MARKET_NARRATIVE_RUNBOOK.md
NARRATIVE_DECISION_RUNBOOK.md
RESEARCH_ROBUSTNESS_RUNBOOK.md
SHADOW_GATE_RUNBOOK.md
```

### قابلیت جدید

Root Cause Discovery این دسته علت‌ها را وزن‌دهی می‌کند:

```text
MACRO_POLICY_PRESSURE
REGULATORY_RISK
REGULATORY_ACCESS_OR_MODERNIZATION
EXCHANGE_MARKET_ACCESS
PROTOCOL_UPGRADE_OR_SECURITY
TECHNICAL_STRUCTURE_MOMENTUM
LIQUIDITY_VOLUME_FLOW
DERIVATIVES_LEVERAGE_FLOW
MIXED_EVENT_CONFLICT
UNKNOWN_OR_INSUFFICIENT_EVIDENCE
```

### خروجی جدید decision log

```text
root_cause_primary
root_cause_direction
root_cause_confidence
root_cause_probability_pct
root_cause_evidence_quality
root_cause_verdict
root_cause_evidence_total
root_cause_official_evidence_total
root_cause_top_causes
root_cause_summary
```

### ایمنی

این نسخه هیچ Paper Trade جدید، Live Trade یا سفارش واقعی ایجاد نمی‌کند.
