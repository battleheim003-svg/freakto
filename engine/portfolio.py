"""
engine.portfolio

Portfolio Scanner models and ranking helpers - v4.6.1

این ماژول خروجی چند نماد را رتبه‌بندی می‌کند تا Freakto بتواند بهترین
وضعیت‌های بازار را از بین چند Symbol پیدا کند.

نسخه v4.6.1:
- Opportunity Ranking Engine v2
- Smart Watchlist
- Elite Opportunity Filter
- Portfolio Telegram Report v2
- Market Breadth Engine
- Daily AI Report Engine
- Trade Consistency Guard for actionable/watchlist recommendations
- Paper Trading metadata fields
- Trade Readiness awareness
"""

from dataclasses import dataclass, field
from typing import List

from .trade_quality import build_trade_intelligence_card
from .market_breadth import MarketBreadthResult, format_breadth_console, format_breadth_telegram
from .intelligence import build_intelligence_report


ACTIONABILITY_BONUS = {
    "HIGH_ACTIONABILITY": 24,
    "ACTIONABLE": 18,
    "WATCHLIST": 7,
    "NOT_ACTIONABLE": -8,
    "MONITOR_ONLY": -16,
}

SIDE_PRIORITY = {
    "LONG": 2,
    "SHORT": 2,
    "NEUTRAL": 0,
}

RISK_ADJUSTMENT = {
    "Low": 4,
    "Medium": -2,
    "High": -10,
    "Unknown": -4,
}


@dataclass
class PortfolioItem:
    symbol: str
    timeframe: str
    side: str
    score: int
    confidence: int
    confidence_label: str
    risk_label: str
    actionability: str
    regime: str = ""
    mtf_direction: str = ""
    mtf_consensus: int = 0
    mtf_quality: str = ""
    rank_score: float = 0.0
    opportunity_score: float = 0.0
    quality_label: str = "Ignore"
    quality_stars: str = "⭐"
    recommendation: str = "IGNORE"
    provider: str = ""
    price: float = 0.0
    decision_timestamp: str = ""
    entry_zone: str = ""
    stop_zone: str = ""
    targets: List[str] = field(default_factory=list)
    trade_quality_grade: str = "-"
    trade_quality_score: int = 0
    first_rr: float = 0.0
    best_rr: float = 0.0
    recommended_risk_pct: float = 0.0
    position_notional: float = 0.0
    expected_drawdown_pct: float = 0.0
    notes: List[str] = field(default_factory=list)

    @property
    def is_directional(self) -> bool:
        return self.side in {"LONG", "SHORT"}

    @property
    def is_elite(self) -> bool:
        return self.recommendation == "ELITE"

    @property
    def is_actionable_candidate(self) -> bool:
        return self.recommendation in {"ELITE", "ACTIONABLE"}

    @property
    def is_watchlist_candidate(self) -> bool:
        return self.recommendation in {"ELITE", "ACTIONABLE", "WATCHLIST"}


@dataclass
class PortfolioScanResult:
    items: List[PortfolioItem] = field(default_factory=list)
    failed_symbols: List[str] = field(default_factory=list)
    market_breadth: MarketBreadthResult | None = None

    @property
    def ranked_items(self) -> List[PortfolioItem]:
        return sorted(
            self.items,
            key=lambda item: (
                item.opportunity_score,
                item.rank_score,
                SIDE_PRIORITY.get(item.side, 0),
                item.score,
                item.confidence,
            ),
            reverse=True,
        )

    @property
    def elite_items(self) -> List[PortfolioItem]:
        return [item for item in self.ranked_items if item.recommendation == "ELITE"]

    @property
    def actionable_items(self) -> List[PortfolioItem]:
        return [
            item for item in self.ranked_items
            if item.recommendation in {"ELITE", "ACTIONABLE"}
        ]

    @property
    def watchlist_items(self) -> List[PortfolioItem]:
        return [
            item for item in self.ranked_items
            if item.recommendation == "WATCHLIST"
        ]

    @property
    def closest_items(self) -> List[PortfolioItem]:
        return [
            item for item in self.ranked_items
            if item.recommendation in {"MONITOR", "IGNORE"}
        ]

    @property
    def has_real_opportunity(self) -> bool:
        return bool(self.elite_items or self.actionable_items or self.watchlist_items)


