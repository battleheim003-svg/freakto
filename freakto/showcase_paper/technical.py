"""Causal technical-vote ensemble used only by the Showcase Paper lab."""

from __future__ import annotations

from math import ceil, isfinite
from types import SimpleNamespace

import pandas as pd

from freakto.showcase_paper.risk import RiskPolicy


ATR_GEOMETRY = {
    "PRECISION": (1.0, 1.5, 48),
    "CAUTIOUS": (1.2, 1.8, 36),
    "ACTIVE_TEST": (1.4, 2.1, 30),
    "EXPLORATORY": (1.6, 2.4, 24),
}


def _vote(condition_long: bool, condition_short: bool) -> str:
    return "LONG" if condition_long else "SHORT" if condition_short else "NEUTRAL"


def technical_votes(window: pd.DataFrame, policy: RiskPolicy) -> dict[str, str]:
    close = pd.to_numeric(window["close"], errors="coerce")
    high = pd.to_numeric(window["high"], errors="coerce")
    low = pd.to_numeric(window["low"], errors="coerce")
    opened = pd.to_numeric(window["open"], errors="coerce")
    volume = pd.to_numeric(window.get("volume", pd.Series(index=window.index, dtype=float)), errors="coerce")
    ema4 = close.ewm(span=4, adjust=False).mean()
    ema10 = close.ewm(span=10, adjust=False).mean()
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    delta = close.diff()
    gains = delta.clip(lower=0).rolling(14).mean()
    losses = (-delta.clip(upper=0)).rolling(14).mean().replace(0, 1e-12)
    rsi = 100 - 100 / (1 + gains / losses)
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    middle = close.rolling(20).mean()
    roc5 = close.pct_change(5)
    lowest = low.rolling(14).min()
    highest = high.rolling(14).max()
    stochastic = 100 * (close - lowest) / (highest - lowest).replace(0, 1e-12)
    stochastic_signal = stochastic.rolling(3).mean()
    previous_high = high.shift(1).rolling(20).max()
    previous_low = low.shift(1).rolling(20).min()
    candle_range = (high - low).replace(0, 1e-12)
    body_ratio = (close - opened) / candle_range
    true_range = pd.concat(
        [(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1
    ).max(axis=1)
    atr = true_range.rolling(14).mean()
    atr_direction = close.diff(3)
    volume_mean = volume.rolling(20).mean()
    latest_volume_mean = float(volume_mean.iloc[-1]) if pd.notna(volume_mean.iloc[-1]) else 0.0
    volume_active = bool(volume.notna().any() and volume.iloc[-1] >= latest_volume_mean)

    votes = {
        "EMA_4_10": _vote(ema4.iloc[-1] > ema10.iloc[-1], ema4.iloc[-1] < ema10.iloc[-1]),
        "PRICE_MOMENTUM": _vote(close.iloc[-1] > close.iloc[-4], close.iloc[-1] < close.iloc[-4]),
        "RSI_14": _vote(rsi.iloc[-1] >= 55, rsi.iloc[-1] <= 45),
        "EMA_10_21": _vote(ema10.iloc[-1] > ema21.iloc[-1], ema10.iloc[-1] < ema21.iloc[-1]),
        "MACD_12_26_9": _vote(macd.iloc[-1] > macd_signal.iloc[-1], macd.iloc[-1] < macd_signal.iloc[-1]),
        "BOLLINGER_POSITION": _vote(close.iloc[-1] > middle.iloc[-1], close.iloc[-1] < middle.iloc[-1]),
        "ROC_5": _vote(roc5.iloc[-1] > 0, roc5.iloc[-1] < 0),
        "STOCHASTIC_14": _vote(
            stochastic.iloc[-1] > stochastic_signal.iloc[-1] and stochastic.iloc[-1] >= 55,
            stochastic.iloc[-1] < stochastic_signal.iloc[-1] and stochastic.iloc[-1] <= 45,
        ),
        "VOLUME_CONFIRMATION": _vote(volume_active and delta.iloc[-1] > 0, volume_active and delta.iloc[-1] < 0),
        "BREAKOUT_20": _vote(close.iloc[-1] > previous_high.iloc[-1], close.iloc[-1] < previous_low.iloc[-1]),
        "CANDLE_STRUCTURE": _vote(body_ratio.iloc[-1] >= 0.2, body_ratio.iloc[-1] <= -0.2),
        "ATR_REGIME": _vote(atr.iloc[-1] > 0 and atr_direction.iloc[-1] > 0, atr.iloc[-1] > 0 and atr_direction.iloc[-1] < 0),
    }
    return {name: votes[name] for name in policy.technical_indicators}


def build_technical_signal(
    window: pd.DataFrame,
    policy: RiskPolicy,
    *,
    timestamp: str,
    regime: str,
    provider: str,
):
    if len(window) < 30:
        raise ValueError("At least 30 causal candles are required for technical confluence")
    votes = technical_votes(window, policy)
    long_votes = sum(value == "LONG" for value in votes.values())
    short_votes = sum(value == "SHORT" for value in votes.values())
    neutral_votes = len(votes) - long_votes - short_votes
    side = "NEUTRAL" if long_votes == short_votes else "LONG" if long_votes > short_votes else "SHORT"
    dominant = max(long_votes, short_votes)
    directional_votes = long_votes + short_votes
    total_indicators = len(votes)
    participation = round(dominant / max(1, total_indicators) * 100)
    directional_agreement = round(dominant / max(1, directional_votes) * 100)
    breadth_minimum = ceil(total_indicators * 0.5)
    breadth_sufficient = directional_votes >= breadth_minimum
    # This legacy Showcase signal is not the active Technical-v2 path. Keep its
    # historical linear score mapping, but feed it the corrected participation
    # metric and fail closed on insufficient breadth. No guessed recalibration.
    score = round(45 + participation * 0.45)
    confidence = round(42 + participation * 0.48)
    recommendation = (
        "MONITOR" if not breadth_sufficient or side == "NEUTRAL"
        else "ACTIONABLE" if score >= 72 else "WATCHLIST" if score >= 60 else "MONITOR"
    )

    close = pd.to_numeric(window["close"], errors="coerce")
    high = pd.to_numeric(window["high"], errors="coerce")
    low = pd.to_numeric(window["low"], errors="coerce")
    true_range = pd.concat(
        [(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1
    ).max(axis=1)
    atr_value = float(true_range.rolling(14).mean().iloc[-1])
    entry = float(close.iloc[-1])
    stop_mult, target_mult, expiry_bars = ATR_GEOMETRY[policy.key]
    if side in {"LONG", "SHORT"} and isfinite(atr_value) and atr_value > max(abs(entry) * 1e-8, 1e-12):
        stop_distance = atr_value * stop_mult
        target_distance = atr_value * target_mult
        geometry = {
            "entry": entry,
            "stop": entry - stop_distance if side == "LONG" else entry + stop_distance,
            "target": entry + target_distance if side == "LONG" else entry - target_distance,
            "expiry_bars": expiry_bars,
            "atr_value": atr_value,
            "stop_atr_multiple": stop_mult,
            "target_atr_multiple": target_mult,
            "source": "SHOWCASE_ATR_RESEARCH_V1",
        }
    else:
        geometry = {}
    return SimpleNamespace(
        side=side,
        decision_timestamp=timestamp,
        score=score,
        confidence=confidence,
        recommendation=recommendation,
        regime=regime,
        provider=provider,
        analysis_depth=policy.analysis_depth,
        indicators_used=list(votes),
        indicator_votes=votes,
        technical_long_votes=long_votes,
        technical_short_votes=short_votes,
        technical_neutral_votes=neutral_votes,
        technical_confluence_pct=participation,
        technical_participation_pct=participation,
        directional_agreement_pct=directional_agreement,
        directional_votes=directional_votes,
        breadth_minimum=breadth_minimum,
        breadth_sufficient=breadth_sufficient,
        minimum_confluence_pct=policy.minimum_confluence_pct,
        trade_geometry=geometry,
    )
