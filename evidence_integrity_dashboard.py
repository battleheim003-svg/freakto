"""Read-only Evidence Integrity Dashboard for Ledger v2."""

from __future__ import annotations

import streamlit as st

from freakto.evidence.ledger import canonical_cohort, decision_lineage
from freakto.evidence.read_model import coverage_funnel, evidence_summary


st.set_page_config(page_title="Freakto Evidence Integrity", layout="wide")
st.title("Evidence Integrity Dashboard")
st.caption("Read-only. Legacy forward claims are never used for readiness.")

summary = evidence_summary()
st.warning(f"Verdict: {summary['status']}")
left, middle, right, fourth = st.columns(4)
left.metric("Directional terminal", summary["directional_terminal_count"])
middle.metric("Net expectancy", summary["net_expectancy_pct"] if summary["net_expectancy_pct"] is not None else "—")
right.metric("Quarantined rows", summary["quarantined_rows"])
fourth.metric("Costs applied", "Yes" if summary["costs_applied"] else "No")
st.code(summary.get("ledger_sha256") or "Ledger not created", language=None)
st.subheader("Promotion blockers")
st.dataframe(summary["blockers"], use_container_width=True)
st.subheader("Six-symbol coverage funnel")
st.dataframe(coverage_funnel(["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "DOGE/USDT"]), use_container_width=True)
st.subheader("Canonical terminal outcomes")
cohort = canonical_cohort()
st.dataframe(cohort, use_container_width=True)
decision_id = st.text_input("Decision lineage lookup")
if decision_id:
    lineage = decision_lineage(decision_id)
    if lineage:
        st.json(lineage)
    else:
        st.error("Decision not found in Ledger v2.")
