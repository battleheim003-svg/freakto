"""Bilingual unified Streamlit control center for Freakto."""

from __future__ import annotations

import html

import streamlit as st

from freakto.paper.campaign import ACTIVE as CAMPAIGN_ACTIVE
from freakto.paper.campaign import campaign_status, start_campaign, stop_campaign
from freakto.ui.control_center_state import (
    ROOT,
    collect_snapshot,
    run_cli,
)
from freakto.ui.job_manager import (
    ACTIVE,
    TERMINAL,
    job_log,
    list_jobs,
    request_cancel,
    retry_job,
    start_quick_job,
    start_workflow_job,
)


st.set_page_config(page_title="Freakto Control Center", page_icon="⚡", layout="wide")

TEXT = {
    "fa": {
        "language": "زبان / Language", "nav": "مرکز مدیریت", "overview": "نمای کلی",
        "data": "داده و Replay", "paper": "Paper Trading", "reports": "گزارش‌ها",
        "golive": "Go-live", "jobs": "اجراها و لاگ‌ها", "guide": "راهنمای اجرا", "refresh": "بروزرسانی وضعیت",
        "safe": "سرمایه واقعی صفر — حالت ایمن", "safe_note": "هیچ عملیات واقعی صرافی از این پنل قابل فعال‌سازی نیست.",
        "title": "مرکز کنترل Freakto", "subtitle": "مدیریت یکپارچه پژوهش، بازپخش، Paper و آمادگی عملیاتی",
        "capital": "وضعیت سرمایه", "zero": "ایمن / صفر", "datasets": "دیتاست‌های بازار",
        "paper_mode": "حالت Paper", "review": "بررسی Go-live", "blocked": "مسدود",
        "reviewable": "قابل بررسی", "no_data": "هنوز دیتایی پیدا نشد", "armed": "فعال",
        "disarmed": "متوقف", "quick_title": "شروع سریع هوشمند", "quick_desc": "این دکمه مسیر کامل را به‌ترتیب اجرا می‌کند؛ روی اولین خطای واقعی متوقف می‌شود و نتیجه هر مرحله را نگه می‌دارد.",
        "full_pipeline": "ساخت/بروزرسانی داده و اجرای Replay کامل هم انجام شود", "confirm_quick": "تأیید می‌کنم این فرآیند ممکن است طولانی باشد و فقط Paper/Research اجرا می‌کند.",
        "quick_button": "شروع مسیر کامل", "quick_running": "در حال اجرای مسیر امن…", "step": "مرحله",
        "command": "فرمان", "result": "نتیجه", "success": "موفق", "stopped": "متوقف شد",
        "safe_block": "مسدود ایمن", "pending": "در انتظار", "quick_done": "مسیر تا آخرین مرحله مجاز اجرا شد.",
        "quick_failed": "مسیر در این مرحله متوقف شد؛ خروجی را بررسی کن.", "recommended": "ترتیب: Data → Replay → Preflight → Arm Research → Cycle → Reports → Go-live check",
        "data_title": "داده و بازپخش تاریخی", "data_note": "فرمان‌های وضعیت read-only هستند. عملیات ساخت و Replay ممکن است زمان‌بر باشند.",
        "data_files": "فایل‌های دیتای بازار", "data_status": "وضعیت داده", "replay_status": "وضعیت Replay",
        "heavy": "عملیات سنگین", "build_confirm": "ساخت داده به اینترنت و زمان نیاز دارد", "build": "ساخت / بروزرسانی داده",
        "replay_confirm": "اجرای Replay روی دیتای موجود را تأیید می‌کنم", "replay_run": "اجرای Replay",
        "paper_title": "Paper Trading — بدون سرمایه واقعی", "live_orders": "سفارش واقعی", "off": "خاموش",
        "unavailable": "از این داشبورد قابل فعال‌سازی نیست", "allocation": "تخصیص سرمایه", "preflight": "بررسی اولیه",
        "arm_research": "فعال‌سازی Research", "one_cycle": "اجرای یک چرخه", "status": "نمایش وضعیت",
        "safe_stop": "توقف ایمن", "stop_confirm": "توقف Paper و ثبت operator stop را تأیید می‌کنم", "disarm": "توقف Paper",
        "strategy_note": "Strategy Paper فقط پس از عبور readiness فعال می‌شود و همچنان صفرسرمایه است.",
        "strategy_confirm": "درخواست Strategy Paper را تأیید می‌کنم", "arm_strategy": "فعال‌سازی Strategy Paper",
        "campaign_title": "کمپین واقعی ۶۰روزه", "campaign_status": "وضعیت کمپین", "campaign_days": "روز سپری‌شده",
        "campaign_trades": "معاملات بسته", "campaign_cycles": "چرخه‌ها", "campaign_target": "پایان هدف",
        "campaign_start": "شروع / ادامه کمپین", "campaign_stop": "توقف امن کمپین", "campaign_started": "کمپین پس‌زمینه فعال شد.",
        "campaign_stop_requested": "درخواست توقف ثبت شد و پس از مرحله جاری اعمال می‌شود.", "campaign_confirm": "قرارداد ۶۰روزه و اجرای صفرسرمایه را تأیید می‌کنم.",
        "reports_title": "گزارش‌ها و خروجی‌ها", "paper_report": "گزارش Paper", "research_report": "گزارش Research",
        "forward_report": "وضعیت Forward", "artifacts": "خروجی‌های Runtime", "no_artifacts": "هنوز خروجی JSON ثبت نشده",
        "golive_title": "گیت آمادگی نهایی", "remaining": "مانع باقی مانده", "manual_only": "تمام گیت‌ها عبور کرده‌اند؛ فقط بررسی دستی مستقل مجاز است.",
        "never_live": "عبور از این گیت هرگز سفارش واقعی را فعال نمی‌کند.", "gate": "گیت", "current": "مقدار فعلی", "required": "حد لازم",
        "rerun_golive": "اجرای دوباره Go-live check", "guide_title": "نقشه ساده اجرای پروژه",
        "guide_body": "**۱. داده:** cache را بررسی و تکمیل کن.\n\n**۲. Replay:** استراتژی را روی تاریخ با قوانین causal اجرا کن.\n\n**۳. Preflight:** آمادگی محیط Paper را بسنج.\n\n**۴. Arm Research:** مشاهده‌های واقعی بازار را بدون سفارش ثبت کن.\n\n**۵. Cycle و Reports:** چرخه را اجرا و نتایج را ارزیابی کن.\n\n**۶. Go-live:** پس از حداقل ۶۰ روز و ۲۰۰ معامله، evidence را بررسی کن.\n\n**قانون طلایی:** «قابل بررسی» هم مجوز معامله واقعی نیست.",
        "running": "در حال اجرا", "exit_ok": "فرمان با موفقیت تمام شد", "exit_blocked": "فرمان طبق قرارداد ایمنی مسدود شد",
        "exit_failed": "اجرای فرمان ناموفق بود", "last_output": "آخرین خروجی فرمان",
        "job_started": "اجرای پس‌زمینه شروع شد", "job_exists": "یک اجرای فعال از قبل وجود دارد", "jobs_title": "مدیریت اجراهای پس‌زمینه",
        "jobs_note": "Quick Start در پس‌زمینه ادامه می‌یابد؛ بستن مرورگر آن را متوقف نمی‌کند.", "no_jobs": "هنوز اجرایی ثبت نشده است.",
        "job_id": "شناسه اجرا", "job_status": "وضعیت", "progress": "پیشرفت", "created": "زمان ایجاد", "current_step": "مرحله فعلی",
        "select_job": "انتخاب اجرا", "cancel": "لغو پس از مرحله فعلی", "retry": "اجرای دوباره", "log": "لاگ اجرا",
        "cancelled_requested": "درخواست لغو ثبت شد؛ پس از پایان مرحله جاری متوقف می‌شود.", "retried": "اجرای مجدد شروع شد.",
    },
    "en": {
        "language": "Language / زبان", "nav": "Management center", "overview": "Overview",
        "data": "Data & Replay", "paper": "Paper Trading", "reports": "Reports",
        "golive": "Go-live", "jobs": "Jobs & logs", "guide": "Run guide", "refresh": "Refresh status",
        "safe": "ZERO REAL CAPITAL — SAFE MODE", "safe_note": "Real exchange execution cannot be enabled from this panel.",
        "title": "Freakto Control Center", "subtitle": "Unified research, replay, Paper, and operational-readiness management",
        "capital": "Capital status", "zero": "Safe / zero", "datasets": "Market datasets",
        "paper_mode": "Paper mode", "review": "Go-live review", "blocked": "Blocked",
        "reviewable": "Reviewable", "no_data": "No market data found", "armed": "Armed",
        "disarmed": "Disarmed", "quick_title": "Smart quick start", "quick_desc": "Runs the complete workflow in order, stops on the first real failure, and preserves every step result.",
        "full_pipeline": "Also build/update data and run the full Replay", "confirm_quick": "I understand this can take a long time and remains Research/Paper only.",
        "quick_button": "Start complete workflow", "quick_running": "Running safe workflow…", "step": "Step",
        "command": "Command", "result": "Result", "success": "Passed", "stopped": "Stopped",
        "safe_block": "Safe block", "pending": "Pending", "quick_done": "Workflow reached the final permitted step.",
        "quick_failed": "Workflow stopped here; inspect the output below.", "recommended": "Order: Data → Replay → Preflight → Arm Research → Cycle → Reports → Go-live check",
        "data_title": "Historical data and Replay", "data_note": "Status commands are read-only. Data builds and Replay can take significant time.",
        "data_files": "Market data files", "data_status": "Data status", "replay_status": "Replay status",
        "heavy": "Long-running operations", "build_confirm": "I understand data building needs network access and time", "build": "Build / update data",
        "replay_confirm": "I confirm Replay should run on cached data", "replay_run": "Run Replay",
        "paper_title": "Paper Trading — zero real capital", "live_orders": "Live orders", "off": "OFF",
        "unavailable": "Cannot be enabled from this dashboard", "allocation": "Capital allocation", "preflight": "Preflight",
        "arm_research": "Arm Research", "one_cycle": "Run one cycle", "status": "Show status",
        "safe_stop": "Safe stop", "stop_confirm": "I confirm Paper disarm and operator-stop recording", "disarm": "Disarm Paper",
        "strategy_note": "Strategy Paper requires readiness and still remains zero-capital.",
        "strategy_confirm": "I confirm the Strategy Paper request", "arm_strategy": "Arm Strategy Paper",
        "campaign_title": "Real 60-day campaign", "campaign_status": "Campaign status", "campaign_days": "Elapsed days",
        "campaign_trades": "Closed trades", "campaign_cycles": "Cycles", "campaign_target": "Target end",
        "campaign_start": "Start / resume campaign", "campaign_stop": "Safely stop campaign", "campaign_started": "Background campaign started.",
        "campaign_stop_requested": "Stop requested and will apply after the current step.", "campaign_confirm": "I confirm the 60-day zero-capital campaign contract.",
        "reports_title": "Reports and outputs", "paper_report": "Paper report", "research_report": "Research report",
        "forward_report": "Forward status", "artifacts": "Runtime artifacts", "no_artifacts": "No JSON artifacts yet",
        "golive_title": "Final readiness gate", "remaining": "blockers remaining", "manual_only": "All gates passed; independent manual review is the only permitted next step.",
        "never_live": "Passing this gate never enables real orders.", "gate": "Gate", "current": "Current", "required": "Required",
        "rerun_golive": "Run Go-live check again", "guide_title": "Simple project run map",
        "guide_body": "**1. Data:** inspect and complete the cache.\n\n**2. Replay:** run the strategy historically under causal rules.\n\n**3. Preflight:** verify the Paper environment.\n\n**4. Arm Research:** collect live observations without orders.\n\n**5. Cycle and Reports:** run a cycle and evaluate results.\n\n**6. Go-live:** after at least 60 days and 200 trades, evaluate evidence.\n\n**Golden rule:** Reviewable never means authorized for live trading.",
        "running": "Running", "exit_ok": "Command completed successfully", "exit_blocked": "Command was safely blocked by policy",
        "exit_failed": "Command failed", "last_output": "Latest command output",
        "job_started": "Background job started", "job_exists": "Another job is already active", "jobs_title": "Background job manager",
        "jobs_note": "Quick Start continues in the background; closing the browser does not stop it.", "no_jobs": "No jobs recorded yet.",
        "job_id": "Job ID", "job_status": "Status", "progress": "Progress", "created": "Created", "current_step": "Current step",
        "select_job": "Select job", "cancel": "Cancel after current step", "retry": "Retry job", "log": "Job log",
        "cancelled_requested": "Cancellation requested; the job will stop after its current step.", "retried": "Retry started.",
    },
}

