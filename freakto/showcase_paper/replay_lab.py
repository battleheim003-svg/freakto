"""Accelerated, local-data market for short Showcase Paper sessions.

This is deliberately a development lab, not a backtest and not official Paper
evidence.  It advances through cached OHLCV one row per worker scan so users can
observe several simulated trade lifecycles in minutes without an exchange API.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from freakto.research.adapters.technical_v2_adapter import TechnicalV2FrameAdapter
from freakto.technical_v2.service import analysis_profile


@dataclass(frozen=True)
class ReplaySnapshot:
    symbol: str
    last: float
    bid: float
    ask: float
    open: float
    high: float
    low: float
    timestamp: str
    bar_index: int
    provider: str = "accelerated-local-replay"


class AcceleratedReplayMarket:
    def __init__(self, root: Path, symbols: tuple[str, ...], *, timeframe: str = "AUTO", risk_level: int = 70, analysis_depth: int | None = None):
        self.root = Path(root)
        self.symbols = symbols
        requested = str(timeframe or "AUTO")
        if requested.upper() == "AUTO":
            requested = next(
                (
                    candidate for candidate in ("15m", "1h", "4h")
                    if all(
                        (self.root / "data" / "market_replay" / candidate / f'{symbol.replace("/", "_")}.csv.gz').is_file()
                        for symbol in symbols
                    )
                ),
                "4h",
            )
        self.timeframe = requested
        self.analysis_depth = int(risk_level if analysis_depth is None else analysis_depth)
        self.adapter = TechnicalV2FrameAdapter(risk_level=risk_level, analysis_depth=self.analysis_depth)
        self.frames: dict[str, pd.DataFrame] = {}
        self.daily_frames: dict[str, pd.DataFrame] = {}
        self.cursors: dict[str, int] = {}
        for symbol in symbols:
            path = self.root / "data" / "market_replay" / self.timeframe / f'{symbol.replace("/", "_")}.csv.gz'
            frame = pd.read_csv(path)
            required = {"timestamp", "open", "high", "low", "close"}
            if not required.issubset(frame.columns) or len(frame) < 40:
                raise ValueError(f"Replay dataset is not usable: {path}")
            frame = frame.dropna(subset=list(required)).reset_index(drop=True)
            self.frames[symbol] = frame
            daily_path = self.root / "data" / "market_replay" / "1d" / f'{symbol.replace("/", "_")}.csv.gz'
            if daily_path.is_file():
                daily = pd.read_csv(daily_path).dropna(subset=list(required)).reset_index(drop=True)
                if len(daily) >= 40:
                    self.daily_frames[symbol] = daily
            # Keep enough warm-up history and a useful recent test segment.
            self.cursors[symbol] = min(len(frame) - 1, max(39, len(frame) - 90))

    def _row(self, symbol: str):
        frame = self.frames[symbol]
        return frame.iloc[self.cursors[symbol]]

    def fetch_snapshot(self, symbol: str) -> ReplaySnapshot:
        row = self._row(symbol)
        last = float(row["close"])
        spread = max(last * 0.0002, 1e-12)
        return ReplaySnapshot(
            symbol=symbol,
            last=last,
            bid=last - spread / 2,
            ask=last + spread / 2,
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            timestamp=str(row["timestamp"]),
            bar_index=int(self.cursors[symbol]),
        )

    def signal(self, symbol: str):
        frame = self.frames[symbol]
        cursor = self.cursors[symbol]
        window = frame.iloc[max(0, cursor - 139): cursor + 1]
        frames = {self.timeframe: window}
        if symbol in self.daily_frames:
            current = pd.to_datetime(self._row(symbol)["timestamp"], utc=True)
            daily = self.daily_frames[symbol]
            timestamps = pd.to_datetime(daily["timestamp"], utc=True)
            causal_daily = daily.loc[timestamps <= current].tail(140)
            if len(causal_daily) >= 40:
                frames["1d"] = causal_daily
        signal = self.adapter.signal(
            symbol, frames, timestamp=str(self._row(symbol)["timestamp"]), provider="local-cache",
        )
        return signal

    def advance(self) -> None:
        for symbol, frame in self.frames.items():
            next_cursor = self.cursors[symbol] + 1
            self.cursors[symbol] = next_cursor if next_cursor < len(frame) else min(len(frame) - 1, max(39, len(frame) - 90))

    def progress(self) -> dict[str, object]:
        return {
            "timeframe": self.timeframe,
            "provider": "accelerated-local-replay",
            "analysis_depth": analysis_profile(self.analysis_depth),
            "cursors": {symbol: int(cursor) for symbol, cursor in self.cursors.items()},
            "timestamps": {symbol: str(self._row(symbol)["timestamp"]) for symbol in self.symbols},
        }
