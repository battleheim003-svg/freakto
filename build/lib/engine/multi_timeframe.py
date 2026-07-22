"""
engine.multi_timeframe

Weighted Multi-Timeframe Consensus Engine

این ماژول خروجی Decision Engine در تایم‌فریم‌های مختلف را تجمیع می‌کند.
نسخه جدید وزن تایم‌فریم‌ها را در نظر می‌گیرد:
- 1d وزن بیشتر دارد چون ساختار کلان‌تر را نشان می‌دهد.
- 4h تایم‌فریم اصلی تصمیم است.
- 1h بیشتر برای نویز/تأیید کوتاه‌مدت استفاده می‌شود.
"""

from dataclasses import dataclass, field
from typing import Dict, List


DEFAULT_TIMEFRAME_WEIGHTS: Dict[str, float] = {
    "15m": 0.05,
    "30m": 0.08,
    "1h": 0.15,
    "2h": 0.20,
    "4h": 0.35,
    "6h": 0.40,
    "8h": 0.42,
    "12h": 0.45,
    "1d": 0.50,
    "1w": 0.70,
}


@dataclass
class TimeframeSignal:
    timeframe: str
    side: str
    score: int
    confidence: int
    weight: float = 0.0


@dataclass
class ConsensusResult:
    direction: str
    consensus: int
    bull_count: int
    bear_count: int
    neutral_count: int
    signals: List[TimeframeSignal] = field(default_factory=list)

    bull_weight: float = 0.0
    bear_weight: float = 0.0
    neutral_weight: float = 0.0
    total_weight: float = 0.0
    alignment_quality: str = "UNKNOWN"



def _normalize_timeframe(timeframe: str) -> str:
    return str(timeframe or "").strip().lower()



def timeframe_weight(timeframe: str) -> float:
    tf = _normalize_timeframe(timeframe)
    return DEFAULT_TIMEFRAME_WEIGHTS.get(tf, 0.20)



def _weighted_bucket(signals: List[TimeframeSignal]):
    bull_weight = 0.0
    bear_weight = 0.0
    neutral_weight = 0.0

    for signal in signals:
        signal.weight = signal.weight or timeframe_weight(signal.timeframe)

        if signal.side == "LONG":
            bull_weight += signal.weight
        elif signal.side == "SHORT":
            bear_weight += signal.weight
        else:
            neutral_weight += signal.weight

    total_weight = bull_weight + bear_weight + neutral_weight

    return bull_weight, bear_weight, neutral_weight, total_weight



def _alignment_quality(consensus: int, direction: str) -> str:
    if direction == "NEUTRAL":
        if consensus >= 70:
            return "NEUTRAL_DOMINANT"
        return "MIXED"

    if consensus >= 85:
        return "STRONG"
    if consensus >= 70:
        return "GOOD"
    if consensus >= 55:
        return "WEAK"
    return "CONFLICTED"



def calculate_consensus(signals: List[TimeframeSignal]) -> ConsensusResult:
    if not signals:
        return ConsensusResult(
            direction="NEUTRAL",
            consensus=0,
            bull_count=0,
            bear_count=0,
            neutral_count=0,
            signals=[],
            alignment_quality="UNKNOWN",
        )

    bull_count = sum(1 for signal in signals if signal.side == "LONG")
    bear_count = sum(1 for signal in signals if signal.side == "SHORT")
    neutral_count = sum(1 for signal in signals if signal.side == "NEUTRAL")

    bull_weight, bear_weight, neutral_weight, total_weight = _weighted_bucket(signals)

    if total_weight <= 0:
        return ConsensusResult(
            direction="NEUTRAL",
            consensus=0,
            bull_count=bull_count,
            bear_count=bear_count,
            neutral_count=neutral_count,
            signals=signals,
            alignment_quality="UNKNOWN",
        )

    weighted_scores = {
        "LONG": bull_weight,
        "SHORT": bear_weight,
        "NEUTRAL": neutral_weight,
    }

    direction = max(weighted_scores, key=weighted_scores.get)
    majority_weight = weighted_scores[direction]
    consensus = round((majority_weight / total_weight) * 100)

    return ConsensusResult(
        direction=direction,
        consensus=consensus,
        bull_count=bull_count,
        bear_count=bear_count,
        neutral_count=neutral_count,
        signals=signals,
        bull_weight=round(bull_weight, 4),
        bear_weight=round(bear_weight, 4),
        neutral_weight=round(neutral_weight, 4),
        total_weight=round(total_weight, 4),
        alignment_quality=_alignment_quality(consensus, direction),
    )