def _component_points(opportunity, name: str) -> int:
    if hasattr(opportunity, "component_points"):
        try:
            return int(opportunity.component_points(name) or 0)
        except Exception:
            return 0
    return 0


def _mtf_score(opportunity, consensus_result=None) -> float:
    if consensus_result is None:
        return 0.0

    consensus = float(getattr(consensus_result, "consensus", 0) or 0)
    direction = getattr(consensus_result, "direction", "")
    primary_side = getattr(opportunity, "side", "")
    quality = getattr(consensus_result, "alignment_quality", "")

    if primary_side in {"LONG", "SHORT"} and direction == primary_side:
        bonus = min(100.0, consensus)
        if quality in {"STRONG_ALIGNMENT", "DIRECTIONAL_ALIGNMENT"}:
            bonus += 8
        return min(100.0, bonus)

    if direction == "NEUTRAL":
        # اجماع خنثی برای فرصت جهت‌دار امتیاز پایینی دارد، اما برای Monitor-only صفر مطلق نیست.
        if primary_side in {"LONG", "SHORT"}:
            return max(0.0, 35.0 - consensus * 0.25)
        return 25.0

    if primary_side in {"LONG", "SHORT"} and direction != primary_side:
        return 0.0

    return 20.0


def _historical_edge_score(opportunity) -> float:
    points = _component_points(opportunity, "Historical Edge")
    # Historical Edge در بازه تقریبی -12 تا +12 است؛ آن را به بازه 0 تا 100 تبدیل می‌کنیم.
    return max(0.0, min(100.0, ((points + 12) / 24) * 100))


def _risk_score(opportunity) -> float:
    risk_penalty = _component_points(opportunity, "Risk Penalty")
    risk_label = getattr(opportunity, "risk_label", "Unknown")

    base = 80.0 + RISK_ADJUSTMENT.get(risk_label, -4)

    if risk_penalty <= -12:
        base -= 35
    elif risk_penalty <= -8:
        base -= 22
    elif risk_penalty <= -5:
        base -= 12
    elif risk_penalty < 0:
        base -= 5

    return max(0.0, min(100.0, base))


def calculate_opportunity_score(opportunity, consensus_result=None) -> float:
    """
    Opportunity Score v2

    این امتیاز مخصوص رتبه‌بندی پورتفو است و با score اصلی فرق دارد.
    ترکیب پیشنهادی:
    - 35% Decision Score
    - 25% Confidence
    - 15% Historical Edge
    - 15% Multi-Timeframe
    - 10% Risk Quality

    سپس با Actionability و Side تعدیل می‌شود.
    """

    decision_score = float(getattr(opportunity, "score", 0) or 0)
    confidence = float(getattr(getattr(opportunity, "confidence", None), "value", 0) or 0)
    historical = _historical_edge_score(opportunity)
    mtf = _mtf_score(opportunity, consensus_result)
    risk = _risk_score(opportunity)

    score = (
        decision_score * 0.35
        + confidence * 0.25
        + historical * 0.15
        + mtf * 0.15
        + risk * 0.10
    )

    actionability = getattr(opportunity, "actionability_label", "MONITOR_ONLY")
    score += ACTIONABILITY_BONUS.get(actionability, 0)

    if getattr(opportunity, "side", "NEUTRAL") == "NEUTRAL":
        score -= 18

    if consensus_result is not None:
        direction = getattr(consensus_result, "direction", "")
        consensus = float(getattr(consensus_result, "consensus", 0) or 0)
        primary_side = getattr(opportunity, "side", "")

        if primary_side in {"LONG", "SHORT"} and direction == primary_side:
            score += min(10, consensus * 0.10)
        elif primary_side in {"LONG", "SHORT"} and direction == "NEUTRAL":
            score -= min(12, consensus * 0.10)
        elif primary_side in {"LONG", "SHORT"} and direction != primary_side:
            score -= min(20, consensus * 0.18)

    return round(max(0.0, min(100.0, score)), 2)


