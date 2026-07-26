"""Professional, bilingual, zero-capital Streamlit control center for Freakto."""

from __future__ import annotations

import html
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, UnidentifiedImageError

from freakto.paper.campaign import ACTIVE as CAMPAIGN_ACTIVE
from freakto.paper.campaign import campaign_status, start_campaign, stop_campaign
from freakto.showcase_paper import list_showcase_trades, showcase_status, start_showcase, stop_showcase
from freakto.showcase_paper.quality import quality_profile, runbook_alignment
from freakto.showcase_paper.risk import risk_policy, session_preset
from freakto.ui.automation import (
    ensure_scheduler_running,
    list_automations,
    run_automation_now,
    scheduler_status,
    set_automation,
)
from freakto.ui.control_center_state import ROOT, collect_snapshot, quick_start_plan, run_cli, workflow_plan
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
        "operations": "مرکز عملیات", "workflows": "فرآیندها", "reports": "گزارش‌ها", "settings": "تنظیمات و اتوماسیون",
        "refresh": "بروزرسانی", "safe": "صفرسرمایه · Live خاموش", "safe_note": "این پنل فقط Research و Paper اجرا می‌کند و امکان ارسال سفارش واقعی ندارد.",
        "ops_title": "مرکز عملیات Freakto", "ops_sub": "همه‌چیز مهم در یک نگاه؛ وضعیت، پیشرفت، مانع و اقدام بعدی",
        "system_health": "سلامت سیستم", "data": "داده", "paper": "Paper", "go_live": "آمادگی نهایی", "automations": "اتوماسیون‌ها",
        "ready": "آماده", "blocked": "مسدود", "enabled": "فعال", "disabled": "خاموش", "live_off": "LIVE ORDERS: OFF",
        "active_operation": "عملیات فعال", "no_active": "هیچ عملیاتی در حال اجرا نیست", "idle_note": "سیستم آماده شروع یک فرآیند جدید است.",
        "current_step": "مرحله جاری", "next_step": "مرحله بعد", "started": "شروع", "elapsed": "زمان سپری‌شده", "progress": "پیشرفت",
        "cancel": "توقف پس از مرحله جاری", "refresh_status": "بروزرسانی وضعیت", "auto_refresh": "بروزرسانی خودکار هنگام اجرا",
        "pipeline": "مسیر کامل", "pipeline_help": "داده → Replay → Preflight → Research Paper → Reports → بررسی آمادگی",
        "start_full": "شروع مسیر کامل", "full_confirm": "تأیید می‌کنم مسیر فقط Research/Paper است و ممکن است زمان‌بر باشد.",
        "include_build": "ساخت داده و Replay کامل انجام شود", "attention": "نیازمند توجه", "next_action": "اقدام پیشنهادی",
        "latest_result": "آخرین نتیجه", "view_details": "مشاهده جزئیات", "recent_activity": "فعالیت اخیر", "no_history": "هنوز سابقه‌ای ثبت نشده است.",
        "workflows_title": "فرآیندهای مستقل", "workflows_sub": "هر بخش را جدا اجرا و مدیریت کن؛ هم‌زمان فقط یک Job فعال است.",
        "data_markets": "داده و بازارها", "validation_paper": "اعتبارسنجی و Paper", "research": "پژوهش‌های جانبی",
        "data_replay": "ساخت داده و Replay", "data_replay_desc": "وضعیت داده، بروزرسانی cache، بررسی و اجرای Replay فشرده.",
        "market_audit": "ممیزی فارکس و طلا", "market_audit_desc": "ساخت OHLCV استاندارد برای EUR/USD و XAU/USD و ثبت Manifest.",
        "market_replay": "Replay فارکس و طلا", "market_replay_desc": "Replay تحقیقاتی با هزینه‌های ثابت ممیزی‌شده و Leakage Audit.",
        "forward_cycle": "چرخه Forward و Shadow", "forward_desc": "Preflight، Research Arm، چرخه Paper و گزارش Forward به‌ترتیب.",
        "airdrop": "Airdrop Outcomes", "airdrop_desc": "همگام‌سازی نتایج واقعی و تولید گزارش کیفیت پیش‌بینی‌ها.",
        "cross_asset": "رتبه‌بندی بین‌بازاری", "cross_desc": "رتبه‌بندی Research-only و ارزیابی تاریخی فایل‌های CSV داخل پروژه.",
        "start": "شروع", "running": "در حال اجرا", "unavailable_active": "یک Job دیگر فعال است", "advanced": "تنظیمات پیشرفته",
        "start_date": "شروع بازه", "end_date": "پایان بازه", "rank_input": "فایل فرصت‌ها", "rankings_input": "فایل رتبه‌بندی", "outcomes_input": "فایل نتایج",
        "rank": "اجرای رتبه‌بندی", "evaluate": "ارزیابی تاریخی", "paper_controls": "کنترل مستقیم Paper", "preflight": "Preflight", "paper_status": "وضعیت Paper",
        "arm_research": "فعال‌سازی Research", "one_cycle": "یک چرخه Paper", "disarm": "توقف Paper", "confirm_sensitive": "این اقدام صفرسرمایه را تأیید می‌کنم.",
        "campaign": "کمپین ۶۰روزه Paper", "campaign_start": "شروع / ادامه کمپین", "campaign_stop": "توقف امن کمپین", "days": "روز", "trades": "معامله بسته", "cycles": "چرخه",
        "showcase": "Showcase Paper", "showcase_desc": "با روشن‌کردن این حالت چند معامله شبیه‌سازی‌شده باز می‌شود و برای Open/Close کارت تصویری می‌سازد.",
        "showcase_disclaimer": "این معاملات فقط برای مشاهده رفتار سیستم‌اند و وارد Evidence رسمی Go-live نمی‌شوند.", "daily_limit": "حد معامله روزانه", "scan_interval": "فاصله بررسی (ثانیه)",
        "holding_minutes": "حداکثر زمان نگهداری (دقیقه)", "leverage": "اهرم نمایشی", "start_showcase": "روشن‌کردن Showcase", "stop_showcase": "خاموش‌کردن و بستن موقعیت‌ها",
        "open_positions": "موقعیت باز", "showcase_cards": "کارت‌های آخرین معاملات", "download_card": "دانلود کارت", "showcase_started": "Showcase Paper در پس‌زمینه روشن شد.", "showcase_stopping": "درخواست توقف ثبت شد؛ موقعیت‌ها با قیمت جاری بسته می‌شوند.",
        "risk_management": "مدیریت ریسک تست", "risk_level": "ریسک‌پذیری (۰ دقیق تا ۱۰۰ اکتشافی)", "session_style": "نوع جلسه", "quality_test": "تست کیفیت و Win rate", "precision": "دقیق و محتاط", "balanced": "متعادل", "rapid_test": "تست سریع", "market_mode": "منبع اجرای تست", "live_public": "بازار عمومی زنده", "accelerated_replay": "Replay محلی شتاب‌یافته", "scan_activity": "فعالیت آخرین اسکن", "next_scan": "اسکن بعدی", "accepted_signals": "سیگنال پذیرفته", "rejected_signals": "علت‌های رد", "data_errors": "خطاهای اخیر داده", "risk_policy_note": "این کنترل فقط پذیرش فرصت در Showcase را تغییر می‌دهد و منطق موتور اصلی را دست‌کاری نمی‌کند.",
        "unlimited_trades": "معاملات session نامحدود", "analysis_depth": "عمق تحلیل", "analysis_depth_control": "عمق تحلیل فنی (مستقل از ریسک)", "technical_tools": "ابزار تکنیکال فعال", "confluence": "همگرایی تکنیکال", "technical_v2_report": "گزارش Technical Engine v2", "market_regime": "رژیم بازار", "mtf_agreement": "هماهنگی چند تایم‌فریم", "trade_geometry": "هندسه معامله", "calibration_status": "وضعیت کالیبراسیون", "decision_drivers": "دلایل تصمیم", "decision_warnings": "هشدارها", "session_evaluation": "ارزیابی جلسه v2", "expectancy": "بازده موردانتظار", "sample_count": "حجم نمونه",
        "quality_mode": "پروفایل کیفیت معامله", "quality_win_rate": "تمرکز بر Win rate", "quality_balanced": "کیفیت متعادل", "quality_volume": "حجم معاملات اکتشافی", "replay_timeframe": "تایم‌فریم اجرای Replay", "performance_guard": "سلامت عملکرد جلسه", "profit_factor": "Profit Factor", "break_even_win_rate": "Win rate سربه‌سر", "quality_comparison": "مقایسه علّی Quality Gate", "quality_gate_note": "این گیت فقط از معاملات بسته‌شده پیش از هر تصمیم استفاده می‌کند و داده آینده را نمی‌بیند.",
        "quality_not_promoted": "Quality Gate هنوز PF بالاتر از ۱ و expectancy مثبت را ثابت نکرده است؛ فقط Research/Paper باقی می‌ماند.",
        "runbook_aligned": "تنظیمات با معیار پیشنهادی Win-rate هم‌راستاست", "runbook_not_aligned": "این تنظیمات معیار پیشنهادی Win-rate نیست", "evidence_collecting": "در حال جمع‌آوری شواهد", "evidence_mature": "نمونه جلسه به حد اولیه رسیده است", "side_maturity": "بلوغ گیت جهت", "break_even_trigger": "آستانه فعال‌سازی Break-even (R)", "mfe_calibration": "کالیبراسیون Break-even با MFE بازنده‌ها",
        "reports_title": "گزارش و تاریخچه", "reports_sub": "نتیجه روشن هر اجرا، مراحل موفق، نقطه توقف، Blockerها و لاگ کامل.",
        "refresh_reports": "تولید همه گزارش‌ها", "readiness": "گزارش آمادگی", "blockers": "موانع", "gates": "گیت‌ها", "job_history": "تاریخچه Jobها",
        "select_job": "انتخاب Job", "retry": "اجرای مجدد", "log": "لاگ فنی", "step_results": "نتیجه مراحل", "result": "نتیجه", "duration": "مدت", "current": "مقدار فعلی", "required": "حد لازم", "schedules": "زمان‌بندی",
        "settings_title": "تنظیمات و اتوماسیون", "settings_sub": "زمان‌بندی‌های محلی، قرارداد ایمنی و تنظیمات فنی در یک فضای جدا.",
        "scheduler": "Scheduler محلی", "scheduler_running": "فعال و مستقل از مرورگر", "scheduler_stopped": "متوقف", "interval": "فاصله اجرا (ساعت)",
        "next_run": "اجرای بعدی", "last_run": "آخرین اجرا", "save": "ذخیره زمان‌بندی", "run_now": "همین حالا اجرا کن", "automation_note": "Scheduler در پس‌زمینه اجرا می‌شود؛ بستن داشبورد زمان‌بندی‌های فعال را متوقف نمی‌کند.",
        "safety_contract": "قرارداد ایمنی", "safety_body": "سرمایه واقعی صفر است، متغیرهای Live به اجبار خاموش‌اند و عبور از Go-live check فقط گزارش تولید می‌کند.",
        "technical": "اطلاعات فنی", "runtime_path": "مسیر Runtime", "guide": "راهنمای ساده", "guide_body": "۱) داده را آماده کن. ۲) Replay را بسنج. ۳) Forward/Paper را جمع‌آوری کن. ۴) گزارش و Blockerها را بررسی کن. ۵) تصمیم Live فقط خارج از این داشبورد و با تأیید مستقل ممکن است.",
        "saved": "ذخیره شد", "job_started": "Job شروع شد", "job_blocked": "شروع Job مسدود شد", "cancel_requested": "درخواست توقف ثبت شد.",
    },
    "en": {
        "operations": "Operations", "workflows": "Workflows", "reports": "Reports", "settings": "Settings & Automation",
        "refresh": "Refresh", "safe": "ZERO CAPITAL · LIVE OFF", "safe_note": "This panel runs Research and Paper only; real orders are unavailable.",
        "ops_title": "Freakto Operations Center", "ops_sub": "Status, progress, blockers, and the next action in one clear view",
        "system_health": "System health", "data": "Data", "paper": "Paper", "go_live": "Final readiness", "automations": "Automations",
        "ready": "Ready", "blocked": "Blocked", "enabled": "Enabled", "disabled": "Off", "live_off": "LIVE ORDERS: OFF",
        "active_operation": "Active operation", "no_active": "No operation is running", "idle_note": "The system is ready to start a new workflow.",
        "current_step": "Current step", "next_step": "Next step", "started": "Started", "elapsed": "Elapsed", "progress": "Progress",
        "cancel": "Stop after current step", "refresh_status": "Refresh status", "auto_refresh": "Auto-refresh while running",
        "pipeline": "Complete workflow", "pipeline_help": "Data → Replay → Preflight → Research Paper → Reports → Readiness review",
        "start_full": "Start complete workflow", "full_confirm": "I confirm this is Research/Paper only and may take a long time.",
        "include_build": "Build data and run full Replay", "attention": "Needs attention", "next_action": "Recommended next action",
        "latest_result": "Latest result", "view_details": "View details", "recent_activity": "Recent activity", "no_history": "No history has been recorded yet.",
        "workflows_title": "Independent workflows", "workflows_sub": "Run and manage each area separately; only one job can be active at a time.",
        "data_markets": "Data & Markets", "validation_paper": "Validation & Paper", "research": "Supporting Research",
        "data_replay": "Data build & Replay", "data_replay_desc": "Check data, update the cache, validate, and run compact Replay.",
        "market_audit": "Forex & gold audit", "market_audit_desc": "Build contract-compatible OHLCV for EUR/USD and XAU/USD.",
        "market_replay": "Forex & gold Replay", "market_replay_desc": "Research Replay with audited fixed costs and leakage checks.",
        "forward_cycle": "Forward & Shadow cycle", "forward_desc": "Preflight, Research arm, Paper cycle, and Forward report in order.",
        "airdrop": "Airdrop Outcomes", "airdrop_desc": "Synchronize resolved outcomes and report prediction quality.",
        "cross_asset": "Cross-asset ranking", "cross_desc": "Research-only ranking and historical evaluation of workspace CSV files.",
        "start": "Start", "running": "Running", "unavailable_active": "Another job is active", "advanced": "Advanced settings",
        "start_date": "Start date", "end_date": "End date", "rank_input": "Opportunity file", "rankings_input": "Rankings file", "outcomes_input": "Outcomes file",
        "rank": "Run ranking", "evaluate": "Historical evaluation", "paper_controls": "Direct Paper controls", "preflight": "Preflight", "paper_status": "Paper status",
        "arm_research": "Arm Research", "one_cycle": "One Paper cycle", "disarm": "Disarm Paper", "confirm_sensitive": "I confirm this zero-capital action.",
        "campaign": "60-day Paper campaign", "campaign_start": "Start / resume campaign", "campaign_stop": "Safely stop campaign", "days": "Days", "trades": "Closed trades", "cycles": "Cycles",
        "showcase": "Showcase Paper", "showcase_desc": "When enabled, this mode opens several simulated trades and creates an image card for every Open/Close.",
        "showcase_disclaimer": "These trades are for observing system behavior only and never enter official Go-live evidence.", "daily_limit": "Daily trade limit", "scan_interval": "Scan interval (seconds)",
        "holding_minutes": "Maximum holding time (minutes)", "leverage": "Display leverage", "start_showcase": "Enable Showcase", "stop_showcase": "Disable and close positions",
        "open_positions": "Open positions", "showcase_cards": "Latest trade cards", "download_card": "Download card", "showcase_started": "Showcase Paper started in the background.", "showcase_stopping": "Stop requested; positions will close at current prices.",
        "risk_management": "Test risk management", "risk_level": "Risk tolerance (0 precision to 100 exploratory)", "session_style": "Session style", "quality_test": "Quality and win-rate test", "precision": "Precision", "balanced": "Balanced", "rapid_test": "Rapid test", "market_mode": "Test execution source", "live_public": "Live public market", "accelerated_replay": "Accelerated local Replay", "scan_activity": "Latest scan activity", "next_scan": "Next scan", "accepted_signals": "Accepted signals", "rejected_signals": "Rejection reasons", "data_errors": "Recent data errors", "risk_policy_note": "This control changes Showcase admission only and never modifies the core engine logic.",
        "unlimited_trades": "Unlimited session trades", "analysis_depth": "Analysis depth", "analysis_depth_control": "Technical analysis depth (independent of risk)", "technical_tools": "Active technical tools", "confluence": "Technical confluence", "technical_v2_report": "Technical Engine v2 report", "market_regime": "Market regime", "mtf_agreement": "Multi-timeframe agreement", "trade_geometry": "Trade geometry", "calibration_status": "Calibration status", "decision_drivers": "Decision drivers", "decision_warnings": "Warnings", "session_evaluation": "v2 session evaluation", "expectancy": "Expectancy", "sample_count": "Sample size",
        "quality_mode": "Trade quality profile", "quality_win_rate": "Win-rate focus", "quality_balanced": "Balanced quality", "quality_volume": "Exploratory trade volume", "replay_timeframe": "Replay execution timeframe", "performance_guard": "Session performance health", "profit_factor": "Profit Factor", "break_even_win_rate": "Break-even win rate", "quality_comparison": "Causal Quality Gate comparison", "quality_gate_note": "This gate uses only trades closed before each decision and never sees future outcomes.",
        "quality_not_promoted": "The Quality Gate has not yet demonstrated PF above 1 and positive expectancy; it remains Research/Paper only.",
        "runbook_aligned": "Settings match the recommended win-rate benchmark", "runbook_not_aligned": "These settings do not match the recommended win-rate benchmark", "evidence_collecting": "Collecting evidence", "evidence_mature": "The session reached its initial sample target", "side_maturity": "Directional gate maturity", "break_even_trigger": "Break-even activation threshold (R)", "mfe_calibration": "Break-even calibration from losing-trade MFE",
        "reports_title": "Reports & history", "reports_sub": "A clear result for every run: passed steps, stop point, blockers, and full logs.",
        "refresh_reports": "Generate all reports", "readiness": "Readiness report", "blockers": "Blockers", "gates": "Gates", "job_history": "Job history",
        "select_job": "Select job", "retry": "Retry", "log": "Technical log", "step_results": "Step results", "result": "Result", "duration": "Duration", "current": "Current", "required": "Required", "schedules": "schedules",
        "settings_title": "Settings & Automation", "settings_sub": "Local schedules, the safety contract, and technical settings in one separate area.",
        "scheduler": "Local scheduler", "scheduler_running": "Running independently of the browser", "scheduler_stopped": "Stopped", "interval": "Interval (hours)",
        "next_run": "Next run", "last_run": "Last run", "save": "Save schedule", "run_now": "Run now", "automation_note": "The scheduler runs in the background; closing the dashboard does not stop enabled schedules.",
        "safety_contract": "Safety contract", "safety_body": "Real capital is zero, Live flags are forced off, and Go-live check only creates a report.",
        "technical": "Technical information", "runtime_path": "Runtime path", "guide": "Simple guide", "guide_body": "1) Prepare data. 2) validate Replay. 3) collect Forward/Paper evidence. 4) review reports and blockers. 5) Live decisions remain outside this dashboard and require independent approval.",
        "saved": "Saved", "job_started": "Job started", "job_blocked": "Job launch blocked", "cancel_requested": "Stop request recorded.",
    },
}