def _find_signal(result: ConsensusResult, timeframe: str) -> TimeframeSignal | None:
    target = _normalize_timeframe(timeframe)

    for signal in result.signals:
        if _normalize_timeframe(signal.timeframe) == target:
            return signal

    return None


def _higher_timeframe_penalty(result: ConsensusResult, primary_side: str) -> int:
    daily = _find_signal(result, "1d")

    if primary_side not in {"LONG", "SHORT"} or daily is None:
        return 0

    if daily.side == "NEUTRAL":
        return -2

    if daily.side != primary_side:
        return -6

    return 0


def consensus_adjustment(result: ConsensusResult, primary_side: str | None = None) -> int:
    """
    امتیاز مستقل MTF.

    منطق جدید سخت‌گیرتر است:
    - وقتی اجماع وزنی NEUTRAL باشد، برای LONG/SHORT امتیاز مثبت نمی‌دهد.
    - اگر تایم‌فریم روزانه خنثی یا مخالف باشد، تصمیم اصلی جریمه می‌شود.
    - فقط وقتی جهت غالب MTF با Bias اصلی هم‌راستا باشد، امتیاز مثبت داده می‌شود.
    """

    if result is None or not result.signals:
        return 0

    primary_side = primary_side or ""
    higher_tf_penalty = _higher_timeframe_penalty(result, primary_side)

    if result.direction == "NEUTRAL":
        if result.consensus >= 75:
            base = -6
        elif result.consensus >= 60:
            base = -4
        elif result.consensus >= 50:
            base = -2
        else:
            base = 0

        return max(-8, min(0, base + higher_tf_penalty))

    if primary_side in {"LONG", "SHORT"} and result.direction != primary_side:
        if result.consensus >= 75:
            base = -8
        elif result.consensus >= 60:
            base = -6
        else:
            base = -4

        return max(-8, min(0, base + higher_tf_penalty))

    if result.direction == primary_side:
        if higher_tf_penalty < 0:
            # جهت کلی شاید هم‌راستا باشد، ولی روزانه هنوز تأیید کامل نداده است.
            return max(-4, higher_tf_penalty)

        if result.consensus >= 90:
            return 8
        if result.consensus >= 80:
            return 6
        if result.consensus >= 70:
            return 4
        if result.consensus >= 60:
            return 2

    return 0



def console_report(result: ConsensusResult):
    print()
    print("=" * 70)
    print("🕓 Weighted Multi-Timeframe Consensus")
    print("=" * 70)

    for signal in result.signals:
        print(
            f"{signal.timeframe:>4} | "
            f"{signal.side:<7} | "
            f"Score {signal.score:>3} | "
            f"Confidence {signal.confidence:>3}% | "
            f"Weight {signal.weight:.2f}"
        )

    print()
    print(f"Consensus : {result.consensus}%")
    print(f"Direction : {result.direction}")
    print(f"Quality   : {result.alignment_quality}")
    print()
    print(
        f"Counts  -> Bull={result.bull_count}  "
        f"Bear={result.bear_count}  "
        f"Neutral={result.neutral_count}"
    )
    print(
        f"Weights -> Bull={result.bull_weight:.2f}  "
        f"Bear={result.bear_weight:.2f}  "
        f"Neutral={result.neutral_weight:.2f}"
    )
    print("=" * 70)



def telegram_lines(result: ConsensusResult):
    lines = []

    lines.append("🕓 *Weighted Multi-Timeframe Consensus*")
    lines.append(f"- Consensus: *{result.consensus}%*")
    lines.append(f"- Direction: *{result.direction}*")
    lines.append(f"- Quality: *{result.alignment_quality}*")
    lines.append(
        f"- Weights: LONG `{result.bull_weight:.2f}` | "
        f"SHORT `{result.bear_weight:.2f}` | "
        f"NEUTRAL `{result.neutral_weight:.2f}`"
    )
    lines.append("")

    for signal in result.signals:
        lines.append(
            f"• {signal.timeframe}: {signal.side} "
            f"({signal.score}) | W `{signal.weight:.2f}`"
        )

    return lines
