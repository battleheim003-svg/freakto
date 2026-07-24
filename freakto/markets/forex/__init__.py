"""Forex market adapter configuration boundary."""

from __future__ import annotations

from pathlib import Path

from freakto.markets.config import MarketConfig, load_market_config

DEFAULT_CONFIG = Path("config") / "markets" / "forex.json"


def config(path: str | Path = DEFAULT_CONFIG) -> MarketConfig:
    return load_market_config(path)


__all__ = ["DEFAULT_CONFIG", "config"]
