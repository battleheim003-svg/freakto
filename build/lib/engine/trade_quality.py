"""
engine.trade_quality

Trade Intelligence Card for Freakto v2.7.0.

Combines R:R, position sizing, Kelly risk, historical outcomes and MTF state
into a compact trade-management view.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .risk_reward import calculate_risk_reward, format_risk_reward_lines, RiskRewardResult
from .position_size import calculate_position_size, format_position_size_lines, PositionSizeResult
from .kelly import calculate_kelly, format_kelly_lines, KellyResult
from .drawdown import calculate_drawdown_from_similarity, format_drawdown_lines, DrawdownResult
from .similarity import find_similar_snapshots


@dataclass
class HistoricalStats:
    sample_size: int = 0
    win_rate: Optional[float] = None
    loss_rate: Optional[float] = None
    stop_rate: Optional[float] = None
    avg_24h_return: Optional[float] = None


@dataclass
class TradeQualityResult:
    grade: str
    score: int
    label: str
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class TradeIntelligenceCard:
    is_directional: bool
    rr: RiskRewardResult
    position: PositionSizeResult
    kelly: KellyResult
    drawdown: DrawdownResult
    quality: TradeQualityResult
    historical: HistoricalStats


def _component_points(opportunity, name: str) -> int:
    try:
        return int(opportunity.component_points(name) or 0)
    except Exception:
        return 0


def _historical_stats(similarity_result) -> HistoricalStats:
    matches = getattr(similarity_result, "matches", []) or []
    evaluated = [item for item in matches if getattr(item, "outcome_label", "") in {"WIN", "LOSS", "FLAT"}]

    if not evaluated:
        return HistoricalStats()

    total = len(evaluated)
    wins = sum(1 for item in evaluated if item.outcome_label == "WIN")
    losses = sum(1 for item in evaluated if item.outcome_label == "LOSS")
    stops = sum(1 for item in evaluated if getattr(item, "stop_hit", 0))
    returns = [item.return_after_24h_pct for item in evaluated if item.return_after_24h_pct is not None]

    return HistoricalStats(
        sample_size=total,
        win_rate=round(wins / total * 100, 1),
        loss_rate=round(losses / total * 100, 1),
        stop_rate=round(stops / total * 100, 1),
        avg_24h_return=round(sum(returns) / len(returns), 2) if returns else None,
    )


def _grade_from_score(score: int) -> tuple[str, str]:
    if score >= 90:
        return "AAA+", "Elite trade quality"
    if score >= 82:
        return "AAA", "Very strong trade quality"
    if score >= 74:
        return "AA", "Strong trade quality"
    if score >= 65:
        return "A", "Good but selective"
    if score >= 55:
        return "B", "Watchlist quality"
    if score >= 45:
        return "C", "Weak / monitor only"
    return "Avoid", "Avoid or monitor only"


def calculate_trade_quality(opportunity, rr: RiskRewardResult, historical: HistoricalStats) -> TradeQualityResult:
    if getattr(opportunity, "side", "NEUTRAL") not in {"LONG", "SHORT"}:
        return TradeQualityResult(
            grade="Avoid",
            score=0,
            label="No directional setup",
            warnings=["Bias خنثی است؛ کیفیت معامله محاسبه نمی‌شود."],
        )

    score = 0
    reasons = []
    warnings = []

    decision_score = int(getattr(opportunity, "score", 0) or 0)
    confidence = int(getattr(getattr(opportunity, "confidence", None), "value", 0) or 0)
    historical_edge = _component_points(opportunity, "Historical Edge")
    mtf = _component_points(opportunity, "MTF Consensus")
    volume = _component_points(opportunity, "Volume")
    risk_penalty = _component_points(opportunity, "Risk Penalty")

    score += min(25, decision_score * 0.25)
    score += min(20, confidence * 0.20)

    if rr.is_valid:
        if rr.first_rr >= 2.0:
            score += 18
            reasons.append(f"R:R اولیه خوب است: {rr.first_rr:.2f}")
        elif rr.first_rr >= 1.2:
            score += 10
            reasons.append(f"R:R قابل قبول است: {rr.first_rr:.2f}")
        else:
            score += 3
            warnings.append(f"R:R اولیه ضعیف است: {rr.first_rr:.2f}")
    else:
        warnings.append(rr.reason)

    if historical.sample_size >= 5 and historical.win_rate is not None:
        if historical.win_rate >= 65:
            score += 16
            reasons.append(f"Win Rate تاریخی مناسب است: {historical.win_rate:.1f}%")
        elif historical.win_rate >= 52:
            score += 8
            reasons.append(f"Win Rate تاریخی متوسط است: {historical.win_rate:.1f}%")
        else:
            warnings.append(f"Win Rate تاریخی ضعیف است: {historical.win_rate:.1f}%")

        if historical.stop_rate is not None and historical.stop_rate >= 55:
            score -= 10
            warnings.append(f"Stop Rate تاریخی بالاست: {historical.stop_rate:.1f}%")
    else:
        warnings.append("نمونه تاریخی کافی برای کیفیت معامله وجود ندارد.")

    if historical_edge > 0:
        score += min(8, historical_edge)
        reasons.append(f"Historical Edge مثبت است: +{historical_edge}")
    elif historical_edge < 0:
        score += max(-8, historical_edge)
        warnings.append(f"Historical Edge منفی است: {historical_edge}")

    if mtf > 0:
        score += min(8, mtf)
        reasons.append(f"MTF هم‌راستا است: +{mtf}")
    elif mtf < 0:
        score += max(-10, mtf)
        warnings.append(f"MTF تأیید کافی نمی‌دهد: {mtf}")

    if volume >= 8:
        score += 5
        reasons.append("Volume تأیید مناسبی دارد.")
    elif volume <= 0:
        score -= 6
        warnings.append("Volume هنوز تأیید نداده است.")

    if risk_penalty <= -8:
        score -= 10
        warnings.append("Risk Penalty بالا است.")
    elif risk_penalty < 0:
        score -= 4

    if getattr(opportunity, "actionability_label", "") in {"ACTIONABLE", "HIGH_ACTIONABILITY"}:
        score += 8
    elif getattr(opportunity, "actionability_label", "") == "WATCHLIST":
        score += 2

    score = int(max(0, min(100, round(score))))
    grade, label = _grade_from_score(score)

    return TradeQualityResult(
        grade=grade,
        score=score,
        label=label,
        reasons=reasons[:5],
        warnings=warnings[:5],
    )


def build_trade_intelligence_card(
    opportunity,
    account_size: float = 10_000.0,
    risk_pct: float = 1.0,
):
    rr = calculate_risk_reward(opportunity)
    similarity = find_similar_snapshots(opportunity)
    historical = _historical_stats(similarity)
    kelly = calculate_kelly(historical.win_rate, rr.first_rr if rr.is_valid else None)

    effective_risk_pct = min(float(risk_pct or 1.0), kelly.recommended_risk_pct or risk_pct)
    position = calculate_position_size(rr, account_size=account_size, risk_pct=effective_risk_pct)
    drawdown = calculate_drawdown_from_similarity(similarity)
    quality = calculate_trade_quality(opportunity, rr, historical)

    return TradeIntelligenceCard(
        is_directional=getattr(opportunity, "side", "NEUTRAL") in {"LONG", "SHORT"},
        rr=rr,
        position=position,
        kelly=kelly,
        drawdown=drawdown,
        quality=quality,
        historical=historical,
    )


def format_trade_card_lines(card: TradeIntelligenceCard) -> List[str]:
    lines = ["*Trade Intelligence:*"]

    if not card.is_directional:
        lines.append("- Bias خنثی است؛ کارت مدیریت معامله فقط برای LONG/SHORT فعال می‌شود.")
        return lines

    lines.append(f"- Quality: *{card.quality.grade}* ({card.quality.score}/100) — {card.quality.label}")

    if card.historical.sample_size > 0:
        win = f"{card.historical.win_rate:.1f}%" if card.historical.win_rate is not None else "نامشخص"
        stop = f"{card.historical.stop_rate:.1f}%" if card.historical.stop_rate is not None else "نامشخص"
        avg = f"{card.historical.avg_24h_return:.2f}%" if card.historical.avg_24h_return is not None else "نامشخص"
        lines.append(f"- Historical: Win `{win}` | Stop `{stop}` | Avg 24h `{avg}`")
    else:
        lines.append("- Historical: نمونه کافی موجود نیست.")

    lines.append("")
    lines.extend(format_risk_reward_lines(card.rr))
    lines.append("")
    lines.extend(format_position_size_lines(card.position))
    lines.append("")
    lines.extend(format_kelly_lines(card.kelly))
    lines.append("")
    lines.extend(format_drawdown_lines(card.drawdown))

    if card.quality.reasons:
        lines.append("")
        lines.append("*Trade Quality Strengths:*")
        for item in card.quality.reasons[:4]:
            lines.append(f"✓ {item}")

    if card.quality.warnings:
        lines.append("")
        lines.append("*Trade Quality Warnings:*")
        for item in card.quality.warnings[:4]:
            lines.append(f"⚠️ {item}")

    return lines
