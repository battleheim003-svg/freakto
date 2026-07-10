"""Optional live feature enrichment for market decisions.

The enrichment layer is deliberately opt-in because it adds network calls. When
disabled or unavailable it returns neutral feature values, so the decision
engine remains deterministic and fast.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd
import requests

from config import (
    CROSS_EXCHANGE_VOLUME_LIMIT,
    ENABLE_CROSS_EXCHANGE_VOLUME,
    ENABLE_NEWS_SENTIMENT,
    ENABLE_ONCHAIN_FEATURES,
    GLASSNODE_API_KEY,
)
from data_fetcher import EXCHANGE_ORDER, _create_exchange, _normalize_symbol_for_exchange, _to_dataframe


DEFAULT_COLUMNS = {
    "cross_exchange_volume": 0.0,
    "cross_exchange_volume_ratio": 1.0,
    "cross_exchange_provider_count": 0,
    "news_sentiment_score": 0.0,
    "onchain_active_addresses": 0.0,
    "onchain_signal_score": 0.0,
}


def _with_defaults(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    for column, value in DEFAULT_COLUMNS.items():
        if column not in enriched.columns:
            enriched[column] = value
    return enriched


def _normalize_timestamp_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "timestamp" not in out.columns:
        out = out.reset_index().rename(columns={"index": "timestamp"})
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce").dt.tz_localize(None)
    return out.dropna(subset=["timestamp"])


def fetch_cross_exchange_volume_frame(symbol: str, timeframe: str, limit: int | None = None) -> pd.DataFrame:
    limit = int(limit or CROSS_EXCHANGE_VOLUME_LIMIT)
    frames = []

    for exchange_name in EXCHANGE_ORDER:
        try:
            exchange = _create_exchange(exchange_name)
            exchange_symbol = _normalize_symbol_for_exchange(symbol, exchange_name)
            candles = exchange.fetch_ohlcv(exchange_symbol, timeframe=timeframe, limit=limit)
            if not candles:
                continue
            frame = _to_dataframe(candles, provider=exchange_name)
            frame = _normalize_timestamp_column(frame)[["timestamp", "volume"]]
            frame = frame.rename(columns={"volume": f"volume_{exchange_name}"})
            frames.append(frame)
        except Exception:
            continue

    if not frames:
        return pd.DataFrame()

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on="timestamp", how="outer")
    volume_cols = [col for col in merged.columns if col.startswith("volume_")]
    merged[volume_cols] = merged[volume_cols].apply(pd.to_numeric, errors="coerce")
    merged["cross_exchange_volume"] = merged[volume_cols].sum(axis=1, skipna=True)
    merged["cross_exchange_provider_count"] = merged[volume_cols].notna().sum(axis=1)
    merged = merged.sort_values("timestamp")
    rolling = merged["cross_exchange_volume"].rolling(20, min_periods=3).mean()
    merged["cross_exchange_volume_ratio"] = (
        merged["cross_exchange_volume"] / rolling.replace(0, pd.NA)
    ).fillna(1.0)
    return merged[[
        "timestamp",
        "cross_exchange_volume",
        "cross_exchange_volume_ratio",
        "cross_exchange_provider_count",
    ]]


@lru_cache(maxsize=8)
def _cached_sentiment() -> dict[str, Any]:
    try:
        from news_sentiment import get_current_sentiment

        return get_current_sentiment()
    except Exception as exc:
        return {"score": 0.0, "summary": f"sentiment_unavailable: {type(exc).__name__}"}


@lru_cache(maxsize=16)
def _cached_onchain(symbol: str) -> dict[str, Any]:
    if not GLASSNODE_API_KEY:
        return {"active_addresses": 0.0, "signal_score": 0.0, "status": "missing_glassnode_key"}

    asset = symbol.split("/")[0].upper()
    if asset not in {"BTC", "ETH"}:
        return {"active_addresses": 0.0, "signal_score": 0.0, "status": "unsupported_asset"}

    try:
        response = requests.get(
            "https://api.glassnode.com/v1/metrics/addresses/active_count",
            params={"a": asset, "api_key": GLASSNODE_API_KEY, "i": "24h"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload:
            return {"active_addresses": 0.0, "signal_score": 0.0, "status": "empty"}
        values = [float(item.get("v", 0.0) or 0.0) for item in payload[-30:]]
        latest = values[-1] if values else 0.0
        avg = sum(values) / len(values) if values else 0.0
        signal = ((latest / avg) - 1.0) if avg else 0.0
        return {
            "active_addresses": latest,
            "signal_score": max(-1.0, min(1.0, signal)),
            "status": "ok",
        }
    except Exception as exc:
        return {"active_addresses": 0.0, "signal_score": 0.0, "status": type(exc).__name__}


def add_live_enrichment_features(df: pd.DataFrame, *, symbol: str, timeframe: str) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    enriched = _with_defaults(df)
    notes: list[str] = []

    if ENABLE_CROSS_EXCHANGE_VOLUME:
        cross = fetch_cross_exchange_volume_frame(symbol, timeframe)
        if not cross.empty:
            base = _normalize_timestamp_column(enriched)
            base = base.merge(cross, on="timestamp", how="left", suffixes=("", "_external"))
            for column in [
                "cross_exchange_volume",
                "cross_exchange_volume_ratio",
                "cross_exchange_provider_count",
            ]:
                ext = f"{column}_external"
                if ext in base.columns:
                    base[column] = base[ext].combine_first(base[column])
                    base = base.drop(columns=[ext])
            enriched = base
            notes.append("cross_exchange_volume")

    if ENABLE_NEWS_SENTIMENT:
        sentiment = _cached_sentiment()
        enriched.loc[enriched.index[-1], "news_sentiment_score"] = float(sentiment.get("score", 0.0) or 0.0)
        enriched.loc[enriched.index[-1], "news_sentiment_summary"] = str(sentiment.get("summary", ""))
        notes.append("news_sentiment")

    if ENABLE_ONCHAIN_FEATURES:
        onchain = _cached_onchain(symbol)
        enriched.loc[enriched.index[-1], "onchain_active_addresses"] = float(onchain.get("active_addresses", 0.0) or 0.0)
        enriched.loc[enriched.index[-1], "onchain_signal_score"] = float(onchain.get("signal_score", 0.0) or 0.0)
        enriched.loc[enriched.index[-1], "onchain_status"] = str(onchain.get("status", ""))
        notes.append("onchain")

    enriched.attrs.update(getattr(df, "attrs", {}) or {})
    enriched.attrs["enrichment_notes"] = notes
    return enriched