def quality_from_opportunity_score(value: float) -> tuple[str, str]:
    if value >= 85:
        return "Elite", "⭐⭐⭐⭐⭐"
    if value >= 72:
        return "Strong", "⭐⭐⭐⭐"
    if value >= 60:
        return "Good", "⭐⭐⭐"
    if value >= 45:
        return "Weak", "⭐⭐"
    return "Ignore", "⭐"


def recommendation_from_item_fields(
    side: str,
    actionability: str,
    opportunity_score: float,
    confidence: int,
    mtf_direction: str,
    mtf_consensus: int,
) -> str:
    """
    Preliminary opportunity recommendation based on score, confidence and MTF.

    v4.0.1 note: this is intentionally only a first pass. Final public
    recommendation must pass through `_apply_trade_consistency_guard`, because
    an item is not truly actionable if its trade card says Avoid or R:R is weak.
    """
    if side not in {"LONG", "SHORT"}:
        if opportunity_score >= 45:
            return "MONITOR"
        return "IGNORE"

    mtf_aligned = mtf_direction == side and mtf_consensus >= 70

    if (
        opportunity_score >= 85
        and confidence >= 70
        and actionability in {"HIGH_ACTIONABILITY", "ACTIONABLE"}
        and mtf_aligned
    ):
        return "ELITE"

    if (
        opportunity_score >= 72
        and confidence >= 60
        and actionability in {"HIGH_ACTIONABILITY", "ACTIONABLE", "WATCHLIST"}
        and mtf_direction in {side, "NEUTRAL"}
    ):
        return "ACTIONABLE"

    if (
        opportunity_score >= 55
        and confidence >= 40
        and actionability in {"WATCHLIST", "ACTIONABLE", "HIGH_ACTIONABILITY"}
    ):
        return "WATCHLIST"

    if opportunity_score >= 45:
        return "MONITOR"

    return "IGNORE"


def _apply_trade_consistency_guard(recommendation: str, trade_card, notes: List[str]) -> str:
    """Prevent contradictory public recommendations.

    The Portfolio layer can see attractive raw opportunity scores while the
    Trade Intelligence card still says Avoid because the setup has weak R:R,
    missing entry/stop data, weak quality, or poor risk confirmation. In v4.0
    this could show `ACTIONABLE` while `Trade=Avoid`. v4.0.1 fixes that by
    making the final recommendation pass a trade-quality gate.
    """
    if recommendation not in {"ELITE", "ACTIONABLE", "WATCHLIST"}:
        return recommendation

    rr = getattr(trade_card, "rr", None)
    quality = getattr(trade_card, "quality", None)
    rr_valid = bool(getattr(rr, "is_valid", False))
    first_rr = float(getattr(rr, "first_rr", 0.0) or 0.0) if rr_valid else 0.0
    quality_score = int(getattr(quality, "score", 0) or 0) if quality else 0
    quality_grade = str(getattr(quality, "grade", "Avoid") or "Avoid") if quality else "Avoid"

    downgrade_reasons = []

    if not rr_valid:
        downgrade_reasons.append("R:R نامعتبر است")
    elif recommendation in {"ELITE", "ACTIONABLE"} and first_rr < 1.20:
        downgrade_reasons.append(f"R:R برای Actionable کافی نیست: {first_rr:.2f}")
    elif recommendation == "WATCHLIST" and first_rr < 1.00:
        downgrade_reasons.append(f"R:R برای Watchlist کافی نیست: {first_rr:.2f}")

    if quality_grade == "Avoid":
        downgrade_reasons.append("Trade Quality برابر Avoid است")
    elif recommendation in {"ELITE", "ACTIONABLE"} and quality_score < 55:
        downgrade_reasons.append(f"Trade Quality برای Actionable کافی نیست: {quality_score}/100")
    elif recommendation == "WATCHLIST" and quality_score < 45:
        downgrade_reasons.append(f"Trade Quality برای Watchlist کافی نیست: {quality_score}/100")

    if recommendation == "ELITE":
        if first_rr < 1.80:
            downgrade_reasons.append(f"R:R برای Elite کافی نیست: {first_rr:.2f}")
        if quality_score < 74:
            downgrade_reasons.append(f"Trade Quality برای Elite کافی نیست: {quality_score}/100")

    if not downgrade_reasons:
        return recommendation

    final = "MONITOR"
    notes.append(f"Trade Guard: {recommendation} -> {final}")
    for reason in downgrade_reasons[:3]:
        notes.append(f"Trade Guard reason: {reason}")
    return final


