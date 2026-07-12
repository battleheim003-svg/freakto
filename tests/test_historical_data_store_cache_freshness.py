from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from engine.historical_data_store import (
    HistoricalDataRequest,
    build_symbol_history,
    load_history,
    save_history,
)


def _frame(start: datetime, periods: int, *, provider: str = "kucoin") -> pd.DataFrame:
    timestamps = pd.date_range(start, periods=periods, freq="4h", tz="UTC")
    base = pd.Series(range(periods), dtype=float) + 100.0
    return pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": base,
            "high": base + 1.0,
            "low": base - 1.0,
            "close": base + 0.25,
            "volume": 1_000.0,
            "provider": provider,
        }
    )


def _request(data_dir: Path, start: datetime, end: datetime) -> HistoricalDataRequest:
    return HistoricalDataRequest(
        symbols=["BTC/USDT"],
        timeframe="4h",
        start_utc=start.isoformat(),
        end_utc=end.isoformat(),
        exchange="kucoin",
        min_acceptable_coverage_pct=90.0,
        data_dir=str(data_dir),
        update_existing=True,
        force_refresh=False,
    )


def test_high_coverage_but_stale_cache_is_refreshed_incrementally(tmp_path: Path) -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    periods = 1_000
    end = start + timedelta(hours=4 * (periods - 1))

    # Six missing tail candles still leave >99% coverage, which previously
    # caused the stale cache to be reused without any network fetch.
    cached = _frame(start, periods - 6)
    save_history(cached, "BTC/USDT", "4h", tmp_path)

    full = _frame(start, periods)
    observed_starts = []

    def fake_fetch(**kwargs):
        observed_starts.append(kwargs["start"])
        fetch_start = pd.Timestamp(kwargs["start"])
        return full.loc[full["timestamp"] >= fetch_start].reset_index(drop=True)

    with (
        patch("engine.historical_data_store.fetch_exchange_history", side_effect=fake_fetch) as mocked_fetch,
        patch("engine.historical_data_store._write_quality"),
    ):
        result = build_symbol_history(_request(tmp_path, start, end), "BTC/USDT")

    assert mocked_fetch.call_count == 1
    assert result.ok is True
    assert result.used_cache is False
    assert result.rows == periods
    assert pd.Timestamp(result.quality.actual_end_utc) == pd.Timestamp(end)

    # The updater should request only the cached tail with one overlap candle,
    # not download the entire three-year dataset again.
    expected_incremental_start = cached["timestamp"].max().to_pydatetime() - timedelta(hours=4)
    assert observed_starts == [expected_incremental_start]
    assert len(load_history("BTC/USDT", "4h", tmp_path)) == periods


def test_cache_with_at_most_one_candle_lag_is_reused(tmp_path: Path) -> None:
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    periods = 1_000
    requested_end = start + timedelta(hours=4 * (periods - 1))

    # One-candle lag is expected when the current exchange candle is not closed.
    cached = _frame(start, periods - 1)
    save_history(cached, "BTC/USDT", "4h", tmp_path)

    with (
        patch("engine.historical_data_store.fetch_exchange_history") as mocked_fetch,
        patch("engine.historical_data_store._write_quality"),
    ):
        result = build_symbol_history(_request(tmp_path, start, requested_end), "BTC/USDT")

    mocked_fetch.assert_not_called()
    assert result.ok is True
    assert result.used_cache is True
    assert result.fetched_rows == 0
    assert result.rows == periods - 1
