"""External-data boundary contracts; concrete legacy adapters migrate in phase 5."""

from .market_data import MarketDataProvider, ProviderFailure

__all__ = ["MarketDataProvider", "ProviderFailure"]