TEXT["fa"].update({
    "data_quality": "کیفیت داده",
    "active_setup": "ستاپ فعال",
    "net_expected_value": "ارزش موردانتظار خالص",
    "execution_cost": "هزینه اجرای تخمینی",
    "portfolio_risk": "ریسک سبد",
    "promotion_status": "وضعیت Challenger",
    "validation_stability": "پایداری Walk-forward",
    "session_profit_target": "هدف سود خالص جلسه (%)",
    "session_loss_limit": "حد زیان جلسه (%)",
    "session_equity": "سرمایه مجازی جلسه (USDT)",
    "session_return": "بازده خالص جلسه",
    "profit_guard": "محافظ سود جلسه",
    "session_guard_title": "محافظ سود و زیان جلسه",
    "loss_stop": "توقف قطعی زیان",
    "loss_capacity_used": "ظرفیت زیان مصرف‌شده",
    "remaining_loss_buffer": "فاصله تا توقف زیان",
    "guard_basis": "مبنای محاسبه: سود و زیان خالص تحقق‌یافته + موقعیت‌های باز، نسبت به سرمایه مجازی جلسه.",
    "guard_disabled": "این محافظ غیرفعال است؛ مقدار آن را بیشتر از صفر قرار بده.",
})
TEXT["en"].update({
    "data_quality": "Data quality",
    "active_setup": "Active setup",
    "net_expected_value": "Net expected value",
    "execution_cost": "Estimated execution cost",
    "portfolio_risk": "Portfolio risk",
    "promotion_status": "Challenger status",
    "validation_stability": "Walk-forward stability",
    "session_profit_target": "Net session profit target (%)",
    "session_loss_limit": "Session loss limit (%)",
    "session_equity": "Virtual session equity (USDT)",
    "session_return": "Net session return",
    "profit_guard": "Session profit guard",
    "session_guard_title": "Session profit and loss guard",
    "loss_stop": "Hard loss stop",
    "loss_capacity_used": "Loss capacity used",
    "remaining_loss_buffer": "Remaining loss buffer",
    "guard_basis": "Basis: net realized PnL plus open-position PnL, divided by virtual session equity.",
    "guard_disabled": "This guard is disabled; set its value above zero to enable it.",
})

