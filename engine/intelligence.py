"""
engine.intelligence

Freakto Intelligence Layer - v4.6.1

این ماژول یک لایه توضیح‌پذیر روی خروجی Decision Engine می‌سازد:
- Market Narrative
- Signal Conflict Analysis
- Explainable Score Map
- Trade Thesis
- Action Plan

این نسخه به API خارجی وابسته نیست و کاملاً deterministic است.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class SignalConflict:
    title: str
    severity: str = "LOW"  # LOW / MEDIUM / HIGH
    explanation: str = ""


@dataclass
class ScoreExplanationItem:
    component: str
    points: int
    max_points: int
    role: str
    interpretation: str


@dataclass
class IntelligenceReport:
    narrative: List[str] = field(default_factory=list)
    conflicts: List[SignalConflict] = field(default_factory=list)
    score_map: List[ScoreExplanationItem] = field(default_factory=list)
    thesis_title: str = "Neutral Thesis"
    thesis_evidence: List[str] = field(default_factory=list)
    thesis_against: List[str] = field(default_factory=list)
    conclusion: str = ""
    action_plan: List[str] = field(default_factory=list)
    confidence_note: str = ""

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


def _points(opportunity, name: str) -> int:
    try:
        return int(opportunity.component_points(name) or 0)
    except Exception:
        return 0


def _component(opportunity, name: str):
    for component in getattr(opportunity, "components", []) or []:
        if component.name == name:
            return component
    return None


def _mtf_direction(opportunity) -> str:
    return str(getattr(opportunity, "raw", {}).get("mtf_direction") or "")


def _mtf_consensus(opportunity) -> int:
    try:
        return int(getattr(opportunity, "raw", {}).get("mtf_consensus") or 0)
    except Exception:
        return 0


def _regime(opportunity) -> str:
    return str(getattr(opportunity, "raw", {}).get("regime_label") or "UNKNOWN")


def _direction_word(side: str) -> str:
    if side == "LONG":
        return "صعودی"
    if side == "SHORT":
        return "نزولی"
    return "خنثی"


def _component_role(name: str) -> str:
    roles = {
        "Trend": "جهت اصلی بازار",
        "Momentum": "قدرت حرکت کوتاه‌مدت",
        "Volume": "تأیید مشارکت بازار",
        "Structure": "ساختار سقف/کف و شکست‌ها",
        "Regime Adjustment": "وضعیت کلی بازار",
        "Risk Penalty": "کیفیت ریسک",
        "Learning Override": "تنظیمات یادگیری امن",
        "Adaptive Adjustment": "تطبیق با رژیم بازار",
        "Historical Edge": "حافظه تاریخی شرایط مشابه",
        "MTF Consensus": "هم‌راستایی چندتایم‌فریم",
    }
    return roles.get(name, "عامل کمکی")


def _interpret_component(name: str, points: int, max_points: int) -> str:
    if name == "Risk Penalty":
        if points <= -10:
            return "ریسک فعال و قابل توجه است."
        if points < 0:
            return "ریسک خفیف تا متوسط روی تصمیم فشار می‌آورد."
        return "ریسک خاصی از این بخش دیده نمی‌شود."

    if max_points <= 0:
        return "این عامل فقط تعدیل‌کننده است."

    ratio = points / max_points
    if points < 0:
        return "این عامل در جهت کاهش کیفیت تصمیم عمل می‌کند."
    if ratio >= 0.75:
        return "این عامل قوی و تأییدکننده است."
    if ratio >= 0.45:
        return "این عامل متوسط است و بخشی از سناریو را تأیید می‌کند."
    if points > 0:
        return "این عامل ضعیف اما غیرصفر است."
    return "این عامل هنوز تأیید کافی نداده است."


def build_score_map(opportunity) -> List[ScoreExplanationItem]:
    items: List[ScoreExplanationItem] = []
    for component in getattr(opportunity, "components", []) or []:
        items.append(
            ScoreExplanationItem(
                component=component.name,
                points=int(component.points or 0),
                max_points=int(component.max_points or 0),
                role=_component_role(component.name),
                interpretation=_interpret_component(component.name, int(component.points or 0), int(component.max_points or 0)),
            )
        )
    return items


def detect_signal_conflicts(opportunity) -> List[SignalConflict]:
    conflicts: List[SignalConflict] = []
    side = getattr(opportunity, "side", "NEUTRAL")
    trend = _points(opportunity, "Trend")
    momentum = _points(opportunity, "Momentum")
    volume = _points(opportunity, "Volume")
    structure = _points(opportunity, "Structure")
    risk = _points(opportunity, "Risk Penalty")
    mtf_direction = _mtf_direction(opportunity)
    mtf_consensus = _mtf_consensus(opportunity)
    regime = _regime(opportunity)

    if side in {"LONG", "SHORT"} and mtf_direction == "NEUTRAL" and mtf_consensus >= 60:
        conflicts.append(SignalConflict(
            title="Bias جهت‌دار اما MTF خنثی است",
            severity="HIGH" if mtf_consensus >= 80 else "MEDIUM",
            explanation=f"سناریوی {side} در تایم‌فریم اصلی دیده شده، اما اجماع چندتایم‌فریمی هنوز آن را تأیید نمی‌کند: {mtf_consensus}% NEUTRAL.",
        ))

    if side in {"LONG", "SHORT"} and mtf_direction in {"LONG", "SHORT"} and mtf_direction != side:
        conflicts.append(SignalConflict(
            title="تضاد مستقیم با Multi-Timeframe",
            severity="HIGH",
            explanation=f"Bias اصلی {side} است اما MTF جهت {mtf_direction} را نشان می‌دهد.",
        ))

    if side in {"LONG", "SHORT"} and volume <= 0 and (trend >= 20 or structure >= 6):
        conflicts.append(SignalConflict(
            title="ساختار/روند بدون تأیید حجم",
            severity="MEDIUM",
            explanation="Trend یا Structure بخشی از سناریو را تأیید می‌کند، اما Volume هنوز مشارکت کافی نشان نداده است.",
        ))

    if trend >= 20 and momentum < 15:
        conflicts.append(SignalConflict(
            title="روند قوی اما مومنتوم ضعیف",
            severity="MEDIUM",
            explanation="جهت کلی بازار قابل مشاهده است، اما قدرت حرکت کوتاه‌مدت هنوز هم‌راستا نیست.",
        ))

    if risk <= -8:
        conflicts.append(SignalConflict(
            title="ریسک روی کیفیت تصمیم فشار می‌آورد",
            severity="HIGH" if risk <= -12 else "MEDIUM",
            explanation=f"Risk Penalty برابر {risk} است و کیفیت ورود را محدود می‌کند.",
        ))

    if side == "LONG" and regime == "TRENDING_BEAR":
        conflicts.append(SignalConflict(
            title="لانگ خلاف رژیم نزولی",
            severity="HIGH",
            explanation="Market Regime نزولی است و با سناریوی LONG تضاد دارد.",
        ))

    if side == "SHORT" and regime == "TRENDING_BULL":
        conflicts.append(SignalConflict(
            title="شورت خلاف رژیم صعودی",
            severity="HIGH",
            explanation="Market Regime صعودی است و با سناریوی SHORT تضاد دارد.",
        ))

    if side == "NEUTRAL" and (trend >= 18 or momentum >= 18) and volume <= 0:
        conflicts.append(SignalConflict(
            title="نشانه‌های اولیه بدون مشارکت بازار",
            severity="LOW",
            explanation="برخی نشانه‌های روند یا مومنتوم دیده می‌شود، اما نبود Volume باعث شده خروجی نهایی خنثی بماند.",
        ))

    return conflicts


def _build_narrative(opportunity, conflicts: List[SignalConflict]) -> List[str]:
    side = getattr(opportunity, "side", "NEUTRAL")
    score = int(getattr(opportunity, "score", 0) or 0)
    confidence = getattr(getattr(opportunity, "confidence", None), "value", 0)
    confidence_label = getattr(getattr(opportunity, "confidence", None), "label", "Low")
    regime = _regime(opportunity)
    mtf_direction = _mtf_direction(opportunity) or "UNKNOWN"
    mtf_consensus = _mtf_consensus(opportunity)
    volume = _points(opportunity, "Volume")
    historical = _points(opportunity, "Historical Edge")

    lines = []
    lines.append(
        f"بازار در تایم‌فریم {getattr(opportunity, 'timeframe', '-') } فعلاً Bias {_direction_word(side)} دارد؛ Score برابر {score}/100 و Confidence برابر {confidence}% ({confidence_label}) است."
    )
    lines.append(
        f"رژیم بازار {regime} است و اجماع چندتایم‌فریمی {mtf_direction}/{mtf_consensus}% را نشان می‌دهد."
    )

    if volume <= 0:
        lines.append("مهم‌ترین محدودیت فعلی، نبود تأیید Volume است؛ یعنی حرکت هنوز مشارکت قوی بازار را نشان نمی‌دهد.")
    elif volume < 8:
        lines.append("Volume کمی بهبود دارد، اما هنوز برای تأیید شکست یا ادامه حرکت قوی کافی نیست.")
    else:
        lines.append("Volume بخشی از سناریو را تأیید می‌کند و کیفیت حرکت بهتر از حالت عادی است.")

    if historical > 4:
        lines.append("حافظه تاریخی برای شرایط مشابه Edge مثبت نشان می‌دهد و از سناریوی فعلی حمایت می‌کند.")
    elif historical < 0:
        lines.append("حافظه تاریخی برای شرایط مشابه هشدار می‌دهد و کیفیت فرصت را پایین می‌آورد.")
    else:
        lines.append("حافظه تاریخی در این وضعیت هنوز مزیت قوی یا منفی قابل اتکا نشان نمی‌دهد.")

    if conflicts:
        high_count = sum(1 for conflict in conflicts if conflict.severity == "HIGH")
        if high_count:
            lines.append(f"در سیگنال‌ها {high_count} تضاد مهم دیده می‌شود؛ بنابراین تصمیم باید محافظه‌کارانه تفسیر شود.")
        else:
            lines.append("چند تضاد خفیف/متوسط در سیگنال‌ها وجود دارد، اما تضاد بحرانی دیده نمی‌شود.")
    else:
        lines.append("سیگنال‌ها از نظر داخلی تضاد مهمی نشان نمی‌دهند.")

    return lines


def _build_thesis(opportunity, conflicts: List[SignalConflict]) -> Tuple[str, List[str], List[str], str, List[str]]:
    side = getattr(opportunity, "side", "NEUTRAL")
    actionability = getattr(opportunity, "actionability_label", "MONITOR_ONLY")

    evidence = []
    against = []
    plan = []

    for component in getattr(opportunity, "components", []) or []:
        if component.points > 0:
            for reason in component.reasons[:2]:
                if reason not in evidence:
                    evidence.append(reason)
        if component.points <= 0:
            for warning in component.warnings[:2]:
                if warning not in against:
                    against.append(warning)

    for conflict in conflicts[:4]:
        text = f"{conflict.title}: {conflict.explanation}"
        if text not in against:
            against.append(text)

    if side == "LONG":
        title = "Bullish Thesis"
    elif side == "SHORT":
        title = "Bearish Thesis"
    else:
        title = "Neutral / Monitor Thesis"

    if actionability in {"ACTIONABLE", "HIGH_ACTIONABILITY"}:
        conclusion = "سناریو از نظر موتور قابل بررسی است، اما اجرای آن همچنان به مدیریت ریسک، Entry و Stop معتبر نیاز دارد."
        plan.append("قبل از تصمیم، Entry/Stop/R:R و اندازه موقعیت بررسی شود.")
        plan.append("در صورت تضعیف Volume یا MTF، سناریو دوباره ارزیابی شود.")
    elif actionability == "WATCHLIST":
        conclusion = "سناریو ارزش زیرنظر گرفتن دارد، اما هنوز تأیید کافی برای ورود جدی ندارد."
        plan.append("منتظر تأیید Volume، شکست ساختاری یا هم‌راستایی بهتر MTF بمان.")
        plan.append("اگر Score و Confidence هم‌زمان بهتر شدند، دوباره ارزیابی شود.")
    else:
        conclusion = "فعلاً خروجی بیشتر حالت مانیتور دارد؛ ورود جدی توسط موتور تأیید نشده است."
        plan.append("فعلاً تمرکز روی مشاهده بازار و جلوگیری از ورود احساسی باشد.")
        plan.append("فقط اگر MTF، Volume و Structure هم‌زمان بهتر شدند، سناریو دوباره بررسی شود.")

    if not evidence:
        evidence.append("شواهد مثبت کافی برای ساخت Thesis جهت‌دار دیده نمی‌شود.")
    if not against:
        against.append("هشدار مهمی فراتر از ریسک‌های عمومی بازار دیده نمی‌شود.")

    return title, evidence[:6], against[:6], conclusion, plan[:5]


def build_intelligence_report(opportunity) -> IntelligenceReport:
    conflicts = detect_signal_conflicts(opportunity)
    score_map = build_score_map(opportunity)
    title, evidence, against, conclusion, plan = _build_thesis(opportunity, conflicts)
    narrative = _build_narrative(opportunity, conflicts)

    confidence = getattr(getattr(opportunity, "confidence", None), "value", 0)
    if confidence >= 70:
        confidence_note = "Confidence خوب است؛ با این حال نتیجه همچنان احتمالاتی است."
    elif confidence >= 45:
        confidence_note = "Confidence متوسط است؛ بخشی از سناریو تأیید شده اما هنوز کامل نیست."
    else:
        confidence_note = "Confidence پایین است؛ خروجی بیشتر نقش مانیتور و هشدار دارد."

    return IntelligenceReport(
        narrative=narrative,
        conflicts=conflicts,
        score_map=score_map,
        thesis_title=title,
        thesis_evidence=evidence,
        thesis_against=against,
        conclusion=conclusion,
        action_plan=plan,
        confidence_note=confidence_note,
    )


def format_intelligence_console(report: IntelligenceReport) -> str:
    lines = []
    lines.append("\n" + "=" * 70)
    lines.append("🧠 Freakto Intelligence Layer v4.6.1")
    lines.append("=" * 70)

    lines.append("Market Narrative:")
    for item in report.narrative:
        lines.append(f"- {item}")

    if report.conflicts:
        lines.append("")
        lines.append("Signal Conflicts:")
        for conflict in report.conflicts[:6]:
            icon = "🔴" if conflict.severity == "HIGH" else "🟠" if conflict.severity == "MEDIUM" else "🟡"
            lines.append(f"{icon} {conflict.title} [{conflict.severity}]")
            lines.append(f"  {conflict.explanation}")

    lines.append("")
    lines.append("Explainable Score Map:")
    for item in report.score_map[:12]:
        sign = "+" if item.points > 0 else ""
        lines.append(f"- {item.component}: {sign}{item.points}/{item.max_points} | {item.role} | {item.interpretation}")

    lines.append("")
    lines.append(report.thesis_title + ":")
    lines.append("Evidence:")
    for item in report.thesis_evidence:
        lines.append(f"  ✓ {item}")
    lines.append("Against / Risks:")
    for item in report.thesis_against:
        lines.append(f"  ⚠ {item}")
    lines.append(f"Conclusion: {report.conclusion}")

    lines.append("")
    lines.append("Action Plan:")
    for item in report.action_plan:
        lines.append(f"  → {item}")
    lines.append(f"Confidence Note: {report.confidence_note}")
    lines.append("=" * 70)
    return "\n".join(lines)


def format_intelligence_telegram(report: IntelligenceReport) -> List[str]:
    lines = ["🧠 *Freakto Intelligence Layer v4.6.1*"]
    lines.append("")
    lines.append("*Market Narrative:*")
    for item in report.narrative[:4]:
        lines.append(f"- {item}")

    if report.conflicts:
        lines.append("")
        lines.append("*Signal Conflicts:*")
        for conflict in report.conflicts[:4]:
            icon = "🔴" if conflict.severity == "HIGH" else "🟠" if conflict.severity == "MEDIUM" else "🟡"
            lines.append(f"{icon} {conflict.title}: {conflict.explanation}")

    lines.append("")
    lines.append(f"*{report.thesis_title}:*")
    lines.append("Evidence:")
    for item in report.thesis_evidence[:4]:
        lines.append(f"✓ {item}")
    lines.append("Against / Risks:")
    for item in report.thesis_against[:4]:
        lines.append(f"⚠️ {item}")
    lines.append(f"Conclusion: {report.conclusion}")

    lines.append("")
    lines.append("*Action Plan:*")
    for item in report.action_plan[:3]:
        lines.append(f"→ {item}")
    return lines


def build_portfolio_intelligence(result) -> List[str]:
    """خلاصه هوشمند سطح پورتفو برای Daily Report و Telegram."""
    lines: List[str] = []
    breadth = getattr(result, "market_breadth", None)
    ranked = getattr(result, "ranked_items", []) or []

    if breadth is not None:
        lines.append(
            f"Market Mode برابر {breadth.market_mode} و Risk Tone برابر {breadth.risk_tone} است؛ "
            f"Market Agreement {breadth.market_agreement}/100 و Opportunity Strength {breadth.opportunity_strength}/100 است."
        )
        if breadth.market_mode == "RISK_ON":
            lines.append("روایت کلی بازار متمایل به ریسک‌پذیری است، اما فقط نمادهایی ارزش بررسی دارند که MTF و Volume هم‌راستا باشند.")
        elif breadth.market_mode == "RISK_OFF":
            lines.append("روایت کلی بازار ریسک‌گریز است؛ اولویت با حفاظت سرمایه و اجتناب از لانگ‌های ضعیف است.")
        elif breadth.market_mode == "MIXED":
            lines.append("بازار روایت واحد ندارد؛ بخشی از نمادها نشانه‌های صعودی دارند اما هم‌راستایی جمعی کافی نیست.")
        else:
            lines.append(
                "بازار عمدتاً خنثی است؛ اگر Market Agreement بالا باشد، یعنی توافق روی خنثی بودن زیاد است، "
                "نه اینکه فرصت معاملاتی قوی وجود دارد."
            )

    if ranked:
        leader = ranked[0]
        lines.append(
            f"نزدیک‌ترین کاندید فعلی {leader.symbol} با Bias {leader.side} و Opportunity {leader.opportunity_score} است؛ Recommendation آن {leader.recommendation} است."
        )
        if leader.mtf_direction == "NEUTRAL":
            lines.append("حتی نزدیک‌ترین کاندید هم هنوز از تایم‌فریم‌های بالاتر تأیید جهت‌دار نگرفته است.")
        elif leader.mtf_direction == leader.side:
            lines.append("کاندید اول از نظر MTF هم‌راستا است و در صورت بهبود Volume/Confidence باید جدی‌تر بررسی شود.")

    if not lines:
        lines.append("داده کافی برای ساخت روایت پورتفو وجود ندارد.")

    return lines[:5]
