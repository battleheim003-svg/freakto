"""Volume and liquidity-quality diagnostics."""

from __future__ import annotations

import pandas as pd


def analyse_volume(frame: pd.DataFrame) -> dict[str, float | str]:
    close = pd.to_numeric(frame["close"], errors="coerce")
    volume = pd.to_numeric(frame.get("volume", 0), errors="coerce").fillna(0)
    mean = volume.rolling(20).mean().replace(0, 1e-12)
    std = volume.rolling(20).std().replace(0, 1e-12)
    relative = float((volume / mean).iloc[-1]) if float(volume.iloc[-1]) > 0 else 0.0
    zscore = float(((volume - mean) / std).iloc[-1]) if float(volume.iloc[-1]) > 0 else 0.0
    typical = (pd.to_numeric(frame["high"]) + pd.to_numeric(frame["low"]) + close) / 3
    rolling_volume = volume.rolling(20).sum().replace(0, 1e-12)
    vwap = (typical * volume).rolling(20).sum() / rolling_volume
    vwap_distance = float((close.iloc[-1] - vwap.iloc[-1]) / close.iloc[-1]) if pd.notna(vwap.iloc[-1]) else 0.0
    quality = "CONFIRMED" if relative >= 1.2 else "NORMAL" if relative >= 0.65 else "THIN"
    return {"relative_volume": relative, "volume_zscore": zscore, "vwap_distance": vwap_distance, "quality": quality}
