"""Small Streamlit renderers for the unified Control Center."""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd
import streamlit as st


def _frame(rows: object) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        return rows
    return pd.DataFrame(list(rows or []))


def _count(rows: object) -> int:
    return len(rows) if rows is not None else 0


def _trade_table(rows: object, *, empty: str) -> None:
    frame = _frame(rows)
    if frame.empty:
        st.info(empty)
    else:
        preferred = [
            name
            for name in (
                "paper_trade_id",
                "trade_id",
                "symbol_normalized",
                "symbol",
                "side_normalized",
                "side",
                "status_normalized",
                "status",
                "entry_time_normalized",
                "entry_time",
                "exit_time_normalized",
                "exit_time",
                "net_r",
                "net_pnl_pct",
            )
            if name in frame.columns
        ]
        st.dataframe(frame[preferred] if preferred else frame, use_container_width=True, hide_index=True)


def render_source_path(value: object) -> None:
    """Render Windows paths without Markdown consuming backslash escapes."""
    st.caption("Source")
    st.code(str(value), language=None)


def render_spot_paper(
    view: dict[str, Any],
    *,
    mode: str,
    start_campaign: Callable[[], object] | None = None,
    stop_campaign: Callable[[], object] | None = None,
) -> None:
    campaign = dict(view.get("campaign") or {})
    performance = dict(view.get("performance") or {})
    readiness = dict(view.get("readiness") or {})
    governance = dict(view.get("governance") or {})
    showcase = mode == "Showcase"
    st.title("Spot Paper Trading")
    if showcase:
        st.warning("Showcase · Not official evidence")
    else:
        st.success("Official Paper · canonical evidence domain")
    cards = st.columns(4)
    cards[0].metric("Worker health", campaign.get("health") or campaign.get("status", "UNKNOWN"))
    cards[1].metric("Open trades", _count(view.get("open_trades")))
    cards[2].metric("Closed trades", _count(view.get("closed_trades")))
    cards[3].metric("Net P&L", performance.get("total_pnl_usd", performance.get("net_pnl_pct", "—")))
    tabs = st.tabs(
        ["Overview", "Campaign", "Open Trades", "Closed Trades", "Performance", "Costs", "Network / Recovery"]
    )
    with tabs[0]:
        render_source_path(view.get("source"))
        st.write("Evidence eligible:", bool(view.get("evidence_eligible")))
        for warning in view.get("warnings") or []:
            st.warning(str(warning))
    with tabs[1]:
        if governance:
            st.error("Status: HOLDOUT CONSUMED — NOT VALIDATED")
            st.write("Research outcome: HOLDOUT CRITERIA FAILED")
            st.write("Promotion eligible: NO")
            st.write("Development candidate: NONE")
            st.caption(
                "This experiment is terminal. Its Holdout has been consumed and cannot be "
                "reused for tuning, promotion, or campaign launch."
            )
            st.caption(
                "Future contract: "
                + str(view.get("walk_forward_contract_version") or "UNKNOWN")
            )
            st.button("Strategy Promotion", disabled=True, use_container_width=True)
            for blocker in governance.get("failure_reasons") or []:
                st.warning(str(blocker))
        st.json(
            {
                key: campaign.get(key)
                for key in (
                    "status",
                    "campaign_id",
                    "elapsed_days",
                    "cycles",
                    "successful_cycles",
                    "failed_cycles",
                    "network_skipped_cycles",
                    "heartbeat_utc",
                )
            }
        )
        if not showcase and start_campaign and stop_campaign:
            preflight_ready = bool(readiness.get("research_collection_ready"))
            blockers = list(readiness.get("blockers") or [])
            if not preflight_ready:
                st.warning("Campaign start is blocked by Paper preflight.")
                for blocker in blockers:
                    st.write(f"• {blocker}")
                st.caption("Build the missing prerequisites in Research, then run preflight again.")
            confirmed = st.checkbox("I confirm this is zero-capital Paper operation.")
            left, right = st.columns(2)
            if left.button(
                "Start / resume campaign",
                disabled=not confirmed or not preflight_ready,
                use_container_width=True,
            ):
                try:
                    start_campaign()
                    st.rerun()
                except RuntimeError as exc:
                    st.error(str(exc))
            campaign_active = str(campaign.get("status") or "") in {"STARTING", "RUNNING"}
            if right.button(
                "Stop campaign safely",
                disabled=not campaign_active,
                use_container_width=True,
            ):
                try:
                    stop_campaign()
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with tabs[2]:
        _trade_table(view.get("open_trades"), empty="No official open trades." if not showcase else "No Showcase open trades.")
    with tabs[3]:
        _trade_table(view.get("closed_trades"), empty="No official closed trades." if not showcase else "No Showcase closed trades.")
    with tabs[4]:
        if performance:
            st.json(performance)
        else:
            st.info("No performance summary is available yet.")
    with tabs[5]:
        st.json(view.get("costs") or {})
    with tabs[6]:
        st.json(
            {
                "health": campaign.get("health"),
                "status": campaign.get("status"),
                "network_skips": campaign.get("network_skipped_cycles", 0),
                "heartbeat_utc": campaign.get("heartbeat_utc"),
                "persistence_source": campaign.get("persistence_source"),
            }
        )


