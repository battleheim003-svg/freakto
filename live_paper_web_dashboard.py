"""Streamlit UI for observing Freakto Shadow/Paper and controlling Shadow locally."""
from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import streamlit as st

from engine.live_paper_dashboard import (
    equity_curve, excel_report, load_dashboard_data, pdf_report,
    performance_attribution, regime_heatmap,
)
from engine.live_paper_runtime import load_runtime_config
from engine.shadow_process_controller import ShadowProcessController


PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "live_paper_config.json"
LOGO_PATH = PROJECT_ROOT / "assets" / "freakto-logo.png"


@st.cache_data(ttl=15, show_spinner=False)
def _data(mode: str):
    return load_dashboard_data(mode, CONFIG_PATH)


def _refresh() -> None:
    _data.clear()
    st.rerun()


@st.cache_data(show_spinner=False)
def _logo_data_uri() -> str:
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _brand_header() -> None:
    st.markdown(
        f"""
        <style>
          .freakto-brand {{
            display: flex; align-items: center; gap: 1.25rem;
            padding: 1.1rem 1.25rem; margin: 0 0 1.35rem 0;
            border: 1px solid rgba(255, 145, 31, .24); border-radius: 18px;
            background: linear-gradient(135deg, rgba(255,145,31,.10), rgba(116,54,180,.08));
          }}
          .freakto-logo {{
            width: 96px; height: 96px; flex: 0 0 96px; object-fit: cover;
            border-radius: 50%; border: 3px solid #ff911f;
            box-shadow: 0 8px 24px rgba(0,0,0,.32), 0 0 0 5px rgba(255,145,31,.10);
          }}
          .freakto-copy h1 {{ margin: 0; padding: 0; font-size: 2.2rem; line-height: 1.08; }}
          .freakto-tagline {{ margin-top: .45rem; color: #aeb7c4; font-size: .92rem; letter-spacing: .02em; }}
          .freakto-powered {{ margin-top: .72rem; color: #ff9f43; font-size: .74rem; font-weight: 700; letter-spacing: .16em; }}
          @media (max-width: 640px) {{
            .freakto-brand {{ gap: .9rem; padding: .9rem; }}
            .freakto-logo {{ width: 72px; height: 72px; flex-basis: 72px; }}
            .freakto-copy h1 {{ font-size: 1.45rem; }}
          }}
        </style>
        <div class="freakto-brand">
          <img class="freakto-logo" src="{_logo_data_uri()}" alt="Freakto logo">
          <div class="freakto-copy">
            <h1>Freakto Shadow / Paper</h1>
            <div class="freakto-tagline">Research-grade market observation and paper execution control center</div>
            <div class="freakto-powered">POWERED BY ALAVI</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Freakto Shadow / Paper", page_icon="📈", layout="wide")
    _brand_header()
    st.caption("PAPER ONLY — the dashboard cannot place real exchange orders.")
    config = load_runtime_config(CONFIG_PATH)
    controller = ShadowProcessController(PROJECT_ROOT, config.state_roots["shadow"])

    with st.sidebar:
        st.header("Shadow worker")
        status = controller.status()
        if status.running:
            st.success(f"RUNNING · PID {status.pid}")
        else:
            st.info("STOPPED")
        groups = st.selectbox("Universe", ["core", "core,growth", "all"], index=0, disabled=status.running)
        interval = st.number_input("Cycle interval (seconds)", min_value=60, max_value=3600, value=300, step=60, disabled=status.running)
        left, middle, right = st.columns(3)
        if left.button("Start", disabled=status.running, use_container_width=True):
            try:
                controller.start(groups=groups, interval_seconds=float(interval))
                st.success("Shadow started; existing state was preserved.")
                _refresh()
            except Exception as exc:
                st.error(f"Start failed: {type(exc).__name__}: {exc}")
        if middle.button("Stop", disabled=not status.running, use_container_width=True):
            try:
                controller.stop()
                st.success("Shadow stopped safely; state was preserved.")
                _refresh()
            except Exception as exc:
                st.error(f"Stop failed: {type(exc).__name__}: {exc}")
        if right.button("Restart", disabled=not status.running, use_container_width=True):
            try:
                controller.restart(groups=status.groups, interval_seconds=status.interval_seconds)
                st.success("Shadow restarted with existing state.")
                _refresh()
            except Exception as exc:
                st.error(f"Restart failed: {type(exc).__name__}: {exc}")
        if st.button("Refresh data", use_container_width=True):
            _refresh()
        st.caption("Closing this browser tab does not stop the worker. Turning off the laptop does.")

    mode = st.radio("Data view", ["shadow", "paper"], horizontal=True)
    data = _data(mode)
    metrics = data.state.get("metrics", {})
    cols = st.columns(6)
    values = [
        ("Gate", "PASSED" if data.gate.get("passed") else "PENDING"),
        ("Elapsed", f"{data.gate.get('days', 0):.2f} days"),
        ("Unique decisions", metrics.get("unique_decisions", 0)),
        ("Complete 4h candles", metrics.get("complete_4h_candles", 0)),
        ("Fresh providers", f"{data.gate.get('provider_freshness_pct', 0):.1f}%"),
        ("Unhandled crashes", metrics.get("unhandled_crashes", 0)),
    ]
    for column, (label, value) in zip(cols, values):
        column.metric(label, value)

    st.subheader("Shadow gate")
    checks = pd.DataFrame([{"check": name, "passed": passed} for name, passed in data.gate.get("checks", {}).items()])
    st.dataframe(checks, use_container_width=True, hide_index=True)

    st.subheader("Trade / decision log")
    st.dataframe(data.fills if not data.fills.empty else data.intents, use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    curve = equity_curve(data)
    with left:
        st.subheader("Equity curve")
        if curve.empty:
            st.info("Equity appears after Paper fills are recorded.")
        else:
            st.line_chart(curve.set_index("timestamp_utc")["equity_usdt"])
    with right:
        st.subheader("Performance attribution")
        attribution = performance_attribution(data)
        if attribution.empty:
            st.info("Attribution appears after Paper fills are recorded.")
        else:
            st.dataframe(attribution, use_container_width=True, hide_index=True)

    st.subheader("Regime heatmap")
    heatmap = regime_heatmap(data)
    if heatmap.empty:
        st.info("No regime-tagged decisions are available yet.")
    else:
        st.dataframe(heatmap.style.background_gradient(cmap="YlGnBu"), use_container_width=True)

    st.subheader("Export")
    export_left, export_right = st.columns(2)
    export_left.download_button("Download Excel report", excel_report(data), f"freakto_{mode}_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    export_right.download_button("Download PDF report", pdf_report(data), f"freakto_{mode}_report.pdf", "application/pdf", use_container_width=True)


if __name__ == "__main__":
    main()
