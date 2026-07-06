"""
engine.position_size

Position Sizing Engine for Freakto v2.7.0.

It calculates the notional position size required to risk a configured
percentage of account capital from entry to stop.
"""

from dataclasses import dataclass
from typing import List, Optional

from .common import fmt_price
from .risk_reward import RiskRewardResult


@dataclass
class PositionSizeResult:
    is_valid: bool
    account_size: float
    risk_pct: float
    risk_amount: float
    position_notional: Optional[float] = None
    position_units: Optional[float] = None
    stop_distance_pct: Optional[float] = None
    reason: str = ""


def calculate_position_size(
    rr: RiskRewardResult,
    account_size: float = 10_000.0,
    risk_pct: float = 1.0,
) -> PositionSizeResult:
    account_size = max(0.0, float(account_size or 0))
    risk_pct = max(0.0, float(risk_pct or 0))
    risk_amount = account_size * risk_pct / 100

    if not rr.is_valid or rr.entry is None or rr.stop is None:
        return PositionSizeResult(
            is_valid=False,
            account_size=account_size,
            risk_pct=risk_pct,
            risk_amount=risk_amount,
            reason="برای محاسبه Position Size، Entry/Stop معتبر لازم است.",
        )

    risk_per_unit = abs(rr.entry - rr.stop)
    if risk_per_unit <= 0:
        return PositionSizeResult(
            is_valid=False,
            account_size=account_size,
            risk_pct=risk_pct,
            risk_amount=risk_amount,
            reason="فاصله Stop نامعتبر است.",
        )

    units = risk_amount / risk_per_unit
    notional = units * rr.entry

    return PositionSizeResult(
        is_valid=True,
        account_size=account_size,
        risk_pct=risk_pct,
        risk_amount=risk_amount,
        position_notional=round(notional, 2),
        position_units=round(units, 8),
        stop_distance_pct=rr.stop_distance_pct,
    )


def format_position_size_lines(result: PositionSizeResult) -> List[str]:
    lines = ["*Position Sizing:*"]
    lines.append(f"- Account: `${result.account_size:,.2f}`")
    lines.append(f"- Risk: `{result.risk_pct:.2f}%` = `${result.risk_amount:,.2f}`")

    if not result.is_valid:
        lines.append(f"- {result.reason}")
        return lines

    lines.append(f"- Position Notional: `${result.position_notional:,.2f}`")
    lines.append(f"- Position Units: `{result.position_units}`")
    if result.stop_distance_pct is not None:
        lines.append(f"- Based on Stop Distance: `{result.stop_distance_pct:.2f}%`")

    return lines
