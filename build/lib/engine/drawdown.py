"""
engine.drawdown

Historical drawdown estimation from similar snapshots.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DrawdownResult:
    is_valid: bool
    sample_size: int = 0
    expected_drawdown_pct: Optional[float] = None
    worst_drawdown_pct: Optional[float] = None
    expected_runup_pct: Optional[float] = None
    reason: str = ""


def calculate_drawdown_from_similarity(similarity_result) -> DrawdownResult:
    matches = getattr(similarity_result, "matches", []) or []
    evaluated = [item for item in matches if getattr(item, "mae_pct", None) is not None]

    if not evaluated:
        return DrawdownResult(
            is_valid=False,
            reason="نمونه تاریخی کافی برای تخمین Drawdown وجود ندارد.",
        )

    # mae_pct is already directional in historical_outcomes. Negative values are adverse.
    adverse_values = [float(item.mae_pct) for item in evaluated]
    runup_values = [float(item.mfe_pct) for item in evaluated if getattr(item, "mfe_pct", None) is not None]

    expected_dd = sum(adverse_values) / len(adverse_values)
    worst_dd = min(adverse_values)
    expected_runup = sum(runup_values) / len(runup_values) if runup_values else None

    return DrawdownResult(
        is_valid=True,
        sample_size=len(evaluated),
        expected_drawdown_pct=round(expected_dd, 2),
        worst_drawdown_pct=round(worst_dd, 2),
        expected_runup_pct=round(expected_runup, 2) if expected_runup is not None else None,
    )


def format_drawdown_lines(result: DrawdownResult) -> List[str]:
    lines = ["*Historical Drawdown:*"]

    if not result.is_valid:
        lines.append(f"- {result.reason}")
        return lines

    lines.append(f"- Samples: `{result.sample_size}`")
    lines.append(f"- Expected Drawdown: `{result.expected_drawdown_pct:.2f}%`")
    lines.append(f"- Worst Drawdown: `{result.worst_drawdown_pct:.2f}%`")

    if result.expected_runup_pct is not None:
        lines.append(f"- Expected Run-up: `{result.expected_runup_pct:.2f}%`")

    return lines
