from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd


@dataclass
class ScoreComponent:
    name: str
    points: int
    max_points: int
    direction: str = "NEUTRAL"  # LONG / SHORT / NEUTRAL / RISK
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def normalized(self) -> float:
        if self.max_points <= 0:
            return 0.0
        return max(0.0, min(1.0, self.points / self.max_points))


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def fmt_price(value: Optional[float]) -> str:
    if value is None:
        return "نامشخص"
    if value >= 100:
        return f"{value:,.0f}"
    if value >= 1:
        return f"{value:,.2f}"
    return f"{value:,.6f}"
