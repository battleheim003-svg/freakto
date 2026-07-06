"""
engine.kelly

Conservative Kelly sizing helpers for Freakto v2.7.0.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class KellyResult:
    is_valid: bool
    win_rate: Optional[float] = None
    reward_risk: Optional[float] = None
    raw_kelly_pct: float = 0.0
    conservative_kelly_pct: float = 0.0
    recommended_risk_pct: float = 1.0
    reason: str = ""


def calculate_kelly(win_rate_pct: Optional[float], reward_risk: Optional[float]) -> KellyResult:
    if win_rate_pct is None or reward_risk is None or reward_risk <= 0:
        return KellyResult(
            is_valid=False,
            recommended_risk_pct=1.0,
            reason="داده کافی برای Kelly وجود ندارد؛ ریسک پایه 1% استفاده می‌شود.",
        )

    p = max(0.0, min(1.0, float(win_rate_pct) / 100))
    b = max(0.01, float(reward_risk))
    q = 1 - p

    raw = ((b * p) - q) / b
    raw_pct = max(0.0, raw * 100)

    # Conservative Kelly: use 25% Kelly and cap at 2% for safety.
    conservative = min(2.0, raw_pct * 0.25)

    # Keep a practical minimum for good but uncertain systems.
    recommended = 0.5 if conservative <= 0 else max(0.5, conservative)

    return KellyResult(
        is_valid=True,
        win_rate=round(win_rate_pct, 2),
        reward_risk=round(reward_risk, 2),
        raw_kelly_pct=round(raw_pct, 2),
        conservative_kelly_pct=round(conservative, 2),
        recommended_risk_pct=round(recommended, 2),
    )


def format_kelly_lines(result: KellyResult) -> List[str]:
    lines = ["*Kelly Risk Model:*"]

    if not result.is_valid:
        lines.append(f"- {result.reason}")
        lines.append(f"- Recommended Risk: `{result.recommended_risk_pct:.2f}%`")
        return lines

    lines.append(f"- Historical Win Rate: `{result.win_rate:.1f}%`")
    lines.append(f"- Reward/Risk Used: `{result.reward_risk:.2f}`")
    lines.append(f"- Raw Kelly: `{result.raw_kelly_pct:.2f}%`")
    lines.append(f"- Conservative Kelly: `{result.conservative_kelly_pct:.2f}%`")
    lines.append(f"- Recommended Risk: `{result.recommended_risk_pct:.2f}%`")

    return lines
