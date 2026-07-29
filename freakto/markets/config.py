"""Fail-closed configuration contracts for new market adapters."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MarketConfig:
    asset_class: str
    schema_version: str
    symbols: tuple[str, ...]
    provider: str
    price_basis: str
    volume_semantics: str
    session_calendar: str
    research_only: bool
    paper_enabled: bool
    live_enabled: bool
    cost_model_status: str
    raw: dict[str, Any]

    def assert_safe(self) -> None:
        if not self.research_only:
            raise ValueError("New market configuration must remain research-only.")
        if self.paper_enabled or self.live_enabled:
            raise ValueError("Paper and Live must remain disabled before separate gates pass.")
        if self.cost_model_status != "UNVERIFIED":
            raise ValueError("Initial market cost model must be explicitly UNVERIFIED.")
        if self.price_basis not in {"bid", "ask", "mid", "last"}:
            raise ValueError("price_basis must be bid, ask, mid, or last.")
        if not self.symbols:
            raise ValueError("At least one canonical BASE/QUOTE symbol is required.")
        if any("/" not in symbol for symbol in self.symbols):
            raise ValueError("Symbols must use canonical BASE/QUOTE notation.")


def load_market_config(path: str | Path) -> MarketConfig:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    safety = payload.get("safety") or {}
    execution = payload.get("execution") or {}
    config = MarketConfig(
        asset_class=str(payload["asset_class"]).strip().lower(),
        schema_version=str(payload["schema_version"]),
        symbols=tuple(str(value).strip().upper() for value in payload["symbols"]),
        provider=str(payload["provider"]).strip().lower(),
        price_basis=str(payload["price_basis"]).strip().lower(),
        volume_semantics=str(payload["volume_semantics"]).strip(),
        session_calendar=str(payload["session_calendar"]).strip(),
        research_only=bool(safety.get("research_only")),
        paper_enabled=bool(safety.get("paper_enabled")),
        live_enabled=bool(safety.get("live_enabled")),
        cost_model_status=str(execution.get("cost_model_status", "")).strip().upper(),
        raw=payload,
    )
    config.assert_safe()
    return config
