from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from engine.historical_data_store import (
    HistoricalDataRequest,
    build_symbol_history,
    fetch_exchange_history,
    load_history,
)


class ListingAwareExchange:
    def __init__(self, symbol: str, listing: datetime, end: datetime, *, provider: str = "kucoin"):
        self.symbol = symbol
        self.provider = provider
        self.markets = {symbol: {}}
        self.calls = []
        timestamps = pd.date_range(listing, end, freq="4h", tz="UTC")
        self.rows = []
        for index, ts in enumerate(timestamps):
            base = 100.0 + index
            self.rows.append([
                int(ts.timestamp() * 1000),
                base,
                base + 1.0,
                base - 1.0,
                base + 0.25,
                1_000.0,
            ])
        self.listing_ms = int(pd.Timestamp(listing).timestamp() * 1000)

    def load_markets(self):
        return self.markets

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        self.calls.append(int(since))
        if symbol != self.symbol or int(since) < self.listing_ms:
            return []
        available = [row for row in self.rows if int(row[0]) >= int(since)]
        return available[:limit]

    def close(self):
        return None


class EmptyExchange:
    def __init__(self, symbol: str):
        self.markets = {symbol: {}}

    def load_markets(self):
        return self.markets

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        return []

    def close(self):
        return None


def test_listing_discovery_advances_empty_ranges_and_recovers_first_candle():
    symbol = "SOL/USDT"
    start = datetime(2017, 1, 1, tzinfo=timezone.utc)
    listing = datetime(2020, 4, 10, tzinfo=timezone.utc)
    end = listing + timedelta(days=5)
    exchange = ListingAwareExchange(symbol, listing, end)

    frame = fetch_exchange_history(
        exchange_name="kucoin",
        symbol=symbol,
        timeframe="4h",
        start=start,
        end=end,
        exchange_factory=lambda _: exchange,
        discover_listing_boundary=True,
        listing_probe_days=120,
        max_listing_probes=80,
    )

    assert not frame.empty
    assert frame["timestamp"].min() == pd.Timestamp(listing)
    assert frame.attrs["listing_boundary_discovered"] is True
    assert frame.attrs["listing_probe_count"] > 1
    assert len(exchange.calls) > 1


def test_default_fetch_still_stops_on_initial_empty_batch():
    symbol = "SOL/USDT"
    start = datetime(2017, 1, 1, tzinfo=timezone.utc)
    listing = datetime(2020, 4, 10, tzinfo=timezone.utc)
    end = listing + timedelta(days=2)
    exchange = ListingAwareExchange(symbol, listing, end)

    frame = fetch_exchange_history(
        exchange_name="kucoin",
        symbol=symbol,
        timeframe="4h",
        start=start,
        end=end,
        exchange_factory=lambda _: exchange,
        discover_listing_boundary=False,
    )

    assert frame.empty
    assert len(exchange.calls) == 1


def test_full_history_falls_back_to_one_provider_without_mixing(tmp_path: Path):
    symbol = "BTC/USDT"
    start = datetime(2017, 1, 1, tzinfo=timezone.utc)
    listing = datetime(2019, 1, 1, tzinfo=timezone.utc)
    end = listing + timedelta(days=10)
    exchanges = {
        "kucoin": EmptyExchange(symbol),
        "okx": ListingAwareExchange(symbol, listing, end, provider="okx"),
    }

    request = HistoricalDataRequest(
        symbols=[symbol],
        timeframe="4h",
        start_utc=start.isoformat(),
        end_utc=end.isoformat(),
        exchange="auto",
        exchange_order=["kucoin", "okx"],
        data_dir=str(tmp_path),
        update_existing=True,
        force_refresh=True,
        min_acceptable_coverage_pct=90.0,
        discover_listing_boundary=True,
        listing_probe_days=120,
        max_listing_probes=80,
    )
    result = build_symbol_history(request, symbol, exchange_factory=lambda name: exchanges[name])

    assert result.ok is True
    assert result.provider == "okx"
    assert result.listing_boundary_discovered is True
    saved = load_history(symbol, "4h", tmp_path)
    assert set(saved["provider"].unique()) == {"okx"}
    assert saved["timestamp"].min() == pd.Timestamp(listing)
