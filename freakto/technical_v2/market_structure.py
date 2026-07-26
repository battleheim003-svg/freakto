"""Causal market-structure and liquidity-event detection."""

from __future__ import annotations

import pandas as pd


def analyse_market_structure(frame: pd.DataFrame, lookback: int = 20) -> dict[str, object]:
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    close = pd.to_numeric(frame["close"], errors="coerce")
    prior_high = float(high.shift(1).rolling(lookback).max().iloc[-1])
    prior_low = float(low.shift(1).rolling(lookback).min().iloc[-1])
    last_high, last_low, last_close = float(high.iloc[-1]), float(low.iloc[-1]), float(close.iloc[-1])
    bullish_break = last_close > prior_high
    bearish_break = last_close < prior_low
    sweep_high = last_high > prior_high and last_close <= prior_high
    sweep_low = last_low < prior_low and last_close >= prior_low
    recent_mid = (float(high.tail(lookback).max()) + float(low.tail(lookback).min())) / 2
    direction = 1.0 if bullish_break or sweep_low else -1.0 if bearish_break or sweep_high else (0.25 if last_close > recent_mid else -0.25)
    prior_move = float(close.iloc[-2] - close.iloc[max(0, len(close) - lookback)])
    event = (
        "BULLISH_CHOCH" if bullish_break and prior_move < 0
        else "BEARISH_CHOCH" if bearish_break and prior_move > 0
        else "BULLISH_BOS" if bullish_break
        else "BEARISH_BOS" if bearish_break
        else "HIGH_SWEEP" if sweep_high
        else "LOW_SWEEP" if sweep_low
        else "RANGE_STRUCTURE"
    )
    return {
        "event": event,
        "direction": direction,
        "support": prior_low,
        "resistance": prior_high,
        "liquidity_sweep": bool(sweep_high or sweep_low),
    }