KIND_LABELS = {
    "QUICK_START": ("مسیر کامل", "Complete workflow"), "DATA_REPLAY": ("داده و Replay", "Data & Replay"),
    "MARKET_DATA_AUDIT": ("ممیزی بازار", "Market audit"), "MARKET_REPLAY": ("Replay بازار", "Market Replay"),
    "FORWARD_SHADOW_CYCLE": ("Forward و Shadow", "Forward & Shadow"), "AIRDROP_OUTCOMES": ("نتایج Airdrop", "Airdrop outcomes"),
    "CROSS_ASSET_RANK": ("رتبه‌بندی بین‌بازاری", "Cross-asset rank"), "CROSS_ASSET_EVALUATE": ("ارزیابی بین‌بازاری", "Cross-asset evaluation"),
    "REPORT_REFRESH": ("بروزرسانی گزارش‌ها", "Report refresh"),
}

STEP_LABELS = {
    "data_status": ("بررسی وضعیت داده", "Check data status"), "data_build": ("ساخت و بروزرسانی داده", "Build and update data"),
    "replay_status": ("بررسی وضعیت Replay", "Check Replay status"), "replay_run": ("اجرای Replay", "Run Replay"),
    "paper_preflight": ("بررسی آمادگی Paper", "Paper preflight"), "arm_research": ("فعال‌سازی Research Paper", "Arm Research Paper"),
    "paper_cycle": ("اجرای چرخه Paper", "Run Paper cycle"), "paper_status": ("بررسی وضعیت Paper", "Check Paper status"),
    "paper_report": ("تولید گزارش Paper", "Generate Paper report"), "research_report": ("تولید گزارش Research", "Generate Research report"),
    "forward_report": ("تولید گزارش Forward", "Generate Forward report"), "go_live_check": ("بررسی آمادگی نهایی", "Final readiness check"),
    "audit_eur_usd": ("ممیزی EUR/USD", "Audit EUR/USD"), "audit_xau_usd": ("ممیزی XAU/USD", "Audit XAU/USD"),
    "replay_forex_gold": ("Replay فارکس و طلا", "Replay forex and gold"), "airdrop_sync": ("همگام‌سازی Airdrop", "Sync Airdrop"),
    "airdrop_report": ("گزارش نتایج Airdrop", "Airdrop outcome report"), "cross_asset_rank": ("رتبه‌بندی دارایی‌ها", "Rank assets"),
    "cross_asset_evaluate": ("ارزیابی تاریخی رتبه‌ها", "Evaluate historical rankings"),
}

STATUS_LABELS = {
    "QUEUED": ("در صف", "Queued"), "RUNNING": ("در حال اجرا", "Running"), "CANCEL_REQUESTED": ("در انتظار توقف", "Stop requested"),
    "SUCCEEDED": ("موفق", "Succeeded"), "FAILED": ("ناموفق", "Failed"), "CANCELLED": ("لغوشده", "Cancelled"), "INTERRUPTED": ("قطع‌شده", "Interrupted"),
    "STARTING": ("در حال شروع", "Starting"), "STOP_REQUESTED": ("در انتظار توقف", "Stop requested"), "STOPPED": ("خاموش", "Stopped"),
}

BLOCKER_LABELS = {
    "policy_version": ("نسخه سیاست Go-live ثبت نشده", "Go-live policy version is missing"),
    "frozen_contract": ("قرارداد ارزیابی هنوز تثبیت نشده", "The evaluation contract is not frozen"),
    "evaluation_window_frozen": ("بازه ارزیابی هنوز تثبیت نشده", "The evaluation window is not frozen"),
    "sample_size": ("حجم نمونه کافی نیست", "The sample size is insufficient"),
    "observation_days": ("روزهای مشاهده کافی نیست", "There are not enough observation days"),
    "after_cost_expectancy": ("بازده موردانتظار پس از هزینه کافی نیست", "After-cost expectancy is below the requirement"),
    "expectancy_confidence": ("اطمینان آماری بازده کافی نیست", "Expectancy confidence is insufficient"),
    "profit_factor": ("Profit Factor به حد لازم نرسیده", "Profit factor is below the requirement"),
    "drawdown": ("افت سرمایه از محدوده مجاز خارج است", "Drawdown is outside the permitted range"),
    "regime_coverage": ("پوشش رژیم‌های بازار کافی نیست", "Market-regime coverage is insufficient"),
    "regime_stability": ("پایداری عملکرد میان رژیم‌ها کافی نیست", "Performance is not stable across regimes"),
    "cycle_reliability": ("قابلیت اتکای چرخه‌ها کافی نیست", "Cycle reliability is insufficient"),
    "data_freshness": ("داده‌ها به‌اندازه کافی تازه نیستند", "Data is not fresh enough"),
    "critical_incidents": ("رخدادهای بحرانی باید بررسی شوند", "Critical incidents require review"),
    "kill_switch": ("Kill Switch تأیید نشده", "The kill switch is not verified"),
    "independent_approvals": ("تأییدهای مستقل کامل نیست", "Independent approvals are incomplete"),
}

AUTOMATION_LABELS = {
    "daily_data_replay": (("داده و Replay", "Data & Replay"), ("بروزرسانی داده، اعتبارسنجی cache و اجرای Replay فشرده.", "Build data, validate the cache, and run compact Replay.")),
    "forward_shadow": (("Forward و Shadow", "Forward & Shadow"), ("اجرای Preflight، Research Arm، یک چرخه Paper و گزارش Forward.", "Run Preflight, Research arm, one Paper cycle, and Forward reports.")),
    "report_refresh": (("گزارش‌ها", "Reports"), ("بروزرسانی گزارش‌های Paper، Research، Forward و آمادگی نهایی.", "Refresh Paper, Research, Forward, and readiness reports.")),
    "airdrop_outcomes": (("نتایج Airdrop", "Airdrop outcomes"), ("همگام‌سازی نتایج نهایی‌شده و بازسازی گزارش پژوهشی.", "Synchronize resolved outcomes and rebuild the research report.")),
}


def t(key: str) -> str:
    return TEXT[st.session_state.get("language", "fa")].get(key, key)


def localized(pair: tuple[str, str] | None, fallback: str = "—") -> str:
    if not pair:
        return fallback
    return pair[0] if st.session_state.get("language", "fa") == "fa" else pair[1]


def kind_label(kind: object) -> str:
    return localized(KIND_LABELS.get(str(kind)), str(kind or "—"))


def step_label(step: object) -> str:
    return localized(STEP_LABELS.get(str(step)), str(step or "—"))


def status_label(status: object) -> str:
    return localized(STATUS_LABELS.get(str(status)), str(status or "—"))


def blocker_label(blocker: object) -> str:
    return localized(BLOCKER_LABELS.get(str(blocker)), str(blocker or "—"))


def format_time(value: object) -> str:
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed.astimezone().strftime("%Y-%m-%d  %H:%M")
    except ValueError:
        return str(value)


def elapsed(job: dict) -> str:
    if not job.get("started_utc"):
        return "—"
    try:
        start = datetime.fromisoformat(str(job["started_utc"]))
        end = datetime.fromisoformat(str(job["ended_utc"])) if job.get("ended_utc") else datetime.now(timezone.utc)
    except ValueError:
        return "—"
    seconds = max(0, int((end - start).total_seconds()))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def esc(value: object) -> str:
    return html.escape(str(value if value is not None else "—"))


