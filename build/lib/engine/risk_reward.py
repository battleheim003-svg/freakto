"""
engine.risk_reward

Risk/Reward Engine for Freakto v2.7.0.

This module calculates directional trade levels and R:R ratios from an
OpportunityV2 object. It is intentionally defensive: if a setup is not
directional or zones are not available, it returns a non-tradable result
instead of raising.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .common import fmt_price


@dataclass
class TargetRR:
    label: str
    price: Optional[float]
    rr: Optional[float]


@dataclass
class RiskRewardResult:
    is_valid: bool
    side: str
    entry: Optional[float] = None
    stop: Optional[float] = None
    stop_distance_pct: Optional[float] = None
    targets: List[TargetRR] = field(default_factory=list)
    reason: str = ""

    @property
    def best_rr(self) -> float:
        values = [target.rr for target in self.targets if target.rr is not None]
        return max(values) if values else 0.0

    @property
    def first_rr(self) -> float:
        for target in self.targets:
            if target.rr is not None:
                return float(target.rr)
        return 0.0


def _to_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        text = str(value).strip().replace(",", "")
        if not text or text in {"---", "نامشخص"}:
            return None
        return float(text)
    except Exception:
        return None


def _parse_zone_midpoint(zone: str) -> Optional[float]:
    if not zone or "نامشخص" in str(zone):
        return None

    parts = str(zone).replace("`", "").split("-")
    numbers = [_to_float(part) for part in parts]
    numbers = [number for number in numbers if number is not None]

    if not numbers:
        return None

    return sum(numbers) / len(numbers)


def _parse_price(value: str) -> Optional[float]:
    return _to_float(str(value).replace("`", ""))


def calculate_risk_reward(opportunity) -> RiskRewardResult:
    side = getattr(opportunity, "side", "NEUTRAL")

    if side not in {"LONG", "SHORT"}:
        return RiskRewardResult(
            is_valid=False,
            side=side,
            reason="Bias جهت‌دار نیست؛ R:R محاسبه نمی‌شود.",
        )

    entry = _parse_zone_midpoint(getattr(opportunity, "entry_zone", ""))
    stop = _parse_price(getattr(opportunity, "stop_zone", ""))

    if entry is None or stop is None or entry <= 0:
        return RiskRewardResult(
            is_valid=False,
            side=side,
            reason="Entry/Stop معتبر برای محاسبه R:R وجود ندارد.",
        )

    risk_abs = abs(entry - stop)
    if risk_abs <= 0:
        return RiskRewardResult(
            is_valid=False,
            side=side,
            entry=entry,
            stop=stop,
            reason="فاصله Entry تا Stop صفر یا نامعتبر است.",
        )

    stop_distance_pct = (risk_abs / entry) * 100
    targets = []

    for index, target_raw in enumerate(getattr(opportunity, "targets", []) or [], start=1):
        target_price = _parse_price(target_raw)
        rr = None

        if target_price is not None:
            reward_abs = target_price - entry if side == "LONG" else entry - target_price
            rr = max(0.0, reward_abs / risk_abs)

        targets.append(
            TargetRR(
                label=f"T{index}",
                price=target_price,
                rr=round(rr, 2) if rr is not None else None,
            )
        )

    return RiskRewardResult(
        is_valid=True,
        side=side,
        entry=entry,
        stop=stop,
        stop_distance_pct=round(stop_distance_pct, 3),
        targets=targets,
    )


def format_risk_reward_lines(result: RiskRewardResult) -> List[str]:
    lines = ["*Risk / Reward:*"]

    if not result.is_valid:
        lines.append(f"- {result.reason}")
        return lines

    lines.append(f"- Entry: `{fmt_price(result.entry)}`")
    lines.append(f"- Stop: `{fmt_price(result.stop)}`")
    lines.append(f"- Stop Distance: `{result.stop_distance_pct:.2f}%`")

    if result.targets:
        lines.append("- Targets R:R:")
        for target in result.targets:
            if target.price is None or target.rr is None:
                continue
            lines.append(f"  • {target.label}: `{fmt_price(target.price)}` | R:R `{target.rr:.2f}`")
    else:
        lines.append("- Target معتبری برای R:R وجود ندارد.")

    return lines
