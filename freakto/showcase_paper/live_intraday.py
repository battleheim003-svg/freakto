"""Public, credential-free intraday technical feed for Showcase Paper only."""

from __future__ import annotations

from dataclasses import dataclass
import time

from data_fetcher import fetch_ohlcv

from freakto.research.adapters.technical_v2_adapter import PublicMultiTimeframeAdapter


@dataclass(frozen=True)
class IntradaySnapshot:
    symbol: str
    last: float
    bid: float
    ask: float
    provider: str


class LiveIntradayTechnicalMarket:
    def __init__(self, *, risk_level: int, analysis_depth: int | None = None, timeframe: str = "1m", limit: int = 140):
        self.analysis_depth = int(risk_level if analysis_depth is None else analysis_depth)
        self.timeframe = timeframe
        self.limit = max(40, int(limit))
        self.cache: dict[tuple[str, str], tuple[float, object]] = {}
        self.adapter = PublicMultiTimeframeAdapter(
            self._fetch, risk_level=risk_level, analysis_depth=self.analysis_depth, limit=self.limit
        )

    def _fetch(self, *, symbol: str, timeframe: str, limit: int):
        key = (symbol, timeframe)
        cached = self.cache.get(key)
        if cached and time.monotonic() - cached[0] < 3.0:
            return cached[1]
        frame = fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        if frame is None or frame.empty or len(frame) < 40:
            raise RuntimeError(f"No usable {timeframe} public OHLCV for {symbol}")
        self.cache[key] = (time.monotonic(), frame)
        return frame

    def _frame(self, symbol: str, *, refresh: bool) -> object:
        cached = self.cache.get((symbol, self.timeframe))
        if cached and (not refresh or time.monotonic() - cached[0] < 3.0):
            return cached[1]
        frame = self._fetch(symbol=symbol, timeframe=self.timeframe, limit=self.limit)
        return frame

    def signal(self, symbol: str):
        frames, provider = self.adapter.fetch_frames(symbol)
        base = frames[next(iter(frames))]
        timestamp = str(base.iloc[-2].get("timestamp", "")) if len(base) > 40 else str(base.iloc[-1].get("timestamp", ""))
        signal = self.adapter.signal(
            symbol, frames, timestamp=timestamp, provider=provider, drop_forming=True, require_fresh=True,
        )
        return signal

    def fetch_snapshot(self, symbol: str) -> IntradaySnapshot:
        frame = self._frame(symbol, refresh=True)
        last = float(frame.iloc[-1]["close"])
        spread = max(last * 0.0002, 1e-12)
        provider = str(getattr(frame, "attrs", {}).get("provider", "public-ohlcv"))
        return IntradaySnapshot(symbol=symbol, last=last, bid=last - spread / 2, ask=last + spread / 2, provider=provider)