def inject_style(rtl: bool) -> None:
    direction = "rtl" if rtl else "ltr"
    align = "right" if rtl else "left"
    st.markdown(
        f"""
<style>
:root {{ --bg:#071018; --panel:#0b1822; --panel2:#0e202d; --line:#1b3949; --text:#eef8fc; --muted:#86a1b1; --accent:#35d4c4; --green:#62e6a2; --amber:#f2c46d; --red:#ff8c91; }}
.stApp {{ background:radial-gradient(circle at 72% -12%,#12364b 0,transparent 34%),linear-gradient(180deg,#08131c,#060d13); color:var(--text); }}
.main .block-container {{ max-width:1380px; padding-top:2.25rem; padding-bottom:3rem; }}
.dashboard {{ direction:{direction}; text-align:{align}; }}
[data-testid="stSidebar"] {{ background:#08131c; border-inline-end:1px solid #173140; }}
[data-testid="stSidebar"] [role="radiogroup"] {{ gap:.25rem; }}
[data-testid="stSidebar"] label {{ padding:.46rem .5rem; border-radius:10px; }}
.page-head {{ display:flex; justify-content:space-between; align-items:end; gap:1rem; padding:.9rem 0 1.1rem; border-bottom:1px solid var(--line); margin-bottom:1rem; }}
.page-head h1 {{ color:var(--text); font-size:1.65rem; margin:.18rem 0; }} .page-head p {{ color:var(--muted); margin:0; font-size:.88rem; }}
.eyebrow {{ color:var(--accent); letter-spacing:.13em; font-weight:800; font-size:.7rem; }}
.safe-pill {{ display:inline-flex; color:var(--green); background:#0b2a21; border:1px solid #215c45; border-radius:999px; padding:.35rem .7rem; font-size:.73rem; font-weight:800; }}
.metric-grid {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:.7rem; margin-bottom:1rem; }}
.metric-card {{ min-height:92px; padding:.8rem .9rem; background:linear-gradient(145deg,#0c1c27,#09151e); border:1px solid var(--line); border-radius:14px; }}
.metric-card .label {{ color:var(--muted); font-size:.72rem; }} .metric-card .value {{ color:var(--text); font-weight:800; font-size:1.15rem; margin:.32rem 0 .16rem; }} .metric-card .note {{ color:#6f8c9d; font-size:.7rem; overflow-wrap:anywhere; }}
.metric-card.good .value {{ color:var(--green); }} .metric-card.warn .value {{ color:var(--amber); }} .metric-card.bad .value {{ color:var(--red); }}
.section-title {{ color:var(--text); font-weight:800; font-size:.94rem; margin-bottom:.18rem; }} .section-copy {{ color:var(--muted); font-size:.79rem; margin-bottom:.7rem; }}
.active-card {{ background:linear-gradient(120deg,#0d2531,#102334); border:1px solid #286078; border-radius:16px; padding:1rem 1.1rem; }}
.active-top {{ display:flex; justify-content:space-between; align-items:start; gap:.8rem; }} .active-title {{ color:var(--text); font-size:1.08rem; font-weight:850; }}
.status-badge {{ display:inline-flex; border-radius:999px; padding:.28rem .58rem; font-size:.7rem; font-weight:800; background:#143547; color:#86deef; }}
.status-badge.success {{ background:#0c3024; color:var(--green); }} .status-badge.error {{ background:#351a20; color:var(--red); }} .status-badge.warn {{ background:#3b2d17; color:var(--amber); }}
.job-meta {{ display:grid; grid-template-columns:repeat(3,1fr); gap:.55rem; margin:.85rem 0; }} .job-meta div {{ background:#091722; padding:.6rem .7rem; border-radius:10px; border:1px solid #173747; }} .job-meta span {{ display:block;color:var(--muted);font-size:.68rem; }} .job-meta strong {{ display:block;color:var(--text);font-size:.79rem;margin-top:.18rem; }}
.timeline {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:.42rem; margin:.7rem 0; }}
.timeline-step {{ border:1px solid #1b3a4b; border-radius:10px; padding:.55rem; color:#7895a6; background:#091722; font-size:.69rem; min-height:54px; }} .timeline-step.done {{ border-color:#23654e;color:var(--green); }} .timeline-step.current {{ border-color:#2a8ba1;color:#9cecf1;background:#0c2b36; }} .timeline-step.failed {{ border-color:#71343a;color:var(--red); }}
.notice {{ border-radius:12px; padding:.75rem .85rem; border:1px solid #514725; background:#292411; color:#f1d78c; font-size:.8rem; margin:.55rem 0; }}
.recommend {{ border-radius:12px; padding:.75rem .85rem; border:1px solid #205846; background:#0b2820; color:#91efbd; font-size:.8rem; margin:.55rem 0; }}
.status-rows {{ display:grid; gap:.42rem; }} .status-row {{ display:flex; justify-content:space-between; gap:1rem; padding:.52rem .65rem; background:#091722; border:1px solid #173443; border-radius:9px; font-size:.74rem; }} .status-row span {{ color:var(--muted); }} .status-row strong {{ color:var(--text); text-align:end; overflow-wrap:anywhere; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background:linear-gradient(145deg,rgba(12,28,39,.92),rgba(8,19,28,.92)); border-color:var(--line)!important; border-radius:15px!important; }}
[data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap:.3rem;background:#08151e;padding:.3rem;border-radius:11px; }} [data-testid="stTabs"] [data-baseweb="tab"] {{ border-radius:8px;padding:.5rem .75rem; }}
[data-testid="stExpander"] {{ border-color:var(--line)!important;border-radius:11px!important;background:#08151e; }}
div[data-testid="stButton"] button {{ border-radius:10px; min-height:2.55rem; font-weight:750; border-color:#28546a; }} div[data-testid="stButton"] button[kind="primary"] {{ background:linear-gradient(90deg,#078b83,#176b96);border:0; }}
div[data-testid="stDataFrame"] {{ border:1px solid var(--line);border-radius:12px;overflow:hidden; }}
@media(max-width:900px) {{ .metric-grid{{grid-template-columns:repeat(2,1fr)}} .job-meta{{grid-template-columns:1fr}} .page-head{{display:block}} }}
</style>
""",
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, eyebrow: str) -> None:
    st.markdown(
        f'<div class="page-head dashboard"><div><div class="eyebrow">{esc(eyebrow)}</div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div><span class="safe-pill">● {esc(t("safe"))}</span></div>',
        unsafe_allow_html=True,
    )


def metrics(items: list[tuple[str, object, object, str]]) -> None:
    cards = "".join(
        f'<div class="metric-card {esc(css)}"><div class="label">{esc(label)}</div><div class="value">{esc(value)}</div><div class="note">{esc(note)}</div></div>'
        for label, value, note, css in items
    )
    st.markdown(f'<div class="metric-grid dashboard">{cards}</div>', unsafe_allow_html=True)


def section_intro(title: str, copy: str) -> None:
    st.markdown(f'<div class="dashboard"><div class="section-title">{esc(title)}</div><div class="section-copy">{esc(copy)}</div></div>', unsafe_allow_html=True)


def status_rows(rows: list[tuple[str, object]]) -> None:
    content = "".join(f'<div class="status-row"><span>{esc(label)}</span><strong>{esc(value)}</strong></div>' for label, value in rows)
    st.markdown(f'<div class="status-rows dashboard">{content}</div>', unsafe_allow_html=True)


def plan_for_job(job: dict) -> tuple:
    try:
        if job.get("kind") == "QUICK_START":
            return quick_start_plan(include_data_build=bool(job.get("full")), include_replay=bool(job.get("full")))
        return workflow_plan(str(job.get("kind")), dict(job.get("options") or {}))
    except (ValueError, OSError):
        return ()


def next_step(job: dict) -> str:
    plan = plan_for_job(job)
    completed = int(job.get("completed_steps") or 0)
    return step_label(plan[completed].key) if completed < len(plan) else "—"


def render_timeline(job: dict) -> None:
    plan = plan_for_job(job)
    completed_keys = {str(item.get("key")) for item in job.get("steps") or [] if item.get("accepted")}
    failed_keys = {str(item.get("key")) for item in job.get("steps") or [] if not item.get("accepted")}
    current = str(job.get("current_step") or "")
    cards = []
    for index, step in enumerate(plan, start=1):
        css = "done" if step.key in completed_keys else "failed" if step.key in failed_keys else "current" if step.key == current else ""
        cards.append(f'<div class="timeline-step {css}">{index}. {esc(step_label(step.key))}</div>')
    if cards:
        st.markdown(f'<div class="timeline dashboard">{"".join(cards)}</div>', unsafe_allow_html=True)


def start_job(kind: str, *, options: dict | None = None) -> None:
    try:
        job = start_workflow_job(kind, options=options)
        st.session_state["notice"] = f'{t("job_started")}: {job["job_id"]}'
        st.rerun()
    except (RuntimeError, ValueError) as exc:
        st.error(f'{t("job_blocked")}: {exc}')


def run_command(label: str, arguments: list[str], *, key: str, disabled: bool = False, primary: bool = False) -> None:
    if st.button(label, key=key, disabled=disabled, type="primary" if primary else "secondary", use_container_width=True):
        with st.spinner(t("running")):
            result = run_cli(arguments, timeout=3600 if "cycle" in arguments else 900)
        st.session_state["last_result"] = result
        st.session_state["snapshot"] = collect_snapshot()


def render_active_job(job: dict | None, *, controls: bool = True) -> None:
    if not job:
        st.markdown(f'<div class="active-card dashboard"><div class="active-title">{esc(t("no_active"))}</div><div class="section-copy">{esc(t("idle_note"))}</div></div>', unsafe_allow_html=True)
        return
    status = str(job.get("status"))
    badge_css = "warn" if status == "CANCEL_REQUESTED" else ""
    st.markdown(
        f'<div class="active-card dashboard"><div class="active-top"><div><div class="eyebrow">{esc(t("active_operation"))}</div><div class="active-title">{esc(kind_label(job.get("kind")))}</div></div><span class="status-badge {badge_css}">{esc(status_label(status))}</span></div>'
        f'<div class="job-meta"><div><span>{esc(t("current_step"))}</span><strong>{esc(step_label(job.get("current_step")))}</strong></div><div><span>{esc(t("next_step"))}</span><strong>{esc(next_step(job))}</strong></div><div><span>{esc(t("elapsed"))}</span><strong>{esc(elapsed(job))}</strong></div></div></div>',
        unsafe_allow_html=True,
    )
    total = max(1, int(job.get("total_steps") or 1))
    done = int(job.get("completed_steps") or 0)
    st.progress(done / total, text=f'{t("progress")}: {done}/{total} · {step_label(job.get("current_step"))}')
    render_timeline(job)
    if controls:
        buttons = st.columns(2)
        with buttons[0]:
            if st.button("↻ " + t("refresh_status"), use_container_width=True, key="active-refresh"):
                st.session_state["snapshot"] = collect_snapshot(); st.rerun()
        with buttons[1]:
            if st.button(t("cancel"), use_container_width=True, key="active-cancel", disabled=status not in ACTIVE):
                request_cancel(str(job["job_id"])); st.warning(t("cancel_requested")); st.rerun()


def workflow_card(title: str, description: str, kind: str, *, key: str, active: bool, options: dict | None = None) -> None:
    with st.container(border=True):
        section_intro(title, description)
        status_rows([(t("system_health"), t("unavailable_active") if active else t("ready")), ("Mode", "Research / Paper")])
        if st.button(t("start"), key=key, type="primary", use_container_width=True, disabled=active):
            start_job(kind, options=options)


def latest_terminal(jobs: list[dict]) -> dict | None:
    return next((job for job in jobs if job.get("status") in TERMINAL), None)


