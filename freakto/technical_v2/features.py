"""Causal continuous technical features grouped into non-overlapping families."""

from __future__ import annotations

import math

import pandas as pd

from freakto.technical_v2.contracts import SignalEvidence


REQUIRED_COLUMNS = {"open", "high", "low", "close"}


def validate_frame(frame: pd.DataFrame, *, minimum_rows: int = 40) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"OHLCV is missing required columns: {sorted(missing)}")
    clean = frame.copy()
    for column in ("open", "high", "low", "close", "volume"):
        if column not in clean:
            clean[column] = 0.0
        clean[column] = pd.to_numeric(clean[column], errors="coerce")
    clean = clean.dropna(subset=list(REQUIRED_COLUMNS)).reset_index(drop=True)
    if len(clean) < minimum_rows:
        raise ValueError(f"At least {minimum_rows} closed candles are required")
    if (clean["high"] < clean["low"]).any() or (clean["close"] <= 0).any():
        raise ValueError("OHLCV contains invalid price geometry")
    return clean


def clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    if not math.isfinite(float(value)):
        return 0.0
    return max(lower, min(upper, float(value)))


def _safe_last(series: pd.Series, default: float = 0.0) -> float:
    value = series.iloc[-1]
    return float(value) if pd.notna(value) and math.isfinite(float(value)) else default


def atr_series(frame: pd.DataFrame, period: int = 14) -> pd.Series:
    close, high, low = frame["close"], frame["high"], frame["low"]
    true_range = pd.concat(
        [(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()


def extract_evidence(frame: pd.DataFrame, *, timeframe: str = "base", depth: int = 100) -> tuple[SignalEvidence, ...]:
    data = validate_frame(frame)
    close, high, low, opened, volume = (
        data["close"], data["high"], data["low"], data["open"], data["volume"]
    )
    atr = atr_series(data).replace(0, 1e-12)
    atr_last = max(_safe_last(atr), float(close.iloc[-1]) * 1e-8)
    ema8 = close.ewm(span=8, adjust=False).mean()
    ema21 = close.ewm(span=21, adjust=False).mean()
    ema55 = close.ewm(span=55, adjust=False).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean().replace(0, 1e-12)
    rsi = 100 - 100 / (1 + gain / loss)
    macd = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    middle = close.rolling(20).mean()
    deviation = close.rolling(20).std().replace(0, 1e-12)
    previous_high = high.shift(1).rolling(20).max()
    previous_low = low.shift(1).rolling(20).min()
    rel_volume = volume / volume.rolling(20).mean().replace(0, 1e-12)
    signed_volume = volume.where(delta >= 0, -volume)
    obv = signed_volume.fillna(0).cumsum()
    body = (close - opened) / (high - low).replace(0, 1e-12)

    values = [
        SignalEvidence("EMA_8_21", "trend", _safe_last(ema8 - ema21), clamp(_safe_last(ema8 - ema21) / atr_last), abs(clamp(_safe_last(ema8 - ema21) / atr_last)), timeframe),
        SignalEvidence("EMA_21_55", "trend", _safe_last(ema21 - ema55), clamp(_safe_last(ema21 - ema55) / (2 * atr_last)), abs(clamp(_safe_last(ema21 - ema55) / (2 * atr_last))), timeframe),
        SignalEvidence("RSI_14", "momentum", _safe_last(rsi, 50), clamp((_safe_last(rsi, 50) - 50) / 25), abs(clamp((_safe_last(rsi, 50) - 50) / 25)), timeframe),
        SignalEvidence("MACD_IMPULSE", "momentum", _safe_last(macd - macd_signal), clamp(_safe_last(macd - macd_signal) / atr_last), abs(clamp(_safe_last(macd - macd_signal) / atr_last)), timeframe),
        SignalEvidence("BOLLINGER_Z", "mean_reversion", _safe_last((close - middle) / deviation), clamp(-_safe_last((close - middle) / deviation) / 2.5), abs(clamp(_safe_last((close - middle) / deviation) / 2.5)), timeframe, "Contrarian at statistical extremes"),
        SignalEvidence("BREAKOUT_20", "structure", float(close.iloc[-1]), 1.0 if close.iloc[-1] > previous_high.iloc[-1] else -1.0 if close.iloc[-1] < previous_low.iloc[-1] else 0.0, 1.0 if close.iloc[-1] > previous_high.iloc[-1] or close.iloc[-1] < previous_low.iloc[-1] else 0.0, timeframe),
        SignalEvidence("CANDLE_BODY", "structure", _safe_last(body), clamp(_safe_last(body)), abs(clamp(_safe_last(body))), timeframe),
        SignalEvidence("RELATIVE_VOLUME", "volume", _safe_last(rel_volume, 1), clamp(_safe_last(delta) / atr_last) if _safe_last(rel_volume, 1) >= 1 else 0.0, clamp((_safe_last(rel_volume, 1) - 1) / 1.5, 0, 1), timeframe),
        SignalEvidence("OBV_SLOPE", "volume", _safe_last(obv.diff(5)), clamp(_safe_last(obv.diff(5)) / max(float(volume.tail(20).mean()) * 5, 1e-12)), abs(clamp(_safe_last(obv.diff(5)) / max(float(volume.tail(20).mean()) * 5, 1e-12))), timeframe),
        SignalEvidence("ATR_EXPANSION", "volatility", _safe_last(atr / atr.rolling(30).median().replace(0, 1e-12), 1), clamp(_safe_last(delta.rolling(3).sum()) / (3 * atr_last)), clamp(abs(_safe_last(atr / atr.rolling(30).median().replace(0, 1e-12), 1) - 1), 0, 1), timeframe),
    ]
    count = max(4, min(len(values), 4 + round(max(0, min(100, depth)) / 100 * (len(values) - 4))))
    return tuple(values[:count])
