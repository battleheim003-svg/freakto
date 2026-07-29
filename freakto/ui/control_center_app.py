"""Unified Streamlit application composition root."""

from __future__ import annotations

import streamlit as st

from freakto.evidence.read_model import evidence_summary
from freakto.paper.campaign import start_campaign, stop_campaign
from freakto.ui.control_center_sections import (
    render_airdrop,
    render_research,
    render_spot_paper,
    render_system,
)
from freakto.ui.control_center_state import ROOT
from freakto.ui.job_manager import list_jobs, start_workflow_job
from freakto.ui.navigation import NAVIGATION
from freakto.ui.unified_state import (
    airdrop_view,
    official_paper_view,
    research_view,
    showcase_view,
    system_view,
)

def run() -> None:
    st.set_page_config(page_title="Freakto Control Center", page_icon="⚡", layout="wide")
    st.sidebar.markdown("## ⚡ FREAKTO")
    page = st.sidebar.radio("Workspace", NAVIGATION)
    st.sidebar.caption("ZERO CAPITAL · LIVE OFF · LOCALHOST ONLY")

    if page == "Spot Paper Trading":
        mode = st.sidebar.selectbox("Data Mode", ["Official Paper", "Showcase"])
        view = official_paper_view(ROOT) if mode == "Official Paper" else showcase_view(ROOT)
        render_spot_paper(
            view,
            mode=mode,
            start_campaign=start_campaign if mode == "Official Paper" else None,
            stop_campaign=stop_campaign if mode == "Official Paper" else None,
        )
    elif page == "Research":
        try:
            evidence = evidence_summary()
        except Exception as exc:
            evidence = {"status": "UNAVAILABLE", "blockers": [f"{type(exc).__name__}"]}
        render_research(research_view(ROOT), evidence)
    elif page == "Airdrop":
        render_airdrop(
            airdrop_view(ROOT),
            launch=lambda: start_workflow_job("AIRDROP_OUTCOMES"),
        )
    else:
        render_system(system_view(ROOT), list_jobs())


run()