def recommendation(snapshot: dict, jobs: list[dict], active: dict | None) -> str:
    if active:
        return f'{t("running")}: {step_label(active.get("current_step"))}. {t("next_step")}: {next_step(active)}.'
    recent = latest_terminal(jobs)
    if recent and recent.get("status") in {"FAILED", "INTERRUPTED"}:
        return f'{kind_label(recent.get("kind"))}: {status_label(recent.get("status"))}. {t("retry")}.'
    blockers = snapshot["go_live"].get("blockers") or []
    if blockers:
        return t("forward_desc")
    return t("guide_body")


if "language" not in st.session_state:
    st.session_state["language"] = "fa"
if "snapshot" not in st.session_state:
    st.session_state["snapshot"] = collect_snapshot()

language_label = st.sidebar.selectbox("زبان / Language", ["فارسی", "English"], index=0 if st.session_state["language"] == "fa" else 1)
st.session_state["language"] = "fa" if language_label == "فارسی" else "en"
inject_style(st.session_state["language"] == "fa")

st.sidebar.markdown("## ⚡ FREAKTO")
page_keys = ["operations", "workflows", "reports", "settings"]
page_names = {key: t(key) for key in page_keys}
requested_page = str(st.query_params.get("page", "operations"))
requested_index = page_keys.index(requested_page) if requested_page in page_keys else 0
selected_name = st.sidebar.radio("Workspace", [page_names[key] for key in page_keys], index=requested_index, key=f'nav-{st.session_state["language"]}')
page = next(key for key, value in page_names.items() if value == selected_name)
if requested_page != page:
    st.query_params["page"] = page
if st.sidebar.button("↻ " + t("refresh"), use_container_width=True):
    st.session_state["snapshot"] = collect_snapshot(); st.rerun()
st.sidebar.divider()
st.sidebar.markdown(f'<div class="dashboard"><span class="safe-pill">● {esc(t("safe"))}</span></div>', unsafe_allow_html=True)
st.sidebar.caption(t("safe_note"))

snapshot = st.session_state["snapshot"]
jobs = list_jobs()
active = next((job for job in jobs if job.get("status") in ACTIVE), None)
automations = list_automations()
enabled_automations = [item for item in automations if item.get("enabled")]
showcase = showcase_status()
showcase_trades = list_showcase_trades()
if enabled_automations and scheduler_status().get("status") != "RUNNING":
    try:
        ensure_scheduler_running()
    except OSError:
        pass

notice = st.session_state.pop("notice", None)
if notice:
    st.success(str(notice))

if page == "operations":
    page_header(t("ops_title"), t("ops_sub"), "FREAKTO / OPERATIONS")
    go_live = snapshot["go_live"]
    metrics([
        (t("system_health"), t("running") if active else t("ready"), t("live_off"), "good"),
        (t("data"), snapshot["data"]["datasets"], format_time(snapshot["data"]["latest_utc"]), ""),
        (t("paper"), snapshot["paper"]["mode"], t("enabled") if snapshot["paper"]["armed"] else t("disabled"), "good" if snapshot["paper"]["armed"] else ""),
        (t("go_live"), t("blocked") if go_live["status"].startswith("BLOCKED") else t("ready"), f'{len(go_live.get("blockers") or [])} {t("blockers")}', "bad" if go_live["status"].startswith("BLOCKED") else "good"),
    ])
    if showcase.get("status") in {"STARTING", "RUNNING", "STOP_REQUESTED"}:
        with st.container(border=True):
            section_intro(t("showcase"), t("showcase_disclaimer"))
            status_rows([
                (t("system_health"), status_label(showcase.get("status"))),
                (t("open_positions"), showcase.get("open_trades", 0)),
                (t("trades"), showcase.get("closed_trades", 0)),
                (t("started"), format_time(showcase.get("started_utc"))),
            ])
            if st.button(t("stop_showcase"), use_container_width=True, key="ops-stop-showcase", disabled=showcase.get("status") == "STOP_REQUESTED"):
                try:
                    stop_showcase(); st.warning(t("showcase_stopping")); st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    main, side = st.columns([1.45, .75])
    with main:
        render_active_job(active)
        if active:
            auto = st.toggle(t("auto_refresh"), value=False, key="auto-refresh")
            if auto:
                components.html("<script>setTimeout(function(){window.parent.location.reload();}, 20000);</script>", height=0)
        else:
            with st.container(border=True):
                section_intro(t("pipeline"), t("pipeline_help"))
                include_build = st.toggle(t("include_build"), value=True)
                confirmed = st.checkbox(t("full_confirm"), key="full-confirm")
                if st.button("▶ " + t("start_full"), type="primary", use_container_width=True, disabled=not confirmed):
                    try:
                        job = start_quick_job(full=include_build)
                        st.session_state["notice"] = f'{t("job_started")}: {job["job_id"]}'
                        st.rerun()
                    except RuntimeError as exc:
                        st.error(f'{t("job_blocked")}: {exc}')
    with side:
        with st.container(border=True):
            section_intro(t("next_action"), t("attention"))
            st.markdown(f'<div class="recommend dashboard">{esc(recommendation(snapshot, jobs, active))}</div>', unsafe_allow_html=True)
            blockers = go_live.get("blockers") or []
            if blockers:
                st.markdown(f'<div class="notice dashboard">{esc(blocker_label(blockers[0]))}</div>', unsafe_allow_html=True)
        with st.container(border=True):
            section_intro(t("automations"), t("automation_note"))
            status_rows([(t("enabled"), len(enabled_automations)), (t("scheduler"), t("scheduler_running") if scheduler_status().get("status") == "RUNNING" else t("scheduler_stopped"))])
        recent = latest_terminal(jobs)
        with st.container(border=True):
            section_intro(t("latest_result"), t("recent_activity"))
            if recent:
                status_rows([(kind_label(recent.get("kind")), status_label(recent.get("status"))), (t("duration"), elapsed(recent)), (t("current_step"), step_label((recent.get("steps") or [{}])[-1].get("key")))])
            else:
                st.caption(t("no_history"))

