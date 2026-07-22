"""Retro-cyberpunk Streamlit UI for Freakto Shadow/Paper operations."""
from __future__ import annotations

import base64
import html
from pathlib import Path
from typing import Any

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

TEXT = {
    "EN": {
        "control": "SHADOW CONTROL", "running": "RUNNING", "stopped": "STOPPED",
        "universe": "UNIVERSE", "interval": "CYCLE INTERVAL / SEC",
        "start": "START", "stop": "STOP", "restart": "REBOOT", "refresh": "SYNC DATA",
        "started": "Shadow booted. State preserved.", "stopped_ok": "Shadow stopped safely. State preserved.",
        "restarted": "Shadow rebooted with existing state.", "start_failed": "BOOT FAILURE",
        "stop_failed": "SHUTDOWN FAILURE", "restart_failed": "REBOOT FAILURE",
        "worker_note": "Browser may close. The worker stays alive while the laptop is on.",
        "light_mode": "LIGHT PROTOCOL", "data_view": "DATA CHANNEL", "shadow": "SHADOW", "paper": "PAPER",
        "paper_only": "SIMULATION ZONE // ZERO REAL EXCHANGE ORDERS",
        "tagline": "RETRO QUANT TERMINAL // MARKET CHAOS, BUT MAKE IT DATA",
        "latest_trades": "LATEST EXECUTION BOARD", "no_trades": "NO PAPER FILLS YET",
        "no_trades_note": "Shadow is watching. Doge is judging. Capital is safe.",
        "gate": "GATE", "passed": "PASSED", "pending": "PENDING", "elapsed": "ELAPSED",
        "days": "days", "decisions": "UNIQUE DECISIONS", "candles": "COMPLETE 4H",
        "fresh": "PROVIDER FRESH", "handled": "HANDLED FAILURES", "crashes": "UNHANDLED CRASHES",
        "gate_matrix": "SHADOW GATE MATRIX", "check": "CHECK", "status": "STATUS",
        "trade_log": "TRADE / DECISION LOG", "equity": "EQUITY CURVE",
        "attribution": "PERFORMANCE ATTRIBUTION", "regime": "REGIME HEATMAP",
        "export": "REPORT EXPORT", "excel": "DOWNLOAD EXCEL", "pdf": "DOWNLOAD PDF",
        "equity_wait": "Equity telemetry appears after Paper fills.",
        "attr_wait": "Attribution appears after Paper fills.", "regime_wait": "No regime-tagged decisions yet.",
    },
    "FA": {
        "control": "کنترل شدو", "running": "در حال اجرا", "stopped": "متوقف",
        "universe": "جهان ارزی", "interval": "فاصله چرخه / ثانیه",
        "start": "شروع", "stop": "توقف", "restart": "راه‌اندازی مجدد", "refresh": "به‌روزرسانی داده",
        "started": "شدو فعال شد و State حفظ شد.", "stopped_ok": "شدو با حفظ State متوقف شد.",
        "restarted": "شدو با State قبلی دوباره فعال شد.", "start_failed": "خطا در شروع",
        "stop_failed": "خطا در توقف", "restart_failed": "خطا در راه‌اندازی مجدد",
        "worker_note": "مرورگر می‌تواند بسته شود؛ تا وقتی لپ‌تاپ روشن است پردازش ادامه دارد.",
        "light_mode": "حالت روشن", "data_view": "کانال داده", "shadow": "شدو", "paper": "پیپر",
        "paper_only": "محیط شبیه‌سازی // بدون سفارش واقعی در صرافی",
        "tagline": "ترمینال کوانت رترو // آشوب بازار، اما با داده",
        "latest_trades": "تابلو آخرین معاملات", "no_trades": "هنوز معامله پیپر ثبت نشده",
        "no_trades_note": "شدو در حال رصد است؛ دوج قضاوت می‌کند؛ سرمایه امن است.",
        "gate": "گیت", "passed": "پاس شده", "pending": "در انتظار", "elapsed": "زمان سپری‌شده",
        "days": "روز", "decisions": "تصمیم یکتا", "candles": "کندل کامل ۴ساعته",
        "fresh": "تازگی منابع", "handled": "خطای مهارشده", "crashes": "کرش مهارنشده",
        "gate_matrix": "ماتریس گیت شدو", "check": "شرط", "status": "وضعیت",
        "trade_log": "لاگ معامله / تصمیم", "equity": "منحنی سرمایه",
        "attribution": "تفکیک عملکرد", "regime": "نقشه حرارتی رژیم بازار",
        "export": "خروجی گزارش", "excel": "دریافت اکسل", "pdf": "دریافت PDF",
        "equity_wait": "پس از ثبت معامله پیپر، منحنی سرمایه نمایش داده می‌شود.",
        "attr_wait": "پس از ثبت معامله پیپر، تفکیک عملکرد نمایش داده می‌شود.",
        "regime_wait": "هنوز تصمیم دارای برچسب رژیم بازار ثبت نشده است.",
    },
}

