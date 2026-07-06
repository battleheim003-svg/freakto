"""
engine.daily_report

Freakto Daily AI Report Engine - v4.6.1

این ماژول خروجی Portfolio Scanner و Market Breadth را به یک گزارش مدیریتی
کوتاه، قابل خواندن و تصمیم‌محور تبدیل می‌کند.

نکته: این نسخه به API هوش مصنوعی خارجی وابسته نیست؛ گزارش را به صورت deterministic
و بر اساس داده‌های خود موتور Freakto تولید می‌کند. بعداً می‌توان همین خروجی را
به یک LLM هم داد تا متن طبیعی‌تر تولید کند.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from .intelligence import build_portfolio_intelligence


REPORTS_DIR = Path("logs") / "reports"


@dataclass
class DailyReport:
    created_at_utc: str
    title: str
    executive_summary: List[str] = field(default_factory=list)
    market_context: List[str] = field(default_factory=list)
    intelligence_narrative: List[str] = field(default_factory=list)
    top_candidates: List[str] = field(default_factory=list)
    risk_notes: List[str] = field(default_factory=list)
    action_plan: List[str] = field(default_factory=list)
    raw_text: str = ""


def _fmt_pct(value) -> str:
    try:
        return f"{float(value):.1f}%"
    except Exception:
        return "0.0%"


def _safe(value, default="-"):
    return value if value not in {None, ""} else default


def _top_items(result, limit=3):
    return result.ranked_items[:limit]


def _direction_fa(side: str) -> str:
    if side == "LONG":
        return "صعودی"
    if side == "SHORT":
        return "نزولی"
    return "خنثی"


def _recommendation_fa(rec: str) -> str:
    mapping = {
        "ELITE": "فرصت بسیار قوی",
        "ACTIONABLE": "قابل بررسی",
        "WATCHLIST": "زیرنظر",
        "MONITOR": "مانیتور",
        "IGNORE": "نادیده گرفتن فعلی",
    }
    return mapping.get(rec, rec)


def build_daily_report(result, symbols=None) -> DailyReport:
    now = datetime.now(timezone.utc).isoformat()
    symbols = symbols or [item.symbol for item in result.items]
    breadth = result.market_breadth

    title = "Freakto Daily Market Report v4.6.1"
    intelligence = []
    executive = []
    context = []
    candidates = []
    risks = []
    plan = []
    intelligence = build_portfolio_intelligence(result) if getattr(result, "items", None) is not None else []

    if not result.items:
        executive.append("هیچ داده معتبری برای ساخت گزارش روزانه در دسترس نیست.")
        risks.append("اسکن پورتفو نتیجه‌ای برنگردانده است؛ وضعیت اتصال به صرافی‌ها و لیست نمادها بررسی شود.")
        plan.append("فعلاً هیچ اقدامی پیشنهاد نمی‌شود.")
    else:
        if breadth is not None:
            executive.append(
                f"حالت کلی بازار {breadth.market_mode} با Risk Tone برابر {breadth.risk_tone} است. "
                f"Market Agreement برابر {breadth.market_agreement}/100 و Opportunity Strength برابر {breadth.opportunity_strength}/100 است."
            )
            executive.append(
                f"پهنای بازار: Bullish {_fmt_pct(breadth.bullish_pct)}، "
                f"Bearish {_fmt_pct(breadth.bearish_pct)}، Neutral {_fmt_pct(breadth.neutral_pct)}."
            )
            executive.append(
                f"میانگین Opportunity Score برابر {breadth.average_opportunity_score:.1f} و "
                f"میانگین Confidence برابر {breadth.average_confidence:.1f}% است."
            )

            context.extend(breadth.summary[:3])
            risks.extend(breadth.warnings[:4])

            if breadth.market_mode == "RISK_ON":
                plan.append("بازار تمایل به ریسک‌پذیری دارد؛ فقط نمادهای هم‌راستا با MTF و Quality مناسب بررسی شوند.")
            elif breadth.market_mode == "RISK_OFF":
                plan.append("بازار در وضعیت ریسک‌گریز است؛ از لانگ‌های ضعیف دوری شود و تمرکز روی حفاظت سرمایه باشد.")
            elif breadth.market_mode == "NEUTRAL":
                plan.append("بازار جهت جمعی قوی ندارد؛ اولویت با مانیتور، صبر و انتظار برای شکست معتبر است.")
            else:
                plan.append("بازار ترکیبی است؛ فقط فرصت‌هایی بررسی شوند که هم‌زمان Score، Confidence و MTF مناسب دارند.")

        real = result.elite_items or result.actionable_items or result.watchlist_items
        if real:
            executive.append(f"{len(real)} کاندید جدی در پورتفو پیدا شد.")
            for item in real[:5]:
                candidates.append(
                    f"{item.symbol}: {_direction_fa(item.side)} | Opp {item.opportunity_score} | "
                    f"Score {item.score} | Confidence {item.confidence}% | "
                    f"Trade {item.trade_quality_grade} | RR {item.first_rr} | "
                    f"Recommendation {_recommendation_fa(item.recommendation)}."
                )
            plan.append("برای کاندیدهای جدی، Entry/Stop/RR و Position Size قبل از هر تصمیم بررسی شود.")
        else:
            executive.append("هیچ فرصت Actionable یا Watchlist جدی در این اسکن دیده نشد.")
            closest = _top_items(result, limit=3)
            if closest:
                candidates.append("نزدیک‌ترین گزینه‌ها برای مانیتور:")
                for item in closest:
                    candidates.append(
                        f"{item.symbol}: {item.side} | Opp {item.opportunity_score} | "
                        f"Score {item.score} | Confidence {item.confidence}% | "
                        f"MTF {_safe(item.mtf_direction)}/{item.mtf_consensus}% | Rec {_recommendation_fa(item.recommendation)}."
                    )
            plan.append("تا زمانی که MTF و Volume تأیید ندهند، ورود جدی پیشنهاد نمی‌شود.")

        failed = getattr(result, "failed_symbols", []) or []
        if failed:
            risks.append(f"برخی نمادها اسکن نشدند: {', '.join(failed[:8])}")

        if not risks:
            risks.append("ریسک خاصی فراتر از هشدارهای داخلی موتور مشاهده نشد؛ با این حال خروجی توصیه مالی نیست.")

    report = DailyReport(
        created_at_utc=now,
        title=title,
        executive_summary=executive,
        market_context=context,
        intelligence_narrative=intelligence,
        top_candidates=candidates,
        risk_notes=risks,
        action_plan=plan,
    )
    report.raw_text = format_daily_report_console(report)
    return report


def format_daily_report_console(report: DailyReport) -> str:
    lines = []
    lines.append("\n" + "=" * 110)
    lines.append("🧠 Freakto Daily AI Report v4.6.1")
    lines.append("=" * 110)
    lines.append(f"Created UTC: {report.created_at_utc}")
    lines.append("")

    lines.append("Executive Summary:")
    for item in report.executive_summary:
        lines.append(f"- {item}")

    if report.market_context:
        lines.append("")
        lines.append("Market Context:")
        for item in report.market_context:
            lines.append(f"- {item}")

    if report.intelligence_narrative:
        lines.append("")
        lines.append("Intelligence Narrative:")
        for item in report.intelligence_narrative:
            lines.append(f"- {item}")

    if report.top_candidates:
        lines.append("")
        lines.append("Candidates:")
        for item in report.top_candidates:
            lines.append(f"- {item}")

    if report.risk_notes:
        lines.append("")
        lines.append("Risk Notes:")
        for item in report.risk_notes:
            lines.append(f"⚠️ {item}")

    if report.action_plan:
        lines.append("")
        lines.append("Action Plan:")
        for item in report.action_plan:
            lines.append(f"✓ {item}")

    lines.append("")
    lines.append("این گزارش توصیه مالی نیست؛ فقط خلاصه تصمیم‌یار بر اساس موتور Freakto است.")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_daily_report_telegram(report: DailyReport) -> str:
    lines = [
        "🧠 *Freakto Daily AI Report v4.6.1*",
        "",
        "*Executive Summary:*",
    ]

    for item in report.executive_summary[:4]:
        lines.append(f"- {item}")

    if report.intelligence_narrative:
        lines.append("")
        lines.append("*Intelligence Narrative:*")
        for item in report.intelligence_narrative[:4]:
            lines.append(f"- {item}")

    if report.top_candidates:
        lines.append("")
        lines.append("*Candidates:*")
        for item in report.top_candidates[:6]:
            lines.append(f"- {item}")

    if report.risk_notes:
        lines.append("")
        lines.append("*Risk Notes:*")
        for item in report.risk_notes[:4]:
            lines.append(f"⚠️ {item}")

    if report.action_plan:
        lines.append("")
        lines.append("*Action Plan:*")
        for item in report.action_plan[:3]:
            lines.append(f"✓ {item}")

    lines.append("")
    lines.append("این گزارش توصیه مالی نیست؛ فقط خلاصه تصمیم‌یار Freakto است.")
    return "\n".join(lines)


def save_daily_report(report: DailyReport, filename: str | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if filename is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"daily_report_{stamp}.md"

    path = REPORTS_DIR / filename
    path.write_text(report.raw_text or format_daily_report_console(report), encoding="utf-8")
    return path