elif page == "workflows":
    page_header(t("workflows_title"), t("workflows_sub"), "FREAKTO / WORKFLOWS")
    if active:
        st.info(f'{t("active_operation")}: {kind_label(active.get("kind"))} · {step_label(active.get("current_step"))}')
    data_tab, validation_tab, research_tab = st.tabs([t("data_markets"), t("validation_paper"), t("research")])
    with data_tab:
        cols = st.columns(3)
        with cols[0]: workflow_card(t("data_replay"), t("data_replay_desc"), "DATA_REPLAY", key="start-data-replay", active=bool(active))
        with cols[1]: workflow_card(t("market_audit"), t("market_audit_desc"), "MARKET_DATA_AUDIT", key="start-market-audit", active=bool(active), options={"start": "2023-01-01", "end": "2026-01-01"})
        with cols[2]: workflow_card(t("market_replay"), t("market_replay_desc"), "MARKET_REPLAY", key="start-market-replay", active=bool(active))
        with st.expander(t("advanced")):
            date_cols = st.columns(2)
            with date_cols[0]: audit_start = st.text_input(t("start_date"), "2023-01-01")
            with date_cols[1]: audit_end = st.text_input(t("end_date"), "2026-01-01")
            if st.button(t("market_audit") + " · " + t("start"), disabled=bool(active), key="advanced-market-audit"):
                start_job("MARKET_DATA_AUDIT", options={"start": audit_start, "end": audit_end})
    with validation_tab:
        with st.container(border=True):
            section_intro(t("showcase"), t("showcase_desc"))
            st.warning(t("showcase_disclaimer"))
            showcase_active = showcase.get("status") in {"STARTING", "RUNNING", "STOP_REQUESTED"}
            showcase_settings = dict(showcase.get("settings") or {})
            section_intro(t("risk_management"), t("risk_policy_note"))
            preset_names = {"QUALITY_TEST": t("quality_test"), "PRECISION": t("precision"), "BALANCED": t("balanced"), "RAPID_TEST": t("rapid_test")}
            preset_key = st.selectbox(
                t("session_style"),
                ["QUALITY_TEST", "RAPID_TEST", "BALANCED", "PRECISION"],
                format_func=lambda value: preset_names[value],
                disabled=showcase_active,
                key="showcase-session-style",
            )
            preset = session_preset(preset_key)
            primary_settings = st.columns([1, 1, 1, 1])
            with primary_settings[0]:
                risk_level = st.slider(
                    t("risk_level"), min_value=0, max_value=100,
                    value=int(showcase_settings.get("risk_level", preset.risk_level)) if showcase_active else preset.risk_level,
                    step=5, disabled=showcase_active, key=f"showcase-risk-{preset_key}",
                )
            with primary_settings[1]:
                analysis_depth = st.slider(
                    t("analysis_depth_control"), min_value=0, max_value=100,
                    value=int(showcase_settings.get("analysis_depth", preset.analysis_depth)) if showcase_active else preset.analysis_depth,
                    step=5, disabled=showcase_active, key=f"showcase-analysis-{preset_key}",
                )
            with primary_settings[2]:
                quality_values = ["WIN_RATE", "BALANCED", "VOLUME"]
                quality_labels = {"WIN_RATE": t("quality_win_rate"), "BALANCED": t("quality_balanced"), "VOLUME": t("quality_volume")}
                preset_quality = {"QUALITY_TEST": "WIN_RATE", "RAPID_TEST": "VOLUME", "BALANCED": "BALANCED", "PRECISION": "WIN_RATE"}[preset_key]
                selected_quality = str(showcase_settings.get("quality_mode", preset_quality)) if showcase_active else preset_quality
                quality_mode = st.selectbox(
                    t("quality_mode"), quality_values, index=quality_values.index(selected_quality),
                    format_func=lambda value: quality_labels[value], disabled=showcase_active,
                    key=f"showcase-quality-{preset_key}",
                )
            with primary_settings[3]:
                mode_values = ["ACCELERATED_REPLAY", "LIVE_PUBLIC"]
                mode_labels = {"ACCELERATED_REPLAY": t("accelerated_replay"), "LIVE_PUBLIC": t("live_public")}
                selected_mode = str(showcase_settings.get("market_mode", preset.market_mode)) if showcase_active else preset.market_mode
                market_mode = st.selectbox(
                    t("market_mode"), mode_values, index=mode_values.index(selected_mode),
                    format_func=lambda value: mode_labels[value], disabled=showcase_active,
                    key=f"showcase-mode-{preset_key}",
                )
            policy = risk_policy(risk_level)
            quality = quality_profile(quality_mode)
            alignment = runbook_alignment(
                quality_mode=quality_mode, risk_level=risk_level, analysis_depth=analysis_depth,
            )
            from freakto.technical_v2.service import analysis_profile
            technical_profile = analysis_profile(analysis_depth)
            st.caption(
                f'{policy.key} · {quality.label} · {technical_profile["label"]} · Technical Engine v2 · '
                f'Score ≥ {policy.minimum_score} · Confidence ≥ {policy.minimum_confidence}% · '
                f'Confluence ≥ {max(policy.minimum_confluence_pct, quality.minimum_confluence_pct)}% · '
                f'Net EV ≥ {quality.minimum_net_expected_value_pct:.2f}% · Cost-adjusted R:R ≥ {quality.minimum_cost_adjusted_reward_risk:.2f}'
            )
            st.success(
                f'∞ {t("unlimited_trades")} · {t("analysis_depth")}: {analysis_depth}/100 · '
                f'MTF: {", ".join(technical_profile["timeframes"])}'
            )
            if alignment["runbook_aligned"]:
                st.success("✓ " + t("runbook_aligned"))
            else:
                st.warning("⚠ " + t("runbook_not_aligned") + ": " + ", ".join(alignment["reasons"]))
            with st.expander(t("advanced")):
                settings_cols = st.columns(3)
                with settings_cols[0]:
                    scan_interval = st.number_input(t("scan_interval"), min_value=5, max_value=3600, value=int(showcase_settings.get("scan_interval_seconds", preset.scan_interval_seconds)) if showcase_active else preset.scan_interval_seconds, step=5, disabled=showcase_active, key=f"showcase-scan-{preset_key}")
                with settings_cols[1]:
                    holding_minutes = st.number_input(t("holding_minutes"), min_value=1, max_value=1440, value=int(showcase_settings.get("maximum_holding_minutes", preset.maximum_holding_minutes)) if showcase_active else preset.maximum_holding_minutes, step=1, disabled=showcase_active, key=f"showcase-hold-{preset_key}")
                with settings_cols[2]:
                    leverage = st.number_input(t("leverage"), min_value=1.0, max_value=5.0, value=float(showcase_settings.get("leverage", preset.leverage)) if showcase_active else preset.leverage, step=0.5, disabled=showcase_active, key=f"showcase-leverage-{preset_key}")
                replay_values = ["AUTO", "15m", "1h", "4h"]
                selected_replay_timeframe = str(showcase_settings.get("replay_timeframe", "AUTO")) if showcase_active else "AUTO"
                replay_timeframe = st.selectbox(
                    t("replay_timeframe"), replay_values, index=replay_values.index(selected_replay_timeframe),
                    disabled=showcase_active or market_mode != "ACCELERATED_REPLAY", key=f"showcase-replay-timeframe-{preset_key}",
                )
                break_even_trigger_r = st.number_input(
                    t("break_even_trigger"), min_value=0.0, max_value=3.0,
                    value=float(showcase_settings.get("break_even_trigger_r", 0.75)) if showcase_active else 0.75,
                    step=0.05, disabled=showcase_active, key=f"showcase-break-even-{preset_key}",
                )
                guard_settings = st.columns(3)
                with guard_settings[0]:
                    session_profit_target = st.number_input(
                        t("session_profit_target"), min_value=0.0, max_value=20.0,
                        value=float(showcase_settings.get("session_profit_target_pct", policy.session_profit_target_pct)) if showcase_active else float(policy.session_profit_target_pct),
                        step=0.25, disabled=showcase_active, key=f"showcase-profit-target-{preset_key}",
                    )
                with guard_settings[1]:
                    session_loss_limit = st.number_input(
                        t("session_loss_limit"), min_value=0.0, max_value=20.0,
                        value=float(showcase_settings.get("session_loss_limit_pct", policy.session_loss_limit_pct)) if showcase_active else float(policy.session_loss_limit_pct),
                        step=0.25, disabled=showcase_active, key=f"showcase-loss-limit-{preset_key}",
                    )
                with guard_settings[2]:
                    session_equity = st.number_input(
                        t("session_equity"), min_value=100.0, max_value=1_000_000.0,
                        value=float(showcase_settings.get("session_equity_usdt", policy.session_equity_usdt)) if showcase_active else float(policy.session_equity_usdt),
                        step=100.0, disabled=showcase_active, key=f"showcase-equity-{preset_key}",
                    )
            session_guard = dict(showcase.get("session_guard") or {})
            guard_return = float(session_guard.get("session_return_pct", 0) or 0)
            guard_pnl = float(session_guard.get("session_pnl_usdt", 0) or 0)
            guard_equity = float(session_guard.get("session_equity_usdt", session_equity) or session_equity)
            guard_profit_target = float(session_guard.get("profit_target_pct", session_profit_target) or 0)
            guard_loss_limit = float(session_guard.get("loss_limit_pct", session_loss_limit) or 0)
            guard_profit_usdt = guard_equity * guard_profit_target / 100.0
            guard_loss_usdt = guard_equity * guard_loss_limit / 100.0
            remaining_loss_pct = max(0.0, guard_return + guard_loss_limit)
            remaining_loss_usdt = guard_equity * remaining_loss_pct / 100.0
            with st.container(border=True):
                st.markdown(f'**{t("session_guard_title")}**')
                guard_metrics = st.columns(4)
                guard_metrics[0].metric(t("session_return"), f"{guard_return:+.3f}%", f"{guard_pnl:+.2f} USDT")
                guard_metrics[1].metric(t("session_profit_target"), f"+{guard_profit_target:.2f}%", f"+{guard_profit_usdt:.2f} USDT")
                guard_metrics[2].metric(t("loss_stop"), f"-{guard_loss_limit:.2f}%", f"-{guard_loss_usdt:.2f} USDT")
                guard_metrics[3].metric(t("remaining_loss_buffer"), f"{remaining_loss_pct:.3f}%", f"{remaining_loss_usdt:.2f} USDT")
                loss_used_pct = max(0.0, -guard_return)
                loss_progress = min(1.0, loss_used_pct / guard_loss_limit) if guard_loss_limit > 0 else 0.0
                st.progress(
                    loss_progress,
                    text=f'{t("loss_capacity_used")}: {loss_used_pct:.3f}% / {guard_loss_limit:.2f}%'
                )
                st.caption(t("guard_basis"))
                if guard_loss_limit <= 0:
                    st.warning(f'{t("loss_stop")}: {t("guard_disabled")}')
            showcase_metrics = st.columns(5)
            showcase_metrics[0].metric(t("system_health"), status_label(showcase.get("status") or "STOPPED"))
            showcase_metrics[1].metric(t("open_positions"), showcase.get("open_trades", 0))
            showcase_metrics[2].metric(t("trades"), showcase.get("closed_trades", 0))
            showcase_metrics[3].metric(t("accepted_signals"), (showcase.get("last_scan") or {}).get("accepted", 0))
            showcase_metrics[4].metric(t("next_scan"), format_time(showcase.get("next_scan_utc")))
            control_cols = st.columns(3)
            with control_cols[0]:
                if st.button("▶ " + t("start_showcase"), type="primary", use_container_width=True, disabled=showcase_active):
                    try:
                        start_showcase(
                            daily_trade_limit=0, scan_interval_seconds=int(scan_interval),
                            maximum_holding_minutes=int(holding_minutes), leverage=float(leverage),
                            risk_level=int(risk_level), analysis_depth=int(analysis_depth), market_mode=str(market_mode),
                            quality_mode=str(quality_mode), replay_timeframe=str(replay_timeframe),
                            break_even_trigger_r=float(break_even_trigger_r),
                            session_equity_usdt=float(session_equity),
                            session_profit_target_pct=float(session_profit_target),
                            session_loss_limit_pct=float(session_loss_limit),
                        )
                        st.success(t("showcase_started")); st.rerun()
                    except (RuntimeError, ValueError) as exc:
                        st.error(str(exc))
            with control_cols[1]:
                if st.button(t("stop_showcase"), use_container_width=True, disabled=not showcase_active or showcase.get("status") == "STOP_REQUESTED"):
                    try:
                        stop_showcase(); st.warning(t("showcase_stopping")); st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            with control_cols[2]:
                if st.button("↻ " + t("refresh_status"), use_container_width=True, key="showcase-refresh"):
                    st.rerun()
            if showcase_active:
                showcase_auto_refresh = st.toggle(
                    t("auto_refresh"), value=False, key="showcase-auto-refresh",
                    help="Optional status refresh every 20 seconds. Manual refresh remains available.",
                )
                if showcase_auto_refresh:
                    components.html("<script>setTimeout(function(){window.parent.location.reload();}, 20000);</script>", height=0)
            if session_guard:
                session_return = float(session_guard.get("session_return_pct", 0) or 0)
                profit_target = float(session_guard.get("profit_target_pct", 0) or 0)
                progress = min(1.0, max(0.0, session_return / profit_target)) if profit_target > 0 else 0.0
                st.progress(progress, text=f'{t("profit_guard")} · {t("session_return")}: {session_return:+.3f}% / {profit_target:.2f}%')
                guard_status = str(session_guard.get("status", "ACTIVE"))
                if guard_status == "PROFIT_TARGET_REACHED":
                    st.success(f'{t("profit_guard")}: PROFIT TARGET REACHED')
                elif guard_status == "LOSS_LIMIT_REACHED":
                    st.error(f'{t("profit_guard")}: LOSS LIMIT REACHED')
            performance = dict(showcase.get("performance") or {})
            session_performance = dict(performance.get("session") or {})
            if session_performance:
                with st.container(border=True):
                    st.markdown(f'**{t("performance_guard")}**')
                    maturity_profiles = dict(showcase.get("quality_maturity_profiles") or {})
                    maturity = dict(maturity_profiles.get(quality_mode) or showcase.get("quality_maturity") or {})
                    session_maturity = dict(maturity.get("session") or {})
                    organic_samples = int(session_maturity.get("organic_closed_trades", 0) or 0)
                    maturity_target = int(session_maturity.get("minimum_samples", 50) or 50)
                    if not session_maturity.get("mature", False):
                        st.info(f'{t("evidence_collecting")}: {organic_samples}/{maturity_target}')
                    else:
                        st.success(f'{t("evidence_mature")}: {organic_samples}/{maturity_target}')
                    st.progress(min(1.0, organic_samples / max(1, maturity_target)))
                    performance_cols = st.columns(5)
                    performance_cols[0].metric(t("sample_count"), int(session_performance.get("samples", 0) or 0))
                    performance_cols[1].metric("Win rate", f'{100 * float(session_performance.get("win_rate", 0) or 0):.1f}%')
                    performance_cols[2].metric(t("profit_factor"), f'{float(session_performance.get("profit_factor", 0) or 0):.2f}')
                    performance_cols[3].metric(t("expectancy"), f'{float(session_performance.get("expectancy_usdt", 0) or 0):+.3f} USDT')
                    performance_cols[4].metric(t("break_even_win_rate"), f'{100 * float(session_performance.get("break_even_win_rate", 0) or 0):.1f}%')
                    side_maturity = dict(maturity.get("side") or {})
                    if side_maturity:
                        st.caption(t("side_maturity"))
                        maturity_cols = st.columns(2)
                        for column, side in zip(maturity_cols, ("LONG", "SHORT")):
                            side_data = dict(side_maturity.get(side) or {})
                            samples = int(side_data.get("samples", 0) or 0)
                            minimum = int(side_data.get("minimum_samples", 0) or 0)
                            column.progress(min(1.0, samples / max(1, minimum)), text=f"{side}: {samples}/{minimum}")
                    mfe = dict(performance.get("losing_trade_mfe") or {})
                    if mfe:
                        calibration = dict(mfe.get("calibration") or {})
                        st.caption(
                            f'{t("mfe_calibration")}: N={int(mfe.get("samples", 0) or 0)} · '
                            f'P50={float(mfe.get("median_r", 0) or 0):.2f}R · P75={float(mfe.get("p75_r", 0) or 0):.2f}R · '
                            f'P90={float(mfe.get("p90_r", 0) or 0):.2f}R · {calibration.get("status", "—")}'
                        )
                    comparison = dict(performance.get("walk_forward_quality") or {})
                    if comparison:
                        with st.expander(t("quality_comparison")):
                            candidate = dict(comparison.get("candidate") or {})
                            baseline = dict(comparison.get("baseline") or {})
                            st.write(
                                f'Baseline: {100 * float(baseline.get("win_rate", 0) or 0):.1f}% / PF {float(baseline.get("profit_factor", 0) or 0):.2f} · '
                                f'Quality: {100 * float(candidate.get("win_rate", 0) or 0):.1f}% / PF {float(candidate.get("profit_factor", 0) or 0):.2f}'
                            )
                            st.caption(t("quality_gate_note"))
                            if float(candidate.get("profit_factor", 0) or 0) <= 1 or float(candidate.get("expectancy_usdt", 0) or 0) <= 0:
                                st.warning(t("quality_not_promoted"))
            last_scan = dict(showcase.get("last_scan") or {})
            if last_scan:
                with st.expander(t("scan_activity"), expanded=bool(last_scan.get("errors"))):
                    st.write(
                        f'{t("accepted_signals")}: {last_scan.get("accepted", 0)}/{last_scan.get("evaluated", 0)} · '
                        f'Opened: {last_scan.get("opened", 0)} · Mode: {last_scan.get("market_mode", "—")}'
                    )
                    last_policy = dict(last_scan.get("risk_policy") or {})
                    if last_policy:
                        st.write(
                            f'{t("analysis_depth")}: {last_policy.get("analysis_depth", "—")} · '
                            f'{t("technical_tools")}: {len(last_policy.get("technical_indicators") or [])} · '
                            f'{t("confluence")}: ≥ {last_policy.get("minimum_confluence_pct", "—")}%'
                        )
                    rejected = dict(last_scan.get("rejected") or {})
                    if rejected:
                        st.write(t("rejected_signals") + ": " + " · ".join(f"{key}={value}" for key, value in rejected.items()))
                    errors = list(last_scan.get("errors") or [])
                    if errors:
                        st.error(t("data_errors") + ": " + " | ".join(str(item.get("error")) for item in errors[-3:]))
            latest_technical = next((trade for trade in showcase_trades if trade.get("technical_v2")), None)
            if latest_technical:
                technical = dict(latest_technical.get("technical_v2") or {})
                with st.expander(t("technical_v2_report"), expanded=True):
                    report_cols = st.columns(3)
                    report_cols[0].metric(t("market_regime"), (technical.get("regime") or {}).get("label", "—"))
                    report_cols[1].metric(t("mtf_agreement"), f'{float(technical.get("timeframe_agreement", 0)):.0%}')
                    geometry = dict(technical.get("geometry") or {})
                    report_cols[2].metric(t("trade_geometry"), f'R:R {float(geometry.get("cost_adjusted_reward_risk", 0)):.2f}')
                    audit_cols = st.columns(3)
                    quality = dict(technical.get("data_quality") or {})
                    setup = dict(technical.get("setup") or {})
                    economics = dict(technical.get("economics") or {})
                    execution = dict(technical.get("execution") or {})
                    portfolio = dict(technical.get("portfolio") or {})
                    audit_cols[0].metric(t("data_quality"), quality.get("status", "—"), f'{float(quality.get("score", 0)):.0%}' if quality else None)
                    setup_labels = {
                        "BREAKOUT_VOLUME": "BREAKOUT",
                        "LIQUIDITY_SWEEP_REVERSAL": "SWEEP REV.",
                        "MOMENTUM_CONTINUATION": "MOMENTUM",
                        "RANGE_MEAN_REVERSION": "RANGE REV.",
                        "VOLATILITY_EXPANSION": "VOL EXP.",
                    }
                    audit_cols[1].metric(t("active_setup"), setup_labels.get(setup.get("name"), setup.get("name", "—")), setup.get("status") if setup else None)
                    audit_cols[2].metric(t("net_expected_value"), f'{float(economics.get("net_expected_value_pct", 0)):+.3f}%')
                    risk_cols = st.columns(3)
                    risk_cols[0].metric(t("execution_cost"), f'{float(execution.get("estimated_round_trip_cost_pct", 0)):.3f}%')
                    risk_cols[1].metric(t("portfolio_risk"), portfolio.get("status", "—"), f'x{float(portfolio.get("size_multiplier", 1)):.2f}')
                    calibration_status = str((technical.get("calibration") or {}).get("status", "—"))
                    calibration_label = {"UNCALIBRATED": "UNCALIB.", "NEEDS_REVIEW": "REVIEW"}.get(calibration_status, calibration_status)
                    risk_cols[2].metric(t("calibration_status"), calibration_label)
                    family_rows = list(technical.get("family_scores") or [])
                    if family_rows:
                        st.dataframe(
                            [{"Family": row.get("family"), "Score": row.get("score"), "Weight": row.get("weight"), "Agreement": row.get("agreement")} for row in family_rows],
                            use_container_width=True, hide_index=True,
                        )
                    st.write(t("decision_drivers") + ": " + " · ".join(technical.get("reasons") or ["—"]))
                    warnings = list(technical.get("warnings") or [])
                    if warnings:
                        st.warning(t("decision_warnings") + ": " + " · ".join(warnings))
                    from freakto.technical_v2.evaluator import evaluate_decisions
                    from freakto.technical_v2.promotion import promotion_recommendation
                    from freakto.technical_v2.validation import sequential_oos_report
                    closed_v2 = [trade for trade in showcase_trades if trade.get("status") == "CLOSED" and trade.get("technical_v2")]
                    evaluation = evaluate_decisions(closed_v2)
                    st.markdown("**" + t("session_evaluation") + "**")
                    evaluation_cols = st.columns(3)
                    evaluation_cols[0].metric(t("sample_count"), evaluation.get("samples", 0))
                    evaluation_cols[1].metric("Win rate", "—" if evaluation.get("win_rate") is None else f'{float(evaluation["win_rate"]):.1%}')
                    evaluation_cols[2].metric(t("expectancy"), "—" if evaluation.get("expectancy_pct") is None else f'{float(evaluation["expectancy_pct"]):+.3f}%')
                    attribution = dict(evaluation.get("family_attribution") or {})
                    if attribution:
                        st.bar_chart(attribution)
                    champion_rows = [trade for trade in showcase_trades if trade.get("status") == "CLOSED" and not trade.get("technical_v2")]
                    champion = evaluate_decisions(champion_rows)
                    validation = sequential_oos_report(closed_v2)
                    promotion = promotion_recommendation(champion, evaluation, validation)
                    promotion_cols = st.columns(2)
                    promotion_cols[0].metric(t("promotion_status"), promotion.get("status", "KEEP_RESEARCH"))
                    promotion_cols[1].metric(t("validation_stability"), f'{float(validation.get("stability", 0)):.0%}')
                    if promotion.get("blockers"):
                        st.info("Promotion blockers: " + " · ".join(promotion["blockers"]))
            card_paths = [Path(str(trade.get("latest_card"))) for trade in showcase_trades[:4] if trade.get("latest_card")]
            card_payloads = []
            for card_path in card_paths:
                try:
                    card_data = card_path.read_bytes()
                    with Image.open(BytesIO(card_data)) as candidate:
                        candidate.verify()
                    card_payloads.append((card_path, card_data))
                except (OSError, UnidentifiedImageError):
                    continue
            if card_payloads:
                section_intro(t("showcase_cards"), t("showcase_disclaimer"))
                card_columns = st.columns(len(card_payloads))
                for card_column, (card_path, card_data) in zip(card_columns, card_payloads):
                    with card_column:
                        st.image(card_data, use_column_width=True)
                        st.download_button(
                            t("download_card"),
                            data=card_data,
                            file_name=card_path.name,
                            mime="image/png",
                            use_container_width=True,
                            key=f"download-{card_path.stem}",
                        )
        top = st.columns([1.1, .9])
        with top[0]:
            workflow_card(t("forward_cycle"), t("forward_desc"), "FORWARD_SHADOW_CYCLE", key="start-forward", active=bool(active))
        with top[1]:
            with st.container(border=True):
                section_intro(t("paper_controls"), t("safe_note"))
                buttons = st.columns(2)
                with buttons[0]: run_command(t("preflight"), ["paper", "preflight"], key="paper-preflight")
                with buttons[1]: run_command(t("paper_status"), ["paper", "status"], key="paper-status")
                with st.expander(t("advanced")):
                    confirmed = st.checkbox(t("confirm_sensitive"), key="paper-confirm")
                    controls = st.columns(3)
                    with controls[0]: run_command(t("arm_research"), ["paper", "arm-research"], key="paper-arm", disabled=not confirmed)
                    with controls[1]: run_command(t("one_cycle"), ["paper", "cycle"], key="paper-cycle", disabled=not confirmed)
                    with controls[2]: run_command(t("disarm"), ["paper", "disarm"], key="paper-disarm", disabled=not confirmed)
        campaign = campaign_status()
        with st.container(border=True):
            section_intro(t("campaign"), t("forward_desc"))
            metrics([(t("days"), f'{float(campaign.get("elapsed_days", 0)):.2f}/{campaign.get("minimum_days", 60)}', campaign.get("target_end_utc") or "—", ""), (t("trades"), f'{campaign.get("closed_trades", 0)}/{campaign.get("minimum_closed_trades", 200)}', campaign.get("status"), ""), (t("cycles"), campaign.get("cycles", 0), campaign.get("campaign_id") or "—", ""), (t("paper"), snapshot["paper"]["mode"], t("live_off"), "good")])
            campaign_confirm = st.checkbox(t("confirm_sensitive"), key="campaign-confirm")
            cbuttons = st.columns(2)
            with cbuttons[0]:
                if st.button(t("campaign_start"), type="primary", use_container_width=True, disabled=not campaign_confirm or campaign.get("status") in CAMPAIGN_ACTIVE):
                    try: start_campaign(); st.rerun()
                    except RuntimeError as exc: st.error(str(exc))
            with cbuttons[1]:
                if st.button(t("campaign_stop"), use_container_width=True, disabled=campaign.get("status") not in {"STARTING", "RUNNING"}):
                    stop_campaign(); st.rerun()
    with research_tab:
        cols = st.columns(2)
        with cols[0]: workflow_card(t("airdrop"), t("airdrop_desc"), "AIRDROP_OUTCOMES", key="start-airdrop", active=bool(active))
        with cols[1]:
            with st.container(border=True):
                section_intro(t("cross_asset"), t("cross_desc"))
                rank_file = st.text_input(t("rank_input"), "data/cross_asset/opportunities.csv")
                if st.button(t("rank"), type="primary", use_container_width=True, disabled=bool(active), key="cross-rank"):
                    start_job("CROSS_ASSET_RANK", options={"input": rank_file})
                with st.expander(t("advanced")):
                    rankings = st.text_input(t("rankings_input"), "data/cross_asset/rankings.csv")
                    outcomes = st.text_input(t("outcomes_input"), "data/cross_asset/outcomes.csv")
                    if st.button(t("evaluate"), use_container_width=True, disabled=bool(active), key="cross-evaluate"):
                        start_job("CROSS_ASSET_EVALUATE", options={"rankings": rankings, "outcomes": outcomes})

