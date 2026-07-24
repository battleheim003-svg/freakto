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
COMMISSION_BPS_PER_SIDE = {
    "EUR/USD": 0.35,
    "GBP/USD": 0.35,
    "USD/JPY": 0.35,
    "XAU/USD": 0.525,
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
        placeholder_dates: set[pd.Timestamp] = set()
        spread_samples: list[pd.Series] = []
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
            placeholder_dates.update(
                pd.to_datetime(part.loc[placeholders, "timestamp"], utc=True).tolist()
            )
            mid_close = (merged["close_bid"] + merged["close_ask"]) / 2.0
            spread_samples.append(
                ((merged["close_ask"] - merged["close_bid"]) / mid_close * 10_000.0)
                .loc[~placeholders]
                .astype(float)
            )
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
        expected = pd.date_range(
            start=pd.Timestamp(start_utc).normalize(),
            end=(pd.Timestamp(end_utc) - pd.Timedelta(nanoseconds=1)).normalize(),
            freq="1D",
            tz="UTC",
        )
        observed = set(pd.to_datetime(frame["timestamp"], utc=True).dt.normalize())
        placeholders_in_range = {
            value.normalize()
            for value in placeholder_dates
            if pd.Timestamp(start_utc) <= value < pd.Timestamp(end_utc)
        }
        unexplained = sorted(set(expected) - observed - placeholders_in_range)
        frame.attrs["session_audit_status"] = (
            "PASSED" if not unexplained and alignment_drops == 0 else "FAILED"
        )
        frame.attrs["session_expected_days"] = len(expected)
        frame.attrs["session_placeholder_days"] = len(placeholders_in_range)
        frame.attrs["session_unexplained_gap_count"] = len(unexplained)
        frame.attrs["session_unexplained_gap_dates"] = tuple(
            value.isoformat() for value in unexplained
        )
        spreads = (
            pd.concat(spread_samples, ignore_index=True)
            if spread_samples
            else pd.Series(dtype=float)
        )
        spreads = spreads[
            spreads.notna()
            & spreads.ge(0)
            & spreads.replace([float("inf"), float("-inf")], pd.NA).notna()
        ]
        canonical_symbol = str(symbol).strip().upper()
        frame.attrs["spread_observations"] = len(spreads)
        frame.attrs["spread_close_bps_median"] = (
            float(spreads.median()) if len(spreads) else None
        )
        frame.attrs["spread_close_bps_p95"] = (
            float(spreads.quantile(0.95)) if len(spreads) else None
        )
        frame.attrs["spread_close_bps_max"] = (
            float(spreads.max()) if len(spreads) else None
        )
        frame.attrs["commission_bps_per_side"] = COMMISSION_BPS_PER_SIDE[
            canonical_symbol
        ]
        frame.attrs["cost_audit_status"] = (
            "AUDITED_EXCLUDING_ROLLOVER" if len(spreads) else "FAILED"
        )
        frame.attrs["suggested_slippage_bps_per_side"] = (
            float(spreads.quantile(0.95) * 0.625) if len(spreads) else None
        )
        report = inspect_ohlcv(frame, "1d", now=now, require_closed=True)
        return frame, report


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