def render_research(view: dict[str, Any], evidence: dict[str, Any]) -> None:
    st.title("Research")
    tabs = st.tabs(["Replay", "Forward / Shadow", "Fresh OOS", "Evidence Integrity", "Reports"])
    with tabs[0]:
        st.metric("Replay data", "Available" if view["replay"] else "Missing")
    with tabs[1]:
        st.metric("Forward reports", view["forward_reports"])
    with tabs[2]:
        st.metric("Fresh OOS artifacts", view["fresh_oos"])
    with tabs[3]:
        st.metric("Verdict", evidence.get("status", "NO_LEDGER"))
        st.metric("Directional terminal", evidence.get("directional_terminal_count", 0))
        blockers = evidence.get("blockers") or []
        if blockers:
            st.dataframe(blockers, use_container_width=True)
    with tabs[4]:
        st.caption("Research reports remain read-only from this workspace.")


def render_airdrop(view: dict[str, Any], *, launch: Callable[[], object] | None = None) -> None:
    st.title("Airdrop")
    st.caption("Independent outcomes domain · no Paper worker imports or state writes")
    cards = st.columns(3)
    cards[0].metric("Storage", "Available" if view["available"] else "Not initialized")
    cards[1].metric("Tables", len(view["table_counts"]))
    cards[2].metric("Paper state touched", "No")
    if view.get("warning"):
        st.warning(view["warning"])
    if view["table_counts"]:
        st.dataframe(
            [{"Table": key, "Rows": value} for key, value in view["table_counts"].items()],
            use_container_width=True,
            hide_index=True,
        )
    if launch and st.button("Run Airdrop outcomes workflow", type="primary"):
        launch()
        st.rerun()


def render_system(view: dict[str, Any], jobs: list[dict[str, Any]]) -> None:
    st.title("System")
    cards = st.columns(4)
    cards[0].metric("Provider / Network", view["network"])
    cards[1].metric("Recovery", view["recovery"])
    cards[2].metric("Jobs", len(jobs))
    cards[3].metric("JSON logs", view["logs"])
    tabs = st.tabs(["Provider / Network", "Jobs", "Logs", "Recovery", "Settings & Safety"])
    with tabs[0]:
        st.json({"network_skips": view["network_skips"], "heartbeat_utc": view["heartbeat_utc"]})
    with tabs[1]:
        st.dataframe(jobs, use_container_width=True, hide_index=True) if jobs else st.info("No jobs recorded.")
    with tabs[2]:
        st.caption(f"{view['logs']} JSON log artifacts are available.")
    with tabs[3]:
        st.json({"status": view["recovery"], "warnings": view["warnings"]})
    with tabs[4]:
        st.success("Paper-only · localhost-only · zero real capital")
        st.json(
            {
                "LIVE_TRADING_ENABLED": view["live_orders_enabled"],
                "REAL_CAPITAL_ENABLED": view["real_capital_enabled"],
            }
        )