elif page == "reports":
    page_header(t("reports_title"), t("reports_sub"), "FREAKTO / REPORTS")
    go_live = snapshot["go_live"]
    metrics([(t("recent_activity"), len(jobs), format_time(jobs[0].get("created_utc")) if jobs else "—", ""), (t("blockers"), len(go_live.get("blockers") or []), go_live["status"], "bad" if go_live["status"].startswith("BLOCKED") else "good"), (t("data"), snapshot["data"]["datasets"], format_time(snapshot["data"]["latest_utc"]), ""), (t("paper"), snapshot["paper"]["mode"], format_time(snapshot["paper"]["updated_utc"]), "")])
    action_cols = st.columns([1, 2])
    with action_cols[0]:
        if st.button(t("refresh_reports"), type="primary", use_container_width=True, disabled=bool(active)):
            start_job("REPORT_REFRESH")
    with action_cols[1]:
        blockers = go_live.get("blockers") or []
        if blockers:
            st.markdown(f'<div class="notice dashboard"><strong>{esc(t("attention"))}:</strong> {esc(blocker_label(blockers[0]))}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="recommend dashboard">{esc(t("ready"))}</div>', unsafe_allow_html=True)
    gate_tab, history_tab = st.tabs([t("readiness"), t("job_history")])
    with gate_tab:
        rows = [{t("gates"): blocker_label(gate.get("name")), t("result"): "PASS" if gate.get("passed") else "BLOCKED", t("current"): gate.get("actual"), t("required"): gate.get("required")} for gate in go_live.get("gates") or []]
        if rows: st.dataframe(rows, use_container_width=True, hide_index=True)
        with st.expander(t("blockers"), expanded=bool(go_live.get("blockers"))):
            for blocker in go_live.get("blockers") or []: st.write("• " + blocker_label(blocker))
    with history_tab:
        if not jobs:
            st.info(t("no_history"))
        else:
            table = [{"Job": job.get("job_id"), "Workflow": kind_label(job.get("kind")), t("result"): status_label(job.get("status")), t("progress"): f'{job.get("completed_steps", 0)}/{job.get("total_steps", 0)}', t("duration"): elapsed(job), t("started"): format_time(job.get("started_utc") or job.get("created_utc"))} for job in jobs]
            st.dataframe(table, use_container_width=True, hide_index=True)
            selected_id = st.selectbox(t("select_job"), [str(job["job_id"]) for job in jobs])
            selected = next(job for job in jobs if job.get("job_id") == selected_id)
            render_active_job(selected, controls=False)
            steps = [{"#": item.get("index"), t("current_step"): step_label(item.get("key")), t("result"): "PASS" if item.get("accepted") else "FAILED", "Exit": item.get("exit_code"), "Time": format_time(item.get("completed_utc"))} for item in selected.get("steps") or []]
            if steps: st.dataframe(steps, use_container_width=True, hide_index=True)
            controls = st.columns(2)
            with controls[0]:
                if st.button(t("cancel"), use_container_width=True, disabled=selected.get("status") not in ACTIVE, key="report-cancel"):
                    request_cancel(selected_id); st.rerun()
            with controls[1]:
                if st.button(t("retry"), use_container_width=True, disabled=selected.get("status") not in TERMINAL or bool(active), key="report-retry"):
                    try: retry_job(selected_id); st.rerun()
                    except (RuntimeError, ValueError) as exc: st.error(str(exc))
            with st.expander(t("log"), expanded=selected.get("status") in {"FAILED", "INTERRUPTED"}):
                st.code(job_log(selected_id) or "—", language="text")