def calculate_rank_score(opportunity, consensus_result=None) -> float:
    """
    Rank Score برای مرتب‌سازی داخلی.
    از v2.6 به بعد rank_score نزدیک به opportunity_score است اما کمی side و score خام را هم لحاظ می‌کند.
    """

    opportunity_score = calculate_opportunity_score(opportunity, consensus_result)
    raw_score = float(getattr(opportunity, "score", 0) or 0)
    confidence = float(getattr(getattr(opportunity, "confidence", None), "value", 0) or 0)

    rank = opportunity_score + raw_score * 0.05 + confidence * 0.03

    if getattr(opportunity, "side", "NEUTRAL") in {"LONG", "SHORT"}:
        rank += 2

    return round(max(0.0, rank), 2)


def build_portfolio_item(symbol: str, opportunity, consensus_result=None, provider: str = "", price: float = 0.0) -> PortfolioItem:
    notes = []

    regime = opportunity.raw.get("regime_label", "") if hasattr(opportunity, "raw") else ""
    mtf_direction = getattr(consensus_result, "direction", "") if consensus_result else ""
    mtf_consensus = int(getattr(consensus_result, "consensus", 0) or 0) if consensus_result else 0
    mtf_quality = getattr(consensus_result, "alignment_quality", "") if consensus_result else ""

    opportunity_score = calculate_opportunity_score(opportunity, consensus_result)
    quality_label, quality_stars = quality_from_opportunity_score(opportunity_score)

    trade_card = build_trade_intelligence_card(opportunity)
    first_rr = round(trade_card.rr.first_rr, 2) if trade_card.rr.is_valid else 0.0
    best_rr = round(trade_card.rr.best_rr, 2) if trade_card.rr.is_valid else 0.0
    position_notional = float(trade_card.position.position_notional or 0.0) if trade_card.position.is_valid else 0.0
    expected_drawdown = float(trade_card.drawdown.expected_drawdown_pct or 0.0) if trade_card.drawdown.is_valid else 0.0

    preliminary_recommendation = recommendation_from_item_fields(
        side=opportunity.side,
        actionability=opportunity.actionability_label,
        opportunity_score=opportunity_score,
        confidence=int(opportunity.confidence.value),
        mtf_direction=mtf_direction,
        mtf_consensus=mtf_consensus,
    )
    recommendation = _apply_trade_consistency_guard(preliminary_recommendation, trade_card, notes)

    if opportunity.side == "NEUTRAL":
        notes.append("فعلاً فقط مانیتور شود")

    if opportunity.actionability_label == "WATCHLIST":
        notes.append("ارزش زیرنظر گرفتن دارد")

    if recommendation == "ELITE":
        notes.append("فرصت قوی با هم‌راستایی بالا")
    elif recommendation == "ACTIONABLE":
        notes.append("قابل بررسی با مدیریت ریسک")
    elif recommendation == "WATCHLIST":
        notes.append("کاندید زیرنظر گرفتن")

    if consensus_result is not None:
        if mtf_direction == "NEUTRAL":
            notes.append("MTF هنوز جهت‌دار نیست")
        elif mtf_direction == opportunity.side:
            notes.append("MTF هم‌راستا است")
        elif opportunity.side in {"LONG", "SHORT"}:
            notes.append("MTF با Bias اصلی تضاد دارد")

    if _component_points(opportunity, "Volume") <= 0:
        notes.append("Volume تأیید نداده")

    intelligence = build_intelligence_report(opportunity)
    if intelligence.thesis_title:
        notes.append(f"Thesis: {intelligence.thesis_title}")
    if intelligence.conflicts:
        notes.append(f"Conflicts: {len(intelligence.conflicts)}")

    return PortfolioItem(
        symbol=symbol,
        timeframe=opportunity.timeframe,
        side=opportunity.side,
        score=int(opportunity.score),
        confidence=int(opportunity.confidence.value),
        confidence_label=opportunity.confidence.label,
        risk_label=opportunity.risk_label,
        actionability=opportunity.actionability_label,
        regime=regime,
        mtf_direction=mtf_direction,
        mtf_consensus=mtf_consensus,
        mtf_quality=mtf_quality,
        rank_score=calculate_rank_score(opportunity, consensus_result),
        opportunity_score=opportunity_score,
        quality_label=quality_label,
        quality_stars=quality_stars,
        recommendation=recommendation,
        provider=provider or "",
        price=float(price or 0),
        decision_timestamp=str(getattr(opportunity, "raw", {}).get("timestamp", "")),
        entry_zone=str(getattr(opportunity, "entry_zone", "") or ""),
        stop_zone=str(getattr(opportunity, "stop_zone", "") or ""),
        targets=list(getattr(opportunity, "targets", []) or []),
        trade_quality_grade=trade_card.quality.grade,
        trade_quality_score=trade_card.quality.score,
        first_rr=first_rr,
        best_rr=best_rr,
        recommended_risk_pct=float(trade_card.kelly.recommended_risk_pct or 0.0),
        position_notional=position_notional,
        expected_drawdown_pct=expected_drawdown,
        notes=notes,
    )


