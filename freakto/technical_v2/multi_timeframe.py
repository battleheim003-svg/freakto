"""Multi-timeframe alignment without leaking future candles."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from freakto.technical_v2.features import extract_evidence


DEFAULT_WEIGHTS = {"5m": 0.15, "15m": 0.20, "1h": 0.30, "4h": 0.35, "base": 1.0}


def timeframe_score(frame: pd.DataFrame, *, timeframe: str, depth: int) -> float:
    evidence = extract_evidence(frame, timeframe=timeframe, depth=depth)
    directional = [item.direction * max(0.2, item.strength) for item in evidence]
    return sum(directional) / max(1, len(directional))


def assess_timeframes(
    frames: Mapping[str, pd.DataFrame], *, depth: int = 100
) -> tuple[dict[str, float], float, float, bool]:
    if not frames:
        raise ValueError("At least one timeframe frame is required")
    scores = {name: round(timeframe_score(frame, timeframe=name, depth=depth), 4) for name, frame in frames.items()}
    weights = {name: DEFAULT_WEIGHTS.get(name, 0.2) for name in scores}
    total_weight = sum(weights.values()) or 1.0
    aggregate = sum(scores[name] * weights[name] for name in scores) / total_weight
    direction = 1 if aggregate >= 0 else -1
    agreeing_weight = sum(weights[name] for name in scores if scores[name] * direction > 0)
    agreement = agreeing_weight / total_weight
    base_name = next(iter(frames))
    counter_trend = len(scores) > 1 and scores[base_name] * aggregate < 0
    return scores, round(aggregate, 4), round(agreement, 4), counter_trend
