"""Research-only adapters for non-crypto market data."""

from freakto.markets.archive import DatasetManifest, persist_replay_dataset
from freakto.markets.config import MarketConfig, load_market_config
from freakto.markets.dukascopy import DukascopyAdapter, DukascopyError
from freakto.markets.twelve_data import TwelveDataAdapter, TwelveDataError

__all__ = [
    "DatasetManifest",
    "DukascopyAdapter",
    "DukascopyError",
    "MarketConfig",
    "TwelveDataAdapter",
    "TwelveDataError",
    "load_market_config",
    "persist_replay_dataset",
]