def _print_item_table(title: str, items: List[PortfolioItem], limit: int = 10) -> None:
    print("\n" + title)
    print("-" * 110)
    print(
        f"{'#':<3} {'Symbol':<12} {'Side':<8} {'Opp':<7} {'Score':<7} {'Conf':<7} "
        f"{'Quality':<12} {'Trade':<9} {'RR':<6} {'Rec':<11} {'MTF':<15} {'Provider':<8}"
    )
    print("-" * 110)

    for index, item in enumerate(items[:limit], start=1):
        mtf = f"{item.mtf_direction}/{item.mtf_consensus}%" if item.mtf_direction else "-"
        quality = f"{item.quality_stars} {item.quality_label}"
        print(
            f"{index:<3} {item.symbol:<12} {item.side:<8} {item.opportunity_score:<7} "
            f"{item.score:<7} {item.confidence:<7} {quality:<12} "
            f"{item.trade_quality_grade:<9} {item.first_rr:<6} {item.recommendation:<11} {mtf:<15} {item.provider:<8}"
        )


def format_portfolio_console(result: PortfolioScanResult, top_n: int = 10) -> None:
    print("\n" + "=" * 110)
    print("🏆 Freakto Portfolio Scanner v4.6.1")
    print("=" * 110)

    if not result.items:
        print("هیچ نتیجه‌ای برای نمایش وجود ندارد.")
        if result.failed_symbols:
            print(f"Failed: {', '.join(result.failed_symbols)}")
        print("=" * 110)
        return

    if result.market_breadth is not None:
        format_breadth_console(result.market_breadth)

    if result.elite_items:
        _print_item_table("🚀 Elite Opportunities", result.elite_items, limit=top_n)

    if result.actionable_items:
        _print_item_table("✅ Actionable Candidates", result.actionable_items, limit=top_n)

    if result.watchlist_items:
        _print_item_table("👀 Smart Watchlist", result.watchlist_items, limit=top_n)

    closest = result.closest_items[:top_n]
    if closest:
        _print_item_table("📌 Closest / Monitor Candidates", closest, limit=top_n)

    if not result.has_real_opportunity:
        print("\nℹ️ No actionable opportunity right now. Market is mostly monitor-only.")

    if result.failed_symbols:
        print("\nFailed symbols:")
        for symbol in result.failed_symbols:
            print(f"  - {symbol}")

    print("=" * 110)


