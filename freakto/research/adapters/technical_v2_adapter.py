"""Adapters connecting public/local OHLCV to Technical Engine v2.

This is the only integration seam.  The challenger never imports or mutates
the Decision Engine, Market Replay, Backtest, or decision evaluator.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import SimpleNamespace

import pandas as pd

from freakto.technical_v2 import TechnicalEngineV2, analysis_profile
from freakto.technical_v2.contracts import TechnicalDecision


def _closed(frame: pd.DataFrame, *, drop_forming: bool) -> pd.DataFrame:
    usable = frame.iloc[:-1] if drop_forming and len(frame) > 40 else frame
    return usable.reset_index(drop=True)


def decision_to_showcase_signal(decision: TechnicalDecision, *, provider: str, analysis_depth: int):
    payload = decision.to_dict()
    long_count = sum(item.direction > 0 for item in decision.evidence)
    short_count = sum(item.direction < 0 for item in decision.evidence)
    neutral_count = len(decision.evidence) - long_count - short_count
    confluence = round(max(long_count, short_count) / max(1, long_count + short_count) * 100)
    profile = analysis_profile(analysis_depth)
    votes = {item.name: "LONG" if item.direction > 0 else "SHORT" if item.direction < 0 else "NEUTRAL" for item in decision.evidence}
    return SimpleNamespace(
        side=decision.side,
        decision_timestamp=decision.timestamp,
        score=round(50 + abs(decision.raw_score) * 50),
        confidence=round(decision.confidence * 100),
        recommendation=decision.recommendation,
        regime=decision.regime.label,
        provider=provider,
        analysis_depth=str(profile["label"]),
        analysis_depth_value=int(profile["depth"]),
        indicators_used=list(votes),
        indicator_votes=votes,
        technical_long_votes=long_count,
        technical_short_votes=short_count,
        technical_neutral_votes=neutral_count,
        technical_confluence_pct=confluence,
        technical_v2=payload,
        family_scores=[item.to_dict() for item in decision.family_scores],
        timeframe_scores=dict(decision.timeframe_scores),
        timeframe_agreement=decision.timeframe_agreement,
        trade_geometry=decision.geometry.to_dict(),
        risk_assessment=decision.risk.to_dict(),
        calibration=decision.calibration.to_dict(),
        decision_reasons=list(decision.reasons),
        decision_warnings=list(decision.warnings),
        engine_version=decision.engine_version,
    )


class TechnicalV2FrameAdapter:
    def __init__(self, *, risk_level: int, analysis_depth: int):
        self.analysis_depth = int(analysis_depth)
        self.engine = TechnicalEngineV2(analysis_depth=analysis_depth, risk_level=risk_level)
        self.calibration_observations: list[tuple[float, bool]] = []

    def set_calibration_observations(self, observations: list[tuple[float, bool]]) -> None:
        self.calibration_observations = list(observations)[-1000:]

    def signal(
        self,
        symbol: str,
        frames: Mapping[str, pd.DataFrame],
        *,
        timestamp: str,
        provider: str,
        drop_forming: bool = False,
    ):
        closed_frames = {name: _closed(frame, drop_forming=drop_forming) for name, frame in frames.items()}
        decision = self.engine.analyse(
            symbol,
            closed_frames,
            timestamp=timestamp,
            calibration_observations=self.calibration_observations,
        )
        return decision_to_showcase_signal(decision, provider=provider, analysis_depth=self.analysis_depth)


class PublicMultiTimeframeAdapter(TechnicalV2FrameAdapter):
    def __init__(
        self,
        fetcher: Callable[..., pd.DataFrame],
        *,
        risk_level: int,
        analysis_depth: int,
        limit: int = 140,
    ):
        super().__init__(risk_level=risk_level, analysis_depth=analysis_depth)
        self.fetcher = fetcher
        self.limit = max(80, int(limit))

    def fetch_frames(self, symbol: str) -> tuple[dict[str, pd.DataFrame], str]:
        profile = analysis_profile(self.analysis_depth)
        frames = {}
        provider = "public-ohlcv"
        for timeframe in profile["timeframes"]:
            frame = self.fetcher(symbol=symbol, timeframe=timeframe, limit=self.limit)
            if frame is None or frame.empty:
                raise RuntimeError(f"No usable {timeframe} public OHLCV for {symbol}")
            frames[str(timeframe)] = frame
            provider = str(getattr(frame, "attrs", {}).get("provider", provider))
        return frames, provider
