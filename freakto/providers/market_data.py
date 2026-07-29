"""Provider-neutral market-data contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable


@dataclass(frozen=True)
class ProviderFailure:
    provider: str
    category: str
    message: str
    retryable: bool = False


@runtime_checkable
class MarketDataProvider(Protocol):
    """Minimum causal OHLCV interface required by research and paper layers."""

    name: str

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        *,
        since_ms: int | None = None,
        limit: int | None = None,
    ) -> Sequence[Mapping[str, Any]]:
        """Return timestamped closed/open candle records without domain scoring."""
        ...
