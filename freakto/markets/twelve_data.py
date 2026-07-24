"""Twelve Data OHLCV adapter for research-only forex and commodity datasets."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping, Sequence

import pandas as pd
import requests

from freakto.market_data import ContractReport, inspect_ohlcv

API_URL = "https://api.twelvedata.com/time_series"
TIMEFRAME_MAP = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1day",
    "1w": "1week",
}


class TwelveDataError(RuntimeError):
    """Provider response could not safely cross the adapter boundary."""


class TwelveDataAdapter:
    name = "twelve_data"

    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 30.0,
        get: Callable[..., Any] = requests.get,
    ):
        if not str(api_key).strip():
            raise ValueError("A Twelve Data API key is required.")
        self._api_key = str(api_key).strip()
        self._timeout = float(timeout)
        self._get = get

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        *,
        since_ms: int | None = None,
        limit: int | None = None,
    ) -> Sequence[Mapping[str, Any]]:
        interval = TIMEFRAME_MAP.get(str(timeframe).strip().lower())
        if interval is None:
            raise ValueError(f"Unsupported Twelve Data timeframe: {timeframe}")
        canonical_symbol = str(symbol).strip().upper()
        if "/" not in canonical_symbol:
            raise ValueError("Twelve Data adapter requires canonical BASE/QUOTE symbols.")

        params: dict[str, Any] = {
            "symbol": canonical_symbol,
            "interval": interval,
            "timezone": "UTC",
            "order": "ASC",
            "format": "JSON",
            "apikey": self._api_key,
        }
        if since_ms is not None:
            params["start_date"] = datetime.fromtimestamp(
                int(since_ms) / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S")
        if limit is not None:
            if int(limit) < 1 or int(limit) > 5000:
                raise ValueError("Twelve Data outputsize must be between 1 and 5000.")
            params["outputsize"] = int(limit)

        response = self._get(API_URL, params=params, timeout=self._timeout)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise TwelveDataError("Provider returned a non-object JSON response.")
        if payload.get("status") == "error" or "values" not in payload:
            code = payload.get("code", "unknown")
            message = payload.get("message", "missing time-series values")
            raise TwelveDataError(f"Twelve Data error {code}: {message}")

        values = payload.get("values")
        if not isinstance(values, list):
            raise TwelveDataError("Provider values must be a list.")
        rows: list[dict[str, Any]] = []
        for value in values:
            if not isinstance(value, dict):
                raise TwelveDataError("Provider returned a malformed time-series row.")
            rows.append(
                {
                    "timestamp": value.get("datetime"),
                    "open": value.get("open"),
                    "high": value.get("high"),
                    "low": value.get("low"),
                    "close": value.get("close"),
                    # Missing volume remains missing and must fail validation.
                    "volume": value.get("volume"),
                    "provider": self.name,
                }
            )
        return rows

    def fetch_validated(
        self,
        symbol: str,
        timeframe: str,
        *,
        since_ms: int | None = None,
        limit: int | None = None,
        now: datetime | None = None,
    ) -> tuple[pd.DataFrame, ContractReport]:
        rows = self.fetch_ohlcv(
            symbol,
            timeframe,
            since_ms=since_ms,
            limit=limit,
        )
        frame = pd.DataFrame.from_records(rows)
        if not frame.empty:
            frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
            for column in ("open", "high", "low", "close", "volume"):
                frame[column] = pd.to_numeric(frame[column], errors="coerce")
        report = inspect_ohlcv(frame, timeframe, now=now, require_closed=True)
        return frame, report
