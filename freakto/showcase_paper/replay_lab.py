"""Accelerated, local-data market for short Showcase Paper sessions.

This is deliberately a development lab, not a backtest and not official Paper
evidence.  It advances through cached OHLCV one row per worker scan so users can
observe several simulated trade lifecycles in minutes without an exchange API.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from freakto.showcase_paper.risk import risk_policy
from freakto.showcase_paper.technical import build_technical_signal


@dataclass(frozen=True)
class ReplaySnapshot:
    symbol: str
    last: float
    bid: float
    ask: float
    provider: str = "accelerated-local-replay"


class AcceleratedReplayMarket:
    def __init__(self, root: Path, symbols: tuple[str, ...], *, timeframe: str = "4h", risk_level: int = 70):
        self.root = Path(root)
        self.symbols = symbols
        self.timeframe = timeframe
        self.policy = risk_policy(risk_level)
        self.frames: dict[str, pd.DataFrame] = {}
        self.cursors: dict[str, int] = {}
        for symbol in symbols:
            path = self.root / "data" / "market_replay" / timeframe / f'{symbol.replace("/", "_")}.csv.gz'
            frame = pd.read_csv(path)
            required = {"timestamp", "open", "high", "low", "close"}
            if not required.issubset(frame.columns) or len(frame) < 40:
                raise ValueError(f"Replay dataset is not usable: {path}")
            frame = frame.dropna(subset=list(required)).reset_index(drop=True)
            self.frames[symbol] = frame
            # Keep enough warm-up history and a useful recent test segment.
            self.cursors[symbol] = max(30, len(frame) - 90)

    def _row(self, symbol: str):
        frame = self.frames[symbol]
        return frame.iloc[self.cursors[symbol]]

    def fetch_snapshot(self, symbol: str) -> ReplaySnapshot:
        row = self._row(symbol)
        last = float(row["close"])
        spread = max(last * 0.0002, 1e-12)
        return ReplaySnapshot(symbol=symbol, last=last, bid=last - spread / 2, ask=last + spread / 2)

    def signal(self, symbol: str):
        frame = self.frames[symbol]
        cursor = self.cursors[symbol]
        window = frame.iloc[max(0, cursor - 29): cursor + 1]
        return build_technical_signal(
            window,
            self.policy,
            timestamp=str(self._row(symbol)["timestamp"]),
            regime="ACCELERATED_REPLAY",
            provider="local-cache",
        )

    def advance(self) -> None:
        for symbol, frame in self.frames.items():
            next_cursor = self.cursors[symbol] + 1
            self.cursors[symbol] = next_cursor if next_cursor < len(frame) else max(30, len(frame) - 90)

    def progress(self) -> dict[str, object]:
        return {
            "timeframe": self.timeframe,
            "provider": "accelerated-local-replay",
            "analysis_depth": self.policy.analysis_depth,
            "indicators_used": list(self.policy.technical_indicators),
            "cursors": {symbol: int(cursor) for symbol, cursor in self.cursors.items()},
            "timestamps": {symbol: str(self._row(symbol)["timestamp"]) for symbol in self.symbols},
        }
