"""Credential-free Dukascopy daily candle adapter for research datasets."""

from __future__ import annotations

import lzma
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import requests

from freakto.market_data import ContractReport, inspect_ohlcv

BASE_URL = "https://datafeed.dukascopy.com/datafeed"
RECORD = struct.Struct(">5if")
POINT_VALUE = {
    "EUR/USD": 100_000.0,
    "GBP/USD": 100_000.0,
    "USD/JPY": 1_000.0,
    "XAU/USD": 1_000.0,
}


class DukascopyError(RuntimeError):
    """Public historical data could not safely cross the adapter boundary."""


class DukascopyAdapter:
    name = "dukascopy"

    def __init__(
        self,
        *,
        timeout: float = 60.0,
        get: Callable[..., Any] = requests.get,
        cache_dir: str | Path | None = None,
    ):
        self._timeout = float(timeout)
        self._get = get
        self._cache_dir = Path(cache_dir) if cache_dir is not None else None

    @staticmethod
    def _instrument(symbol: str) -> tuple[str, float]:
        canonical = str(symbol).strip().upper()
        divisor = POINT_VALUE.get(canonical)
        if divisor is None:
            raise ValueError(f"Unsupported Dukascopy symbol: {canonical}")
        return canonical.replace("/", ""), divisor

    def _year_side(self, symbol: str, year: int, side: str) -> pd.DataFrame:
        instrument, divisor = self._instrument(symbol)
        price_side = str(side).strip().upper()
        if price_side not in {"BID", "ASK"}:
            raise ValueError("Dukascopy price side must be BID or ASK.")
        url = (
            f"{BASE_URL}/{instrument}/{int(year)}/"
            f"{price_side}_candles_day_1.bi5"
        )
        cache_path = (
            self._cache_dir / instrument / f"{int(year)}_{price_side}.bi5"
            if self._cache_dir is not None
            else None
        )
        if cache_path is not None and cache_path.is_file():
            compressed = cache_path.read_bytes()
        else:
            response = self._get(url, timeout=self._timeout)
            if int(response.status_code) == 404:
                return pd.DataFrame()
            response.raise_for_status()
            compressed = bytes(response.content)
            if cache_path is not None and compressed:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_bytes(compressed)
        if not compressed:
            return pd.DataFrame()
        try:
            raw = lzma.decompress(compressed)
        except lzma.LZMAError as exc:
            raise DukascopyError(f"Invalid LZMA payload for {symbol} {year} {side}.") from exc
        if len(raw) % RECORD.size:
            raise DukascopyError(
                f"Invalid Dukascopy record length for {symbol} {year} {side}."
            )

        origin = pd.Timestamp(year=int(year), month=1, day=1, tz="UTC")
        rows: list[dict[str, Any]] = []
        for time_delta, open_, close, low, high, volume in RECORD.iter_unpack(raw):
            rows.append(
                {
                    "timestamp": origin + pd.to_timedelta(int(time_delta), unit="s"),
                    "open": float(open_) / divisor,
                    "high": float(high) / divisor,
                    "low": float(low) / divisor,
                    "close": float(close) / divisor,
                    "volume": float(volume),
                }
            )
        return pd.DataFrame.from_records(rows)

    def fetch_range(
        self,
        symbol: str,
        timeframe: str,
        *,
        start: datetime,
        end: datetime,
        now: datetime | None = None,
    ) -> tuple[pd.DataFrame, ContractReport]:
        if str(timeframe).strip().lower() != "1d":
            raise ValueError("Credential-free Dukascopy adapter currently supports 1d.")
        start_utc = _utc(start)
        end_utc = _utc(end)
        if start_utc >= end_utc:
            raise ValueError("Historical start must be earlier than end.")

        parts: list[pd.DataFrame] = []
        alignment_drops = 0
        placeholder_rows_removed = 0
        last_included = pd.Timestamp(end_utc) - pd.Timedelta(nanoseconds=1)
        for year in range(start_utc.year, int(last_included.year) + 1):
            bid = self._year_side(symbol, year, "BID")
            ask = self._year_side(symbol, year, "ASK")
            if bid.empty or ask.empty:
                continue
            merged = bid.merge(
                ask,
                on="timestamp",
                suffixes=("_bid", "_ask"),
                how="inner",
                validate="one_to_one",
            )
            alignment_drops += len(bid) + len(ask) - (2 * len(merged))
            part = pd.DataFrame({"timestamp": merged["timestamp"]})
            for column in ("open", "high", "low", "close"):
                part[column] = (
                    merged[f"{column}_bid"] + merged[f"{column}_ask"]
                ) / 2.0
            part["volume"] = merged["volume_bid"] + merged["volume_ask"]
            placeholders = part["volume"].le(0)
            placeholder_rows_removed += int(placeholders.sum())
            parts.append(part.loc[~placeholders].copy())

        if parts:
            frame = pd.concat(parts, ignore_index=True)
            mask = (
                frame["timestamp"].ge(pd.Timestamp(start_utc))
                & frame["timestamp"].lt(pd.Timestamp(end_utc))
            )
            frame = (
                frame.loc[mask]
                .sort_values("timestamp")
                .drop_duplicates("timestamp", keep="last")
                .reset_index(drop=True)
            )
            frame["provider"] = self.name
        else:
            frame = pd.DataFrame(
                columns=["timestamp", "open", "high", "low", "close", "volume", "provider"]
            )
        frame.attrs["price_basis"] = "mid"
        frame.attrs["volume_semantics"] = "best_bid_plus_best_ask_quote_volume"
        frame.attrs["placeholder_rows_removed"] = placeholder_rows_removed
        frame.attrs["bid_ask_alignment_drops"] = alignment_drops
        report = inspect_ohlcv(frame, "1d", now=now, require_closed=True)
        return frame, report


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