def format_portfolio_telegram(result: PortfolioScanResult, top_n: int = 8) -> str:
    lines = [
        "🏆 *Freakto Portfolio Scanner v4.6.1*",
        "",
    ]

    if not result.items:
        lines.append("هیچ نتیجه‌ای برای نمایش وجود ندارد.")
        return "\n".join(lines)

    if result.market_breadth is not None:
        lines.extend(format_breadth_telegram(result.market_breadth))
        lines.append("")

    if result.elite_items:
        lines.append("🚀 *Elite Opportunities*")
        for index, item in enumerate(result.elite_items[:top_n], start=1):
            lines.extend(_telegram_item_lines(index, item))
        lines.append("")

    if result.actionable_items:
        lines.append("✅ *Actionable Candidates*")
        for index, item in enumerate(result.actionable_items[:top_n], start=1):
            lines.extend(_telegram_item_lines(index, item))
        lines.append("")

    if result.watchlist_items:
        lines.append("👀 *Smart Watchlist*")
        for index, item in enumerate(result.watchlist_items[:top_n], start=1):
            lines.extend(_telegram_item_lines(index, item))
        lines.append("")

    if not result.has_real_opportunity:
        lines.append("ℹ️ *No actionable opportunity right now.*")
        lines.append("بازار فعلاً بیشتر حالت مانیتور دارد.")
        lines.append("")

    closest = result.closest_items[:min(5, top_n)]
    if closest:
        lines.append("📌 *Closest Candidates*")
        for index, item in enumerate(closest, start=1):
            lines.append(
                f"{index}. {item.quality_stars} *{item.symbol}* | {item.side} | "
                f"Opp `{item.opportunity_score}` | {item.recommendation}"
            )
        lines.append("")

    if result.failed_symbols:
        lines.append("Failed:")
        for symbol in result.failed_symbols[:6]:
            lines.append(f"- {symbol}")
        lines.append("")

    lines.append("این رتبه‌بندی توصیه مالی نیست؛ فقط مقایسهٔ وضعیت نمادها بر اساس موتور Freakto است.")

    return "\n".join(lines)


def _telegram_item_lines(index: int, item: PortfolioItem) -> List[str]:
    icon = "🟢" if item.side == "LONG" else "🔴" if item.side == "SHORT" else "⚪"
    mtf = f"{item.mtf_direction} {item.mtf_consensus}%" if item.mtf_direction else "-"
    notes = f" | {', '.join(item.notes[:2])}" if item.notes else ""

    return [
        (
            f"{index}. {icon} {item.quality_stars} *{item.symbol}* | {item.side} | "
            f"Opp `{item.opportunity_score}` | Score `{item.score}` | Conf `{item.confidence}%`"
        ),
        f"   Trade: *{item.trade_quality_grade}* `{item.trade_quality_score}/100` | RR `{item.first_rr}` | Risk `{item.recommended_risk_pct:.2f}%`",
        f"   Rec: *{item.recommendation}* | MTF: `{mtf}` | Regime: {item.regime or '-'}{notes}",
    ]
