"""Fail-closed execution policy shared by CLI and paper operations."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Mapping


@dataclass(frozen=True)
class SafetyPolicy:
    live_orders_enabled: bool = False
    real_capital_enabled: bool = False
    allocation_pct: float = 0.0

    def __post_init__(self) -> None:
        if self.live_orders_enabled or self.real_capital_enabled or self.allocation_pct != 0.0:
            raise ValueError("Freakto paper policy must remain fail-closed")

    def payload(self) -> dict[str, bool | float]:
        return {
            "live_orders_enabled": self.live_orders_enabled,
            "real_capital_enabled": self.real_capital_enabled,
            "allocation_pct": self.allocation_pct,
        }

    def child_environment(self, parent: Mapping[str, str] | None = None) -> dict[str, str]:
        environment = dict(os.environ if parent is None else parent)
        environment.update(
            {
                "PYTHONUTF8": "1",
                "LIVE_TRADING_ENABLED": "false",
                "REAL_CAPITAL_ENABLED": "false",
            }
        )
        return environment


PAPER_SAFETY = SafetyPolicy()
