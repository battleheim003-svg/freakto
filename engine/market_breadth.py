"""
engine.market_breadth

Market Breadth Engine - v4.6.1

این ماژول نتیجه اسکن پورتفو را به یک نمای کلی از وضعیت بازار تبدیل می‌کند.
به جای اینکه فقط بگوییم هر نماد چه وضعیتی دارد، می‌گوییم کل بازار بیشتر در
حالت Risk-On، Risk-Off، Neutral یا Mixed قرار دارد.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class MarketBreadthResult:
    total_symbols: int = 0
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0

    actionable_count: int = 0
    watchlist_count: int = 0
    monitor_count: int = 0
    ignore_count: int = 0

    average_score: float = 0.0
    average_confidence: float = 0.0
    average_opportunity_score: float = 0.0

    bullish_pct: float = 0.0
    bearish_pct: float = 0.0
    neutral_pct: float = 0.0

    market_mode: str = "UNKNOWN"
    # market_agreement یعنی بازار چقدر روی یک حالت جمعی توافق دارد؛
    # مثلاً Neutral 100% یعنی همه نمادها خنثی‌اند، نه اینکه فرصت معاملاتی قوی است.
    market_agreement: int = 0
    # opportunity_strength قدرت واقعی فرصت‌های معاملاتی پورتفو را نشان می‌دهد.
    opportunity_strength: int = 0
    # برای سازگاری با نسخه‌های قبلی نگه داشته شده؛ از v4.6.1 بهتر است market_agreement خوانده شود.
    market_strength: int = 0
    risk_tone: str = "UNKNOWN"
    summary: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_risk_on(self) -> bool:
        return self.market_mode == "RISK_ON"

    @property
    def is_risk_off(self) -> bool:
        return self.market_mode == "RISK_OFF"

    @property
    def is_neutral(self) -> bool:
        return self.market_mode == "NEUTRAL"


def _safe_pct(part: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((part / total) * 100, 1)


def _avg(values) -> float:
    values = [float(v) for v in values if v is not None]
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


def calculate_market_breadth(items) -> MarketBreadthResult:
    """
    items: لیستی از PortfolioItem
    """

    total = len(items)
    if total == 0:
        return MarketBreadthResult(
            total_symbols=0,
            market_mode="NO_DATA",
            risk_tone="UNKNOWN",
            summary=["هیچ نمادی برای محاسبه Market Breadth وجود ندارد."],
        )

    bullish = sum(1 for item in items if item.side == "LONG")
    bearish = sum(1 for item in items if item.side == "SHORT")
    neutral = sum(1 for item in items if item.side == "NEUTRAL")

    actionable = sum(1 for item in items if item.recommendation in {"ELITE", "ACTIONABLE"})
    watchlist = sum(1 for item in items if item.recommendation == "WATCHLIST")
    monitor = sum(1 for item in items if item.recommendation == "MONITOR")
    ignore = sum(1 for item in items if item.recommendation == "IGNORE")

    avg_score = _avg(item.score for item in items)
    avg_conf = _avg(item.confidence for item in items)
    avg_opp = _avg(item.opportunity_score for item in items)

    bull_pct = _safe_pct(bullish, total)
    bear_pct = _safe_pct(bearish, total)
    neutral_pct = _safe_pct(neutral, total)

    mode = "MIXED"
    risk_tone = "MIXED"
    agreement = 0
    opportunity_strength = 0
    summary = []
    warnings = []

    # تصمیم کلی بازار: عمداً محافظه‌کارانه است.
    if neutral_pct >= 65:
        mode = "NEUTRAL"
        risk_tone = "MONITOR"
        agreement = int(round(neutral_pct))
        opportunity_strength = int(round(avg_opp))
        summary.append("بیشتر نمادها خنثی هستند؛ بازار فعلاً جهت جمعی قوی ندارد.")
        summary.append(
            f"Market Agreement بالا روی خنثی بودن است ({agreement}/100)، "
            f"اما Opportunity Strength فقط {opportunity_strength}/100 است."
        )
    elif bull_pct >= 55 and avg_opp >= 45:
        mode = "RISK_ON"
        risk_tone = "BULLISH"
        agreement = int(round(bull_pct))
        opportunity_strength = int(round((avg_opp * 0.60) + (avg_conf * 0.25) + (bull_pct * 0.15)))
        summary.append("پهنای بازار بیشتر به سمت خرید/ریسک‌پذیری متمایل است.")
    elif bear_pct >= 55 and avg_opp >= 45:
        mode = "RISK_OFF"
        risk_tone = "BEARISH"
        agreement = int(round(bear_pct))
        opportunity_strength = int(round((avg_opp * 0.60) + (avg_conf * 0.25) + (bear_pct * 0.15)))
        summary.append("پهنای بازار بیشتر به سمت فروش/ریسک‌گریزی متمایل است.")
    else:
        mode = "MIXED"
        risk_tone = "CAUTION"
        strongest_direction = max(bull_pct, bear_pct, neutral_pct)
        agreement = int(round(strongest_direction))
        opportunity_strength = int(round((avg_opp * 0.70) + (avg_conf * 0.20) + (max(bull_pct, bear_pct) * 0.10)))
        summary.append("بازار ترکیبی است؛ هم‌راستایی کافی بین نمادها دیده نمی‌شود.")

    if actionable == 0 and watchlist == 0:
        warnings.append("هیچ فرصت actionable یا watchlist جدی در پورتفو دیده نشد.")

    if avg_conf < 35:
        warnings.append(f"میانگین Confidence پایین است: {avg_conf:.1f}%")

    if avg_opp < 35:
        warnings.append(f"میانگین Opportunity Score پایین است: {avg_opp:.1f}")

    summary.append(
        f"Bullish: {bullish}/{total} ({bull_pct:.1f}%) | "
        f"Bearish: {bearish}/{total} ({bear_pct:.1f}%) | "
        f"Neutral: {neutral}/{total} ({neutral_pct:.1f}%)"
    )

    summary.append(
        f"Actionable: {actionable} | Watchlist: {watchlist} | Monitor: {monitor} | Ignore: {ignore}"
    )

    return MarketBreadthResult(
        total_symbols=total,
        bullish_count=bullish,
        bearish_count=bearish,
        neutral_count=neutral,
        actionable_count=actionable,
        watchlist_count=watchlist,
        monitor_count=monitor,
        ignore_count=ignore,
        average_score=avg_score,
        average_confidence=avg_conf,
        average_opportunity_score=avg_opp,
        bullish_pct=bull_pct,
        bearish_pct=bear_pct,
        neutral_pct=neutral_pct,
        market_mode=mode,
        market_agreement=max(0, min(100, agreement)),
        opportunity_strength=max(0, min(100, opportunity_strength)),
        market_strength=max(0, min(100, agreement)),
        risk_tone=risk_tone,
        summary=summary,
        warnings=warnings,
    )


def format_breadth_console(breadth: MarketBreadthResult) -> None:
    print("\n" + "=" * 110)
    print("🌐 Market Breadth Engine v4.6.1")
    print("=" * 110)
    print(f"Market Mode : {breadth.market_mode}")
    print(f"Risk Tone   : {breadth.risk_tone}")
    print(f"Agreement   : {breadth.market_agreement}/100")
    print(f"Opp Strength: {breadth.opportunity_strength}/100")
    print(f"Avg Score   : {breadth.average_score:.1f}")
    print(f"Avg Conf    : {breadth.average_confidence:.1f}%")
    print(f"Avg Opp     : {breadth.average_opportunity_score:.1f}")
    print()

    for line in breadth.summary:
        print(f"- {line}")

    if breadth.warnings:
        print("\nWarnings:")
        for warning in breadth.warnings:
            print(f"⚠️ {warning}")

    print("=" * 110)


def format_breadth_telegram(breadth: MarketBreadthResult) -> List[str]:
    lines = [
        "🌐 *Market Breadth v4.6.1*",
        f"- Mode: *{breadth.market_mode}*",
        f"- Risk Tone: *{breadth.risk_tone}*",
        f"- Market Agreement: `{breadth.market_agreement}/100`",
        f"- Opportunity Strength: `{breadth.opportunity_strength}/100`",
        f"- Avg Opportunity: `{breadth.average_opportunity_score:.1f}`",
        f"- Avg Confidence: `{breadth.average_confidence:.1f}%`",
        "",
    ]

    lines.append(
        f"Bull `{breadth.bullish_pct:.1f}%` | "
        f"Bear `{breadth.bearish_pct:.1f}%` | "
        f"Neutral `{breadth.neutral_pct:.1f}%`"
    )

    lines.append(
        f"Actionable `{breadth.actionable_count}` | "
        f"Watchlist `{breadth.watchlist_count}` | "
        f"Monitor `{breadth.monitor_count}` | Ignore `{breadth.ignore_count}`"
    )

    if breadth.warnings:
        lines.append("")
        for warning in breadth.warnings[:3]:
            lines.append(f"⚠️ {warning}")

    return lines
