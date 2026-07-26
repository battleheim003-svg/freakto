"""Explainable trend/volatility regime classifier."""

from __future__ import annotations

import pandas as pd

from freakto.technical_v2.contracts import RegimeAssessment
from freakto.technical_v2.features import atr_series, clamp, validate_frame


def assess_regime(frame: pd.DataFrame) -> RegimeAssessment:
    data = validate_frame(frame)
    close = data["close"]
    atr = atr_series(data).replace(0, 1e-12)
    trend = clamp(float((close.ewm(span=20, adjust=False).mean().iloc[-1] - close.ewm(span=50, adjust=False).mean().iloc[-1]) / atr.iloc[-1]) / 2)
    normalized_atr = atr / close
    history = normalized_atr.dropna().tail(100)
    percentile = float((history <= history.iloc[-1]).mean()) if len(history) else 0.5
    trending = abs(trend) >= 0.35
    high_vol = percentile >= 0.70
    label = ("UPTREND" if trend > 0 else "DOWNTREND") if trending else "RANGE"
    if high_vol:
        label += "_HIGH_VOL"
    weights = {
        "trend": 1.35 if trending else 0.75,
        "momentum": 1.20 if trending else 0.85,
        "mean_reversion": 0.55 if trending else 1.35,
        "structure": 1.20,
        "volume": 1.05,
        "volatility": 0.90 if high_vol else 1.0,
    }
    confidence = min(1.0, 0.5 + abs(trend) * 0.35 + abs(percentile - 0.5) * 0.2)
    return RegimeAssessment(label, round(trend, 4), round(percentile, 4), round(confidence, 4), weights)