TEXT["fa"].update(
    {
        "market": "بازارهای جدید",
        "forward": "Forward و Shadow",
        "airdrop": "Airdrop Radar",
        "cross_asset": "رتبه‌بندی بین‌بازاری",
        "market_title": "کنترل بازارهای فارکس و طلا",
        "market_note": "ممیزی داده و Replay در jobهای مستقل اجرا می‌شوند؛ هسته و Decision Engine فقط مصرف‌کننده داده معتبر باقی می‌مانند.",
        "adapter_manifests": "Manifestهای ممیزی‌شده",
        "audit_range": "بازه ممیزی UTC",
        "start_date": "تاریخ شروع",
        "end_date": "تاریخ پایان انحصاری",
        "audit_confirm": "اجرای ممیزی EUR/USD و XAU/USD را تأیید می‌کنم",
        "start_audit": "شروع ممیزی داده بازار",
        "market_replay_confirm": "Replay تحقیقاتی با هزینه‌های ممیزی‌شده را تأیید می‌کنم",
        "start_market_replay": "شروع Replay فارکس و طلا",
        "forward_title": "کنترل Forward و Shadow",
        "forward_note": "هر چرخه Preflight، Research Arm، یک چرخه مشاهده و گزارش Forward را به‌ترتیب اجرا می‌کند. خروجی blocked یک توقف ایمن است.",
        "last_forward": "آخرین گزارش Forward",
        "forward_confirm": "اجرای یک چرخه صفرسرمایه Forward/Shadow را تأیید می‌کنم",
        "start_forward": "شروع چرخه Forward/Shadow",
        "airdrop_title": "کنترل Outcomeهای Airdrop",
        "airdrop_note": "Sync فقط snapshotهای موجود را وارد می‌کند و بدون دیتابیس Radar با وضعیت SYNC_BLOCKED متوقف می‌شود؛ هیچ outcome ساخته نمی‌شود.",
        "tracker_db": "دیتابیس Outcome",
        "airdrop_confirm": "Sync و گزارش evidence را تأیید می‌کنم",
        "start_airdrop": "شروع Sync و گزارش Airdrop",
        "cross_title": "کنترل رتبه‌بندی Cross-Asset",
        "cross_note": "فقط CSVهای داخل workspace پذیرفته می‌شوند. Ranker هیچ تصمیم معاملاتی به موتور ارسال نمی‌کند.",
        "opportunity_csv": "CSV فرصت‌های استانداردشده",
        "rankings_csv": "CSV رتبه‌بندی‌ها",
        "outcomes_csv": "CSV outcomeهای مشاهده‌شده",
        "rank_confirm": "قرارداد داده و اجرای Research-only Rank را تأیید می‌کنم",
        "start_rank": "شروع رتبه‌بندی",
        "evaluate_confirm": "ارزیابی causal رتبه‌بندی‌ها را تأیید می‌کنم",
        "start_evaluate": "شروع ارزیابی تاریخی",
        "workflow_started": "Job بخش شروع شد",
        "workflow_blocked": "شروع Job به‌صورت ایمن مسدود شد",
        "one_at_time": "برای جلوگیری از تداخل فایل‌ها، در هر لحظه فقط یک job پس‌زمینه اجرا می‌شود.",
        "kind": "بخش",
    }
)
TEXT["en"].update(
    {
        "market": "New Markets",
        "forward": "Forward & Shadow",
        "airdrop": "Airdrop Radar",
        "cross_asset": "Cross-Asset Ranking",
        "market_title": "Forex and gold controls",
        "market_note": "Data audit and Replay run as isolated jobs; the core and Decision Engine remain unchanged consumers of validated data.",
        "adapter_manifests": "Audited manifests",
        "audit_range": "UTC audit range",
        "start_date": "Start date",
        "end_date": "Exclusive end date",
        "audit_confirm": "I confirm the EUR/USD and XAU/USD data audit",
        "start_audit": "Start market data audit",
        "market_replay_confirm": "I confirm research Replay with audited cost inputs",
        "start_market_replay": "Start forex and gold Replay",
        "forward_title": "Forward and Shadow controls",
        "forward_note": "Each cycle runs Preflight, Research Arm, one observation cycle, and Forward reporting in order. A blocked result is a safe stop.",
        "last_forward": "Latest Forward report",
        "forward_confirm": "I confirm one zero-capital Forward/Shadow cycle",
        "start_forward": "Start Forward/Shadow cycle",
        "airdrop_title": "Airdrop outcome controls",
        "airdrop_note": "Sync imports existing snapshots only and returns SYNC_BLOCKED without a Radar database; it never fabricates outcomes.",
        "tracker_db": "Outcome database",
        "airdrop_confirm": "I confirm evidence sync and reporting",
        "start_airdrop": "Start Airdrop sync and report",
        "cross_title": "Cross-Asset ranker controls",
        "cross_note": "Only CSV files inside the workspace are accepted. The ranker never emits a Decision Engine action.",
        "opportunity_csv": "Standardized opportunities CSV",
        "rankings_csv": "Rankings CSV",
        "outcomes_csv": "Observed outcomes CSV",
        "rank_confirm": "I confirm the data contract and research-only ranking run",
        "start_rank": "Start ranking",
        "evaluate_confirm": "I confirm causal ranking evaluation",
        "start_evaluate": "Start historical evaluation",
        "workflow_started": "Section job started",
        "workflow_blocked": "Job launch was safely blocked",
        "one_at_time": "Only one background job runs at a time to prevent artifact conflicts.",
        "kind": "Area",
    }
)


