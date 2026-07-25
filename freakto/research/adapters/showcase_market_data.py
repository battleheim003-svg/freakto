"""Public-price adapter for the isolated Showcase Paper layer."""

from __future__ import annotations

from engine.live_demo import CcxtPublicMarketData, DEFAULT_PUBLIC_EXCHANGES


def build_showcase_market_data():
    """Return the existing public-data-only adapter; no exchange credentials."""
    return CcxtPublicMarketData(DEFAULT_PUBLIC_EXCHANGES)