else:
    page_header(t("settings_title"), t("settings_sub"), "FREAKTO / SETTINGS")
    scheduler = scheduler_status()
    metrics([(t("scheduler"), t("scheduler_running") if scheduler.get("status") == "RUNNING" else t("scheduler_stopped"), f'PID: {scheduler.get("pid") or "—"}', "good" if scheduler.get("status") == "RUNNING" else ""), (t("automations"), len(enabled_automations), f'{len(automations)} {t("schedules")}', ""), (t("paper"), snapshot["paper"]["mode"], t("live_off"), "good"), (t("system_health"), t("ready"), t("safe"), "good")])
    automation_tab, safety_tab, technical_tab = st.tabs([t("automations"), t("safety_contract"), t("technical")])
    with automation_tab:
        st.info(t("automation_note"))
        for item in automations:
            automation_title, automation_copy = AUTOMATION_LABELS[str(item["id"])]
            with st.container(border=True):
                columns = st.columns([1.4, .55, .6, .55])
                with columns[0]:
                    section_intro(localized(automation_title), localized(automation_copy))
                    status_rows([(t("last_run"), format_time(item.get("last_started_utc"))), (t("next_run"), format_time(item.get("next_run_utc")))])
                with columns[1]:
                    enabled = st.toggle(t("enabled"), value=bool(item.get("enabled")), key=f'automation-enabled-{item["id"]}')
                with columns[2]:
                    interval = st.number_input(t("interval"), min_value=1, max_value=720, value=int(item["interval_hours"]), key=f'automation-interval-{item["id"]}')
                with columns[3]:
                    if st.button(t("save"), use_container_width=True, key=f'automation-save-{item["id"]}'):
                        set_automation(str(item["id"]), enabled=enabled, interval_hours=int(interval))
                        if enabled: ensure_scheduler_running()
                        st.success(t("saved")); st.rerun()
                    if st.button(t("run_now"), use_container_width=True, disabled=bool(active), key=f'automation-run-{item["id"]}'):
                        try: run_automation_now(str(item["id"])); st.rerun()
                        except (RuntimeError, ValueError) as exc: st.error(str(exc))
    with safety_tab:
        st.success(t("safety_body"))
        status_rows([("LIVE_TRADING_ENABLED", "false"), ("REAL_CAPITAL_ENABLED", "false"), ("Capital allocation", "0.0%"), ("Go-live action", "REPORT ONLY")])
    with technical_tab:
        section_intro(t("guide"), t("guide_body"))
        status_rows([(t("runtime_path"), ROOT / ".freakto-runtime" / "control-center"), ("Data", snapshot["data"]["path"]), ("Artifacts", snapshot["runtime"]["json_artifacts"])])
        with st.expander(t("technical")):
            st.code(".\\run_control_center.bat", language="powershell")
            st.code(str(ROOT / "logs" / "paper_launch_v2" / "go_live_evidence.json"), language="text")

result = st.session_state.get("last_result")
if result is not None:
    with st.expander(t("latest_result"), expanded=not result.ok):
        if result.ok: st.success(f'PASS · exit {result.exit_code}')
        elif result.exit_code == 2: st.warning(f'BLOCKED · exit {result.exit_code}')
        else: st.error(f'FAILED · exit {result.exit_code}')
        if result.stdout.strip(): st.code(result.stdout[-8000:], language="text")
        if result.stderr.strip(): st.code(result.stderr[-4000:], language="text")