def tr(key: str) -> str:
    return TEXT[st.session_state.get("language", "fa")][key]


def inject_style(rtl: bool) -> None:
    direction = "rtl" if rtl else "ltr"
    align = "right" if rtl else "left"
    st.markdown(
        f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Vazirmatn:wght@400;500;600;700;800&display=swap');
.stApp {{ background: radial-gradient(circle at 80% 0%, #14283c 0, #08111c 35%, #050b12 75%); color:#e8f3fa; }}
.main .block-container {{ max-width:1400px; padding-top:1.6rem; }}
[data-testid="stSidebar"] {{ background:linear-gradient(180deg,#0a1723,#07101a); border-right:1px solid #19364a; }}
[data-testid="stSidebar"] * {{ direction:{direction}; text-align:{align}; }}
.dashboard {{ direction:{direction}; text-align:{align}; font-family:{'Vazirmatn' if rtl else 'Inter'},sans-serif; }}
.hero {{ position:relative; overflow:hidden; padding:1.65rem 1.8rem; border:1px solid #24475d; border-radius:24px;
background:linear-gradient(115deg,rgba(13,42,59,.96),rgba(14,27,44,.96) 55%,rgba(37,25,58,.9)); box-shadow:0 24px 70px rgba(0,0,0,.28); margin-bottom:1.1rem; }}
.hero:after {{ content:''; position:absolute; width:280px; height:280px; border-radius:50%; background:#27d7c51c; top:-170px; right:8%; box-shadow:0 0 90px #27d7c544; }}
.eyebrow {{ color:#47ddcf; font-size:.74rem; letter-spacing:.16em; font-weight:800; }}
.hero h1 {{ margin:.35rem 0 .25rem; color:#f5fbff; font-size:2.15rem; }} .hero p {{ margin:0;color:#9bb3c3; }}
.safe-pill {{ display:inline-flex; margin-top:.85rem; color:#7df5b0; background:#0d3024; border:1px solid #245e45; padding:.32rem .7rem; border-radius:999px; font-weight:700; font-size:.75rem; }}
.metric-card {{ padding:1.05rem 1.1rem; min-height:132px; border-radius:18px; background:linear-gradient(145deg,#0d1d29,#0a151f); border:1px solid #1b394c; box-shadow:0 12px 35px rgba(0,0,0,.18); }}
.metric-label {{ color:#7190a3; font-size:.72rem; text-transform:uppercase; letter-spacing:.12em; }}
.metric-value {{ color:#f4fbff; font-size:1.55rem; font-weight:800; margin:.48rem 0 .3rem; }} .metric-note {{ color:#88a4b5; font-size:.78rem; word-break:break-word; }}
.good {{ color:#74efaa; }} .bad {{ color:#ff9c9c; }}
.quick-box {{ padding:1.25rem 1.35rem; border:1px solid #28596d; border-radius:20px; background:linear-gradient(120deg,#0d2431,#101c2c); margin:1rem 0; }}
.quick-box h3 {{ color:#65e4d8; margin:0 0 .25rem; }} .quick-box p {{ color:#96afbf; margin:0; }}
div[data-testid="stButton"] button {{ border-radius:12px; border:1px solid #2a566d; min-height:2.7rem; font-weight:700; }}
div[data-testid="stButton"] button[kind="primary"] {{ background:linear-gradient(90deg,#0c8e88,#176b96); border:0; box-shadow:0 8px 25px #087d7544; }}
div[data-testid="stDataFrame"] {{ border:1px solid #1d3b4d; border-radius:14px; overflow:hidden; }}
</style>
""",
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, note: str = "", css: str = "") -> None:
    st.markdown(
        f'<div class="metric-card dashboard"><div class="metric-label">{html.escape(label)}</div>'
        f'<div class="metric-value {css}">{html.escape(value)}</div><div class="metric-note">{html.escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


def execute(label: str, arguments: list[str], *, key: str, primary: bool = False, disabled: bool = False) -> None:
    if st.button(label, key=key, type="primary" if primary else "secondary", use_container_width=True, disabled=disabled):
        with st.spinner(f"{tr('running')}: freakto {' '.join(arguments)}"):
            result = run_cli(arguments, timeout=3600 if arguments[:2] in (["data", "build"], ["replay", "run"]) else 900)
        st.session_state["last_result"] = result
        st.session_state["snapshot"] = collect_snapshot()


def start_section_job(
    label: str,
    kind: str,
    *,
    key: str,
    options: dict | None = None,
    disabled: bool = False,
) -> None:
    if st.button(
        label,
        key=key,
        type="primary",
        use_container_width=True,
        disabled=disabled,
    ):
        try:
            job = start_workflow_job(kind, options=options)
            st.session_state["job_notice"] = (
                f"{tr('workflow_started')}: {job['job_id']}"
            )
            st.success(st.session_state["job_notice"])
        except (RuntimeError, ValueError) as exc:
            st.error(f"{tr('workflow_blocked')}: {exc}")


def show_last_result() -> None:
    result = st.session_state.get("last_result")
    if result is None:
        return
    with st.expander(tr("last_output"), expanded=not result.ok):
        if result.ok: st.success(f"{tr('exit_ok')} — exit {result.exit_code}")
        elif result.exit_code == 2: st.warning(f"{tr('exit_blocked')} — exit 2")
        else: st.error(f"{tr('exit_failed')} — exit {result.exit_code}")
        st.code("freakto " + " ".join(result.command[5:]), language="text")
        if result.stdout.strip(): st.code(result.stdout.strip(), language="json")
        if result.stderr.strip(): st.code(result.stderr.strip(), language="text")


if "language" not in st.session_state: st.session_state["language"] = "fa"
if "snapshot" not in st.session_state: st.session_state["snapshot"] = collect_snapshot()

language_label = st.sidebar.selectbox("Language / زبان", ["فارسی", "English"], index=0 if st.session_state["language"] == "fa" else 1)
st.session_state["language"] = "fa" if language_label == "فارسی" else "en"
rtl = st.session_state["language"] == "fa"
inject_style(rtl)

pages = [
    "overview",
    "data",
    "market",
    "forward",
    "airdrop",
    "cross_asset",
    "paper",
    "reports",
    "golive",
    "jobs",
    "guide",
]
page_labels = [tr(item) for item in pages]
st.sidebar.markdown("## ⚡ FREAKTO")
selected = st.sidebar.radio(tr("nav"), page_labels)
page = pages[page_labels.index(selected)]
if st.sidebar.button("↻ " + tr("refresh"), use_container_width=True):
    st.session_state["snapshot"] = collect_snapshot(); st.rerun()
st.sidebar.divider()
st.sidebar.markdown(f"<div class='dashboard'><span class='safe-pill'>● {tr('safe')}</span></div>", unsafe_allow_html=True)
st.sidebar.caption(tr("safe_note"))

snapshot = st.session_state["snapshot"]
st.markdown(f'<div class="hero dashboard"><div class="eyebrow">FREAKTO // CONTROL CENTER</div><h1>{tr("title")}</h1><p>{tr("subtitle")}</p><span class="safe-pill">● {tr("safe")}</span></div>', unsafe_allow_html=True)

if page == "overview":
    go_live = snapshot["go_live"]
    cols = st.columns(4)
    with cols[0]: metric_card(tr("capital"), tr("zero"), "LIVE ORDERS: OFF", "good")
    with cols[1]: metric_card(tr("datasets"), str(snapshot["data"]["datasets"]), snapshot["data"]["latest_utc"] or tr("no_data"))
    with cols[2]: metric_card(tr("paper_mode"), str(snapshot["paper"]["mode"]), tr("armed") if snapshot["paper"]["armed"] else tr("disarmed"), "good" if snapshot["paper"]["armed"] else "")
    with cols[3]: metric_card(tr("review"), tr("blocked") if go_live["status"].startswith("BLOCKED") else tr("reviewable"), f"{len(go_live['blockers'])} blockers", "bad" if go_live["status"].startswith("BLOCKED") else "good")

    st.markdown(f'<div class="quick-box dashboard"><h3>⚡ {tr("quick_title")}</h3><p>{tr("quick_desc")}</p></div>', unsafe_allow_html=True)
    full = st.toggle(tr("full_pipeline"), value=True)
    confirmed = st.checkbox(tr("confirm_quick"))
    if st.button("▶ " + tr("quick_button"), type="primary", use_container_width=True, disabled=not confirmed):
        try:
            job = start_quick_job(full=full)
            st.session_state["job_notice"] = f"{tr('job_started')}: {job['job_id']}"
        except RuntimeError as exc:
            st.session_state["job_notice"] = f"{tr('job_exists')}: {exc}"
    if st.session_state.get("job_notice"):
        st.info(st.session_state["job_notice"])
    active_jobs = [job for job in list_jobs() if job.get("status") in ACTIVE]
    if active_jobs:
        active = active_jobs[0]
        total = max(1, int(active.get("total_steps") or 1))
        st.progress(int(active.get("completed_steps") or 0) / total, text=f"{active.get('status')} — {active.get('current_step') or tr('pending')}")
    st.info(tr("recommended"))

elif page == "data":
    st.subheader(tr("data_title")); st.caption(tr("data_note"))
    c1, c2 = st.columns([1, 1])
    with c1:
        metric_card(tr("data_files"), str(snapshot["data"]["datasets"]), snapshot["data"]["path"])
        execute(tr("data_status"), ["data", "status"], key="data-status", primary=True)
        execute(tr("replay_status"), ["replay", "status"], key="replay-status")
    with c2:
        st.markdown("#### " + tr("heavy"))
        build_ok = st.checkbox(tr("build_confirm"), key="build-confirm")
        execute(tr("build"), ["data", "build"], key="data-build", disabled=not build_ok)
        replay_ok = st.checkbox(tr("replay_confirm"), key="replay-confirm")
        execute(tr("replay_run"), ["replay", "run", "--compact"], key="replay-run", disabled=not replay_ok)

elif page == "market":
    st.subheader(tr("market_title"))
    st.caption(tr("market_note"))
    st.info(tr("one_at_time"))
    market = snapshot["workflows"]
    cards = st.columns(3)
    with cards[0]:
        metric_card(
            tr("adapter_manifests"),
            str(market["market_adapter_manifests"]),
            "EUR/USD + XAU/USD",
        )
    with cards[1]:
        metric_card("Paper", "OFF", "research_only=true", "good")
    with cards[2]:
        metric_card("Live", "OFF", "not available", "good")
    st.markdown("#### " + tr("audit_range"))
    dates = st.columns(2)
    with dates[0]:
        audit_start = st.text_input(
            tr("start_date"),
            value="2023-01-01",
            key="market-audit-start",
        )
    with dates[1]:
        audit_end = st.text_input(
            tr("end_date"),
            value="2026-01-01",
            key="market-audit-end",
        )
    audit_ok = st.checkbox(tr("audit_confirm"), key="market-audit-confirm")
    start_section_job(
        tr("start_audit"),
        "MARKET_DATA_AUDIT",
        key="market-audit-start-button",
        options={"start": audit_start, "end": audit_end},
        disabled=not audit_ok,
    )
    st.divider()
    replay_ok = st.checkbox(
        tr("market_replay_confirm"),
        key="market-replay-confirm",
    )
    start_section_job(
        tr("start_market_replay"),
        "MARKET_REPLAY",
        key="market-replay-start-button",
        disabled=not replay_ok,
    )

elif page == "forward":
    st.subheader(tr("forward_title"))
    st.caption(tr("forward_note"))
    st.info(tr("one_at_time"))
    forward_cols = st.columns(3)
    with forward_cols[0]:
        metric_card(
            tr("last_forward"),
            "COLLECTING",
            snapshot["workflows"]["forward_latest_utc"] or "—",
        )
    with forward_cols[1]:
        metric_card("Paper", "OFF", "gate-controlled", "good")
    with forward_cols[2]:
        metric_card("Live", "OFF", "manual authorization absent", "good")
    execute(
        tr("forward_report"),
        ["report", "forward"],
        key="forward-section-status",
    )
    forward_ok = st.checkbox(tr("forward_confirm"), key="forward-cycle-confirm")
    start_section_job(
        tr("start_forward"),
        "FORWARD_SHADOW_CYCLE",
        key="forward-cycle-start",
        disabled=not forward_ok,
    )

elif page == "airdrop":
    st.subheader(tr("airdrop_title"))
    st.caption(tr("airdrop_note"))
    st.info(tr("one_at_time"))
    airdrop_cols = st.columns(3)
    with airdrop_cols[0]:
        metric_card(
            tr("tracker_db"),
            "READY" if snapshot["workflows"]["airdrop_tracker_exists"] else "EMPTY",
            str(ROOT / "history" / "airdrop_outcomes.db"),
        )
    with airdrop_cols[1]:
        metric_card("Wallet automation", "OFF", "not available", "good")
    with airdrop_cols[2]:
        metric_card("Claim automation", "OFF", "not available", "good")
    airdrop_ok = st.checkbox(tr("airdrop_confirm"), key="airdrop-confirm")
    start_section_job(
        tr("start_airdrop"),
        "AIRDROP_OUTCOMES",
        key="airdrop-start",
        disabled=not airdrop_ok,
    )

elif page == "cross_asset":
    st.subheader(tr("cross_title"))
    st.caption(tr("cross_note"))
    st.info(tr("one_at_time"))
    opportunity_path = st.text_input(
        tr("opportunity_csv"),
        value="data/cross_asset/opportunities.csv",
        key="cross-opportunity-input",
    )
    rank_ok = st.checkbox(tr("rank_confirm"), key="cross-rank-confirm")
    start_section_job(
        tr("start_rank"),
        "CROSS_ASSET_RANK",
        key="cross-rank-start",
        options={"input": opportunity_path},
        disabled=not rank_ok,
    )
    st.divider()
    paths = st.columns(2)
    with paths[0]:
        rankings_path = st.text_input(
            tr("rankings_csv"),
            value="data/cross_asset/rankings.csv",
            key="cross-rankings-input",
        )
    with paths[1]:
        outcomes_path = st.text_input(
            tr("outcomes_csv"),
            value="data/cross_asset/outcomes.csv",
            key="cross-outcomes-input",
        )
    evaluate_ok = st.checkbox(
        tr("evaluate_confirm"),
        key="cross-evaluate-confirm",
    )
    start_section_job(
        tr("start_evaluate"),
        "CROSS_ASSET_EVALUATE",
        key="cross-evaluate-start",
        options={"rankings": rankings_path, "outcomes": outcomes_path},
        disabled=not evaluate_ok,
    )

elif page == "paper":
    st.subheader(tr("paper_title"))
    c1, c2, c3 = st.columns(3)
    with c1: metric_card(tr("paper_mode"), str(snapshot["paper"]["mode"]), tr("armed") if snapshot["paper"]["armed"] else tr("disarmed"))
    with c2: metric_card(tr("live_orders"), tr("off"), tr("unavailable"), "good")
    with c3: metric_card(tr("allocation"), "0.0%", "FAIL-CLOSED", "good")
    actions = st.columns(4)
    with actions[0]: execute(tr("preflight"), ["paper", "preflight"], key="paper-preflight", primary=True)
    with actions[1]: execute(tr("arm_research"), ["paper", "arm-research"], key="paper-arm")
    with actions[2]: execute(tr("one_cycle"), ["paper", "cycle"], key="paper-cycle")
    with actions[3]: execute(tr("status"), ["paper", "status"], key="paper-status")
    st.markdown("#### " + tr("safe_stop"))
    stop_ok = st.checkbox(tr("stop_confirm"), key="stop-confirm")
    execute(tr("disarm"), ["paper", "disarm"], key="paper-disarm", disabled=not stop_ok)
    st.warning(tr("strategy_note"))
    strategy_ok = st.checkbox(tr("strategy_confirm"), key="strategy-confirm")
    execute(tr("arm_strategy"), ["paper", "arm-strategy"], key="paper-strategy", disabled=not strategy_ok)
    st.divider()
    st.markdown("### " + tr("campaign_title"))
    campaign = campaign_status()
    campaign_cols = st.columns(4)
    with campaign_cols[0]: metric_card(tr("campaign_status"), str(campaign.get("status")), str(campaign.get("campaign_id") or "—"), "good" if campaign.get("status") == "RUNNING" else "")
    with campaign_cols[1]: metric_card(tr("campaign_days"), f"{float(campaign.get('elapsed_days', 0)):.2f} / {campaign.get('minimum_days', 60)}", "")
    with campaign_cols[2]: metric_card(tr("campaign_trades"), f"{campaign.get('closed_trades', 0)} / {campaign.get('minimum_closed_trades', 200)}", "")
    with campaign_cols[3]: metric_card(tr("campaign_cycles"), str(campaign.get("cycles", 0)), str(campaign.get("target_end_utc") or "—"))
    campaign_confirm = st.checkbox(tr("campaign_confirm"), key="campaign-confirm")
    campaign_buttons = st.columns(2)
    with campaign_buttons[0]:
        if st.button(tr("campaign_start"), key="campaign-start", use_container_width=True, type="primary", disabled=not campaign_confirm or campaign.get("status") in CAMPAIGN_ACTIVE):
            try:
                start_campaign(); st.success(tr("campaign_started")); st.rerun()
            except RuntimeError as exc: st.error(str(exc))
    with campaign_buttons[1]:
        if st.button(tr("campaign_stop"), key="campaign-stop", use_container_width=True, disabled=campaign.get("status") not in {"STARTING", "RUNNING"}):
            stop_campaign(); st.warning(tr("campaign_stop_requested")); st.rerun()

elif page == "reports":
    st.subheader(tr("reports_title"))
    cols = st.columns(3)
    with cols[0]: execute(tr("paper_report"), ["report", "paper", "--no-plot"], key="report-paper", primary=True)
    with cols[1]: execute(tr("research_report"), ["report", "research"], key="report-research")
    with cols[2]: execute(tr("forward_report"), ["report", "forward"], key="report-forward")
    metric_card(tr("artifacts"), str(snapshot["runtime"]["json_artifacts"]), snapshot["runtime"]["latest_utc"] or tr("no_artifacts"))

elif page == "golive":
    st.subheader(tr("golive_title")); result = snapshot["go_live"]
    if result["status"].startswith("BLOCKED"): st.error(f"BLOCKED — {len(result['blockers'])} {tr('remaining')}")
    else: st.success(tr("manual_only"))
    st.caption(tr("never_live"))
    rows = [{tr("gate"): gate["name"], tr("result"): "✓" if gate["passed"] else "×", tr("current"): str(gate["actual"]), tr("required"): str(gate["required"])} for gate in result["gates"]]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    execute(tr("rerun_golive"), ["paper", "go-live-check"], key="go-live-check", primary=True)
    st.code(str(ROOT / "logs" / "paper_launch_v2" / "go_live_evidence.json"), language="text")

elif page == "jobs":
    st.subheader(tr("jobs_title")); st.caption(tr("jobs_note"))
    jobs = list_jobs()
    if not jobs:
        st.info(tr("no_jobs"))
    else:
        table = []
        for job in jobs:
            total = int(job.get("total_steps") or 0)
            done = int(job.get("completed_steps") or 0)
            table.append(
                {
                    tr("job_id"): job.get("job_id"),
                    tr("kind"): job.get("kind"),
                    tr("job_status"): job.get("status"),
                    tr("progress"): f"{done}/{total}",
                    tr("current_step"): job.get("current_step") or "—",
                    tr("created"): job.get("created_utc"),
                }
            )
        st.dataframe(table, use_container_width=True, hide_index=True)
        identifiers = [job["job_id"] for job in jobs]
        selected_id = st.selectbox(tr("select_job"), identifiers)
        selected_job = next(job for job in jobs if job["job_id"] == selected_id)
        total = max(1, int(selected_job.get("total_steps") or 1))
        st.progress(int(selected_job.get("completed_steps") or 0) / total, text=f"{selected_job.get('status')} — {selected_job.get('current_step') or '—'}")
        if selected_job.get("error"): st.error(selected_job["error"])
        steps = selected_job.get("steps") or []
        if steps: st.dataframe(steps, use_container_width=True, hide_index=True)
        buttons = st.columns(3)
        with buttons[0]:
            if st.button("↻ " + tr("refresh"), key="jobs-refresh", use_container_width=True): st.rerun()
        with buttons[1]:
            if st.button(tr("cancel"), key="job-cancel", use_container_width=True, disabled=selected_job.get("status") not in ACTIVE):
                request_cancel(selected_id); st.success(tr("cancelled_requested")); st.rerun()
        with buttons[2]:
            if st.button(tr("retry"), key="job-retry", use_container_width=True, disabled=selected_job.get("status") not in TERMINAL):
                retry_job(selected_id); st.success(tr("retried")); st.rerun()
        log_text = job_log(selected_id)
        with st.expander(tr("log"), expanded=selected_job.get("status") in {"FAILED", "INTERRUPTED"}):
            st.code(log_text or "—", language="text")

else:
    st.subheader(tr("guide_title")); st.markdown(tr("guide_body")); st.code(".\\run_control_center.bat", language="powershell")

show_last_result()
