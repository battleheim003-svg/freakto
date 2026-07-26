"""Public, credential-free intraday technical feed for Showcase Paper only."""

from __future__ import annotations

from dataclasses import dataclass
import time

from data_fetcher import fetch_ohlcv

from freakto.showcase_paper.risk import risk_policy
from freakto.showcase_paper.technical import build_technical_signal


@dataclass(frozen=True)
class IntradaySnapshot:
    symbol: str
    last: float
    bid: float
    ask: float
    provider: str


class LiveIntradayTechnicalMarket:
    def __init__(self, *, risk_level: int, timeframe: str = "5m", limit: int = 120):
        self.policy = risk_policy(risk_level)
        self.timeframe = timeframe
        self.limit = max(40, int(limit))
        self.cache: dict[str, tuple[float, object]] = {}

    def _frame(self, symbol: str, *, refresh: bool) -> object:
        cached = self.cache.get(symbol)
        if cached and (not refresh or time.monotonic() - cached[0] < 3.0):
            return cached[1]
        frame = fetch_ohlcv(symbol=symbol, timeframe=self.timeframe, limit=self.limit)
        if frame is None or frame.empty or len(frame) < 30:
            raise RuntimeError(f"No usable {self.timeframe} public OHLCV for {symbol}")
        self.cache[symbol] = (time.monotonic(), frame)
        return frame

    def signal(self, symbol: str):
        frame = self._frame(symbol, refresh=True)
        timestamp = str(frame.iloc[-1].get("timestamp", ""))
        provider = str(getattr(frame, "attrs", {}).get("provider", "public-ohlcv"))
        return build_technical_signal(
            frame.iloc[-30:], self.policy, timestamp=timestamp,
            regime=f"LIVE_INTRADAY_{self.timeframe.upper()}", provider=provider,
        )

    def fetch_snapshot(self, symbol: str) -> IntradaySnapshot:
        frame = self._frame(symbol, refresh=True)
        last = float(frame.iloc[-1]["close"])
        spread = max(last * 0.0002, 1e-12)
        provider = str(getattr(frame, "attrs", {}).get("provider", "public-ohlcv"))
        return IntradaySnapshot(symbol=symbol, last=last, bid=last - spread / 2, ask=last + spread / 2, provider=provider)
