"""Universe selection and replay-history readiness for the live demo."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_UNIVERSE_PATH = Path("live_demo_universe.json")
VALID_GROUPS = ("core", "growth", "meme")


@dataclass(frozen=True)
class UniverseConfig:
    groups: dict[str, tuple[str, ...]]
    timeframe: str
    target_years: float
    minimum_coverage_pct: float
    discover_listing_boundary: bool

    @property
    def all_symbols(self) -> tuple[str, ...]:
        return _dedupe(symbol for group in VALID_GROUPS for symbol in self.groups.get(group, ()))


def _dedupe(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value).upper().strip() for value in values if str(value).strip()))


def load_universe(path: str | Path = DEFAULT_UNIVERSE_PATH) -> UniverseConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if int(payload.get("schema_version", 0)) != 1:
        raise ValueError("unsupported live demo universe schema")
    raw_groups = payload.get("groups") or {}
    groups = {name: _dedupe(raw_groups.get(name, [])) for name in VALID_GROUPS}
    if not any(groups.values()):
        raise ValueError("live demo universe contains no symbols")
    for symbol in _dedupe(symbol for values in groups.values() for symbol in values):
        if "/" not in symbol or not symbol.endswith("/USDT"):
            raise ValueError(f"invalid USDT spot symbol: {symbol}")
    history = payload.get("history") or {}
    return UniverseConfig(
        groups=groups,
        timeframe=str(history.get("timeframe", "4h")),
        target_years=float(history.get("target_years", 3.0)),
        minimum_coverage_pct=float(history.get("minimum_coverage_pct", 90.0)),
        discover_listing_boundary=bool(history.get("discover_listing_boundary", True)),
    )


def select_symbols(
    universe: UniverseConfig,
    *,
    groups: Iterable[str] = ("core", "growth", "meme"),
    explicit_symbols: Iterable[str] = (),
) -> tuple[str, ...]:
    explicit = _dedupe(explicit_symbols)
    if explicit:
        return explicit
    selected = []
    for group in groups:
        name = str(group).lower().strip()
        if name not in VALID_GROUPS:
            raise ValueError(f"unknown universe group: {group}")
        selected.extend(universe.groups.get(name, ()))
    return _dedupe(selected)


def history_status(universe: UniverseConfig, symbols: Iterable[str], data_dir: str = "data/market_replay"):
    from engine.historical_data_store import scan_historical_data

    return scan_historical_data(
        symbols=list(symbols),
        timeframe=universe.timeframe,
        years=universe.target_years,
        data_dir=data_dir,
    )


def build_history(universe: UniverseConfig, symbols: Iterable[str], data_dir: str = "data/market_replay"):
    from engine.historical_data_store import HistoricalDataRequest, build_historical_data

    request = HistoricalDataRequest(
        symbols=list(symbols),
        timeframe=universe.timeframe,
        years=universe.target_years,
        exchange="auto",
        exchange_order=["kucoin", "okx", "bybit", "kraken"],
        min_acceptable_coverage_pct=universe.minimum_coverage_pct,
        data_dir=data_dir,
        update_existing=True,
        discover_listing_boundary=universe.discover_listing_boundary,
    )
    return build_historical_data(request)