CHECK_LABELS = {
    "minimum_days": ("7-day runtime", "اجرای هفت‌روزه"),
    "minimum_unique_decisions": ("Unique decisions", "تصمیم‌های یکتا"),
    "minimum_complete_4h_candles": ("Complete 4h candles", "کندل‌های کامل ۴ساعته"),
    "duplicates": ("Zero duplicate executions", "صفر اجرای تکراری"),
    "open_candles": ("Zero open-candle decisions", "صفر تصمیم روی کندل باز"),
    "state": ("Zero state corruption", "صفر خرابی State"),
    "crashes": ("Zero unhandled crashes", "صفر کرش مهارنشده"),
    "provider_freshness": ("Provider freshness", "تازگی منابع"),
}


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


def _inject_theme(light: bool) -> None:
    palette = {
        "bg": "#f5f0fa" if light else "#07060d",
        "panel": "rgba(255,255,255,.88)" if light else "rgba(14,10,25,.88)",
        "panel2": "#eee5f7" if light else "#100b1d",
        "text": "#21162c" if light else "#f7f2ff",
        "muted": "#665b72" if light else "#aaa0b9",
        "grid": "rgba(115,52,160,.09)" if light else "rgba(157,72,255,.08)",
        "shadow": "rgba(62,24,84,.15)" if light else "rgba(0,0,0,.46)",
    }
    st.markdown(
        f"""
        <style>
        :root {{ --bg:{palette['bg']}; --panel:{palette['panel']}; --panel2:{palette['panel2']};
          --text:{palette['text']}; --muted:{palette['muted']}; --orange:#ff911f; --purple:#a855f7;
          --cyan:#48e5ff; --profit:#2ee59d; --loss:#ff4778; --warning:#ffb020; --neutral:#8b7aa8; }}
        .stApp {{ color:var(--text); background-color:var(--bg); background-image:
          linear-gradient({palette['grid']} 1px, transparent 1px),
          linear-gradient(90deg, {palette['grid']} 1px, transparent 1px); background-size:32px 32px; }}
        .stApp::before {{ content:""; position:fixed; inset:0; pointer-events:none; z-index:999;
          background:repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(0,0,0,.035) 4px); }}
        [data-testid="stSidebar"] {{ background:var(--panel2); border-right:1px solid rgba(168,85,247,.35); }}
        [data-testid="stSidebar"] * {{ color:var(--text); }}
        [data-testid="stHeader"] {{ background:transparent; }}
        .block-container {{ max-width:1500px; padding-top:1.35rem; padding-bottom:3rem; }}
        div[data-testid="stMetric"] {{ background:var(--panel); border:1px solid rgba(168,85,247,.28);
          border-left:3px solid var(--orange); padding:.72rem .8rem; box-shadow:0 8px 24px {palette['shadow']}; }}
        div[data-testid="stMetricLabel"] {{ color:var(--muted); letter-spacing:.08em; text-transform:uppercase; }}
        div[data-testid="stMetricValue"] {{ color:var(--text); }}
        .stButton button, .stDownloadButton button {{ border-radius:3px; border:1px solid var(--purple);
          background:linear-gradient(135deg,rgba(168,85,247,.18),rgba(255,145,31,.12)); color:var(--text);
          font-weight:700; letter-spacing:.04em; box-shadow:0 0 14px rgba(168,85,247,.10); }}
        .stButton button:hover, .stDownloadButton button:hover {{ border-color:var(--orange); color:var(--orange);
          box-shadow:0 0 18px rgba(255,145,31,.28); transform:translateY(-1px); }}
        [data-testid="stDataFrame"] {{ border:1px solid rgba(72,229,255,.24); box-shadow:0 0 22px rgba(72,229,255,.06); }}
        .freakto-brand {{ position:relative; overflow:hidden; display:flex; align-items:center; gap:1.35rem;
          padding:1.15rem 1.35rem; margin-bottom:1rem; border:1px solid rgba(255,145,31,.42);
          background:linear-gradient(110deg,var(--panel),rgba(96,34,139,.18)); clip-path:polygon(0 0,97% 0,100% 28%,100% 100%,3% 100%,0 72%);
          box-shadow:0 12px 34px {palette['shadow']}, inset 0 0 25px rgba(168,85,247,.06); }}
        .freakto-brand::after {{ content:"FREAKTO // NODE 01 // SIGNAL LOCK"; position:absolute; right:1.2rem; bottom:.45rem;
          font:600 .58rem monospace; letter-spacing:.14em; color:rgba(72,229,255,.58); }}
        .logo-shell {{ position:relative; width:104px; height:104px; flex:0 0 104px; }}
        .freakto-logo {{ width:100%; height:100%; object-fit:cover; border-radius:50%; border:3px solid var(--orange);
          box-shadow:0 0 12px rgba(255,145,31,.75),0 0 30px rgba(168,85,247,.40); animation:logoFlux 4s ease-in-out infinite; }}
        .logo-shell::before,.logo-shell::after {{ content:""; position:absolute; inset:-7px; border-radius:50%;
          border:1px dashed var(--cyan); animation:orbit 9s linear infinite; }}
        .logo-shell::after {{ inset:-12px; border-color:rgba(168,85,247,.55); animation-direction:reverse; animation-duration:13s; }}
        .freakto-copy h1 {{ margin:0; padding:0; color:var(--text); font-size:2.2rem; letter-spacing:.025em;
          text-shadow:2px 0 rgba(72,229,255,.22),-2px 0 rgba(255,71,120,.18); }}
        .freakto-tagline {{ margin-top:.42rem; color:var(--cyan); font:600 .82rem monospace; letter-spacing:.07em; }}
        .freakto-powered {{ margin-top:.72rem; color:var(--orange); font:800 .72rem monospace; letter-spacing:.19em; }}
        .worker-status {{ padding:.72rem .8rem; margin:.45rem 0 .8rem; border:1px solid var(--neutral); color:var(--muted);
          background:rgba(139,122,168,.08); font:800 .78rem monospace; letter-spacing:.12em; text-align:center; }}
        .worker-status.running {{ color:var(--profit); border-color:var(--profit); background:rgba(46,229,157,.08);
          box-shadow:0 0 18px rgba(46,229,157,.22); animation:statusPulse 1.6s ease-in-out infinite; }}
        .section-title {{ display:flex; align-items:center; gap:.7rem; margin:1.45rem 0 .72rem; color:var(--text);
          font:800 1rem monospace; letter-spacing:.1em; text-transform:uppercase; }}
        .section-title::before {{ content:""; width:7px; height:20px; background:var(--orange); box-shadow:0 0 11px var(--orange); }}
        .trade-board {{ position:relative; overflow:hidden; border:1px solid rgba(72,229,255,.42); background:var(--panel);
          box-shadow:0 0 25px rgba(72,229,255,.08); }}
        .trade-ticker {{ overflow:hidden; white-space:nowrap; padding:.67rem 0; border-bottom:1px solid rgba(168,85,247,.28);
          color:var(--cyan); font:700 .76rem monospace; }}
        .trade-ticker span {{ display:inline-block; padding-left:100%; animation:ticker 28s linear infinite; }}
        .trade-row {{ display:grid; grid-template-columns:1.35fr .7fr 1fr 1fr 1fr; gap:.75rem; padding:.62rem .85rem;
          border-bottom:1px solid rgba(139,122,168,.13); font:.78rem monospace; }}
        .trade-row:last-child {{ border-bottom:0; }} .trade-side.buy {{ color:var(--cyan); }}
        .trade-side.sell,.tone-profit {{ color:var(--profit); }} .tone-loss {{ color:var(--loss); }}
        .empty-board {{ padding:1.45rem; text-align:center; color:var(--muted); }}
        .empty-board strong {{ display:block; color:var(--warning); font:800 1rem monospace; margin-bottom:.35rem; }}
        @keyframes statusPulse {{ 50% {{ box-shadow:0 0 28px rgba(46,229,157,.48); filter:brightness(1.18); }} }}
        @keyframes logoFlux {{ 50% {{ box-shadow:0 0 20px rgba(255,145,31,.9),0 0 40px rgba(168,85,247,.52); transform:scale(1.025); }} }}
        @keyframes orbit {{ to {{ transform:rotate(360deg); }} }}
        @keyframes ticker {{ to {{ transform:translateX(-100%); }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _brand_header(t: dict[str, str], language: str) -> None:
    direction = "rtl" if language == "FA" else "ltr"
    st.markdown(
        f"""
        <div class="freakto-brand">
          <div class="logo-shell"><img class="freakto-logo" src="{_logo_data_uri()}" alt="Freakto logo"></div>
          <div class="freakto-copy" dir="{direction}">
            <h1>Freakto Shadow / Paper</h1>
            <div class="freakto-tagline">{html.escape(t['tagline'])}</div>
            <div class="freakto-powered">POWERED BY ALAVI</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section_title(label: str) -> None:
    st.markdown(f'<div class="section-title">{html.escape(label)}</div>', unsafe_allow_html=True)


def _display(value: Any, digits: int = 4) -> str:
    try:
        number = float(value)
        if pd.isna(number):
            return "—"
        return f"{number:,.{digits}f}"
    except (TypeError, ValueError):
        return html.escape(str(value or "—"))


def _latest_trade_board(fills: pd.DataFrame, t: dict[str, str]) -> None:
    _section_title(t["latest_trades"])
    if fills.empty:
        st.markdown(
            f'<div class="trade-board"><div class="trade-ticker"><span>FREAKTO // SHADOW SCAN ACTIVE // '
            f'NO CAPITAL AT RISK // WAITING FOR PAPER GATE //</span></div><div class="empty-board">'
            f'<strong>{html.escape(t["no_trades"])}</strong>{html.escape(t["no_trades_note"])}</div></div>',
            unsafe_allow_html=True,
        )
        return
    latest = fills.copy()
    if "timestamp_utc" in latest.columns:
        latest = latest.sort_values("timestamp_utc")
    if "equity_usdt" in latest.columns:
        latest["_equity_delta"] = pd.to_numeric(latest["equity_usdt"], errors="coerce").diff()
    if "timestamp_utc" in latest.columns:
        latest = latest.sort_values("timestamp_utc", ascending=False)
    latest = latest.head(8)
    ticker_items = []
    rows = []
    for _, row in latest.iterrows():
        symbol = html.escape(str(row.get("symbol", "—")))
        side = html.escape(str(row.get("side", "—")).upper())
        price = _display(row.get("execution_price"))
        amount = _display(row.get("amount"), 6)
        equity = row.get("equity_usdt")
        tone = ""
        try:
            equity_delta = float(row.get("_equity_delta"))
            if not pd.isna(equity_delta):
                tone = "tone-profit" if equity_delta >= 0 else "tone-loss"
        except (TypeError, ValueError):
            pass
        timestamp = html.escape(str(row.get("timestamp_utc", "—")))[:19].replace("T", " ")
        ticker_items.append(f"{side} {symbol} @ {price}")
        rows.append(
            f'<div class="trade-row"><span>{timestamp}</span><span class="trade-side {side.lower()}">{side}</span>'
            f'<span>{symbol}</span><span>${price}</span><span class="{tone}">${_display(equity, 2)} · {amount}</span></div>'
        )
    ticker = " &nbsp; ◆ &nbsp; ".join(ticker_items)
    st.markdown(
        f'<div class="trade-board"><div class="trade-ticker"><span>{ticker}</span></div>{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Freakto Shadow / Paper", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
    config = load_runtime_config(CONFIG_PATH)
    controller = ShadowProcessController(PROJECT_ROOT, config.state_roots["shadow"])
    status = controller.status()

    with st.sidebar:
        language = st.selectbox("LANGUAGE / زبان", ["EN", "FA"], key="ui_language")
        t = TEXT[language]
        light = st.toggle(t["light_mode"], key="light_mode")
        st.markdown(f'<div class="section-title">{html.escape(t["control"])}</div>', unsafe_allow_html=True)
        state_class = "running" if status.running else "stopped"
        state_text = f'{t["running"]} · PID {status.pid}' if status.running else t["stopped"]
        st.markdown(f'<div class="worker-status {state_class}">{html.escape(state_text)}</div>', unsafe_allow_html=True)
        groups = st.selectbox(t["universe"], ["core", "core,growth", "all"], index=0, disabled=status.running)
        interval = st.number_input(t["interval"], min_value=60, max_value=3600, value=300, step=60, disabled=status.running)
        left, middle, right = st.columns(3)
        if left.button(t["start"], disabled=status.running, use_container_width=True):
            try:
                controller.start(groups=groups, interval_seconds=float(interval))
                st.success(t["started"])
                _refresh()
            except Exception as exc:
                st.error(f'{t["start_failed"]}: {type(exc).__name__}: {exc}')
        if middle.button(t["stop"], disabled=not status.running, use_container_width=True):
            try:
                controller.stop()
                st.success(t["stopped_ok"])
                _refresh()
            except Exception as exc:
                st.error(f'{t["stop_failed"]}: {type(exc).__name__}: {exc}')
        if right.button(t["restart"], disabled=not status.running, use_container_width=True):
            try:
                controller.restart(groups=status.groups, interval_seconds=status.interval_seconds)
                st.success(t["restarted"])
                _refresh()
            except Exception as exc:
                st.error(f'{t["restart_failed"]}: {type(exc).__name__}: {exc}')
        if st.button(t["refresh"], use_container_width=True):
            _refresh()
        st.caption(t["worker_note"])

    _inject_theme(light)
    _brand_header(t, language)
    st.caption(t["paper_only"])

    mode = st.radio(t["data_view"], ["shadow", "paper"], format_func=lambda value: t[value], horizontal=True)
    data = _data(mode)
    metrics = data.state.get("metrics", {})
    cols = st.columns(7)
    values = [
        (t["gate"], t["passed"] if data.gate.get("passed") else t["pending"]),
        (t["elapsed"], f'{data.gate.get("days", 0):.2f} {t["days"]}'),
        (t["decisions"], metrics.get("unique_decisions", 0)),
        (t["candles"], metrics.get("complete_4h_candles", 0)),
        (t["fresh"], f'{data.gate.get("provider_freshness_pct", 0):.1f}%'),
        (t["handled"], metrics.get("handled_symbol_failures", 0)),
        (t["crashes"], metrics.get("unhandled_crashes", 0)),
    ]
    for column, (label, value) in zip(cols, values):
        column.metric(label, value)

    _latest_trade_board(_data("paper").fills, t)

    _section_title(t["gate_matrix"])
    label_index = 1 if language == "FA" else 0
    checks = pd.DataFrame([
        {t["check"]: CHECK_LABELS.get(name, (name, name))[label_index], t["status"]: "✓ PASS" if passed else "✕ WAIT"}
        for name, passed in data.gate.get("checks", {}).items()
    ])
    st.dataframe(checks, use_container_width=True, hide_index=True)

    _section_title(t["trade_log"])
    st.dataframe(data.fills if not data.fills.empty else data.intents, use_container_width=True, hide_index=True)

    left, right = st.columns(2)
    curve = equity_curve(data)
    with left:
        _section_title(t["equity"])
        if curve.empty:
            st.info(t["equity_wait"])
        else:
            st.line_chart(curve.set_index("timestamp_utc")["equity_usdt"], color="#ff911f")
    with right:
        _section_title(t["attribution"])
        attribution = performance_attribution(data)
        if attribution.empty:
            st.info(t["attr_wait"])
        else:
            st.dataframe(attribution, use_container_width=True, hide_index=True)

    _section_title(t["regime"])
    heatmap = regime_heatmap(data)
    if heatmap.empty:
        st.info(t["regime_wait"])
    else:
        st.dataframe(heatmap.style.background_gradient(cmap="magma"), use_container_width=True)

    _section_title(t["export"])
    export_left, export_right = st.columns(2)
    export_left.download_button(t["excel"], excel_report(data), f"freakto_{mode}_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    export_right.download_button(t["pdf"], pdf_report(data), f"freakto_{mode}_report.pdf", "application/pdf", use_container_width=True)


if __name__ == "__main__":
    main()
