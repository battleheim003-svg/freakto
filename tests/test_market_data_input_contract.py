from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from freakto.market_data import OHLCV_COLUMNS, inspect_ohlcv


def _valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                ["2024-01-01T00:00:00Z", "2024-01-01T04:00:00Z"]
            ),
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [10.0, 11.0],
        }
    )


def test_contract_columns_match_legacy_replay_boundary():
    assert OHLCV_COLUMNS == ("timestamp", "open", "high", "low", "close", "volume")


def test_valid_closed_utc_frame_passes_without_mutation():
    frame = _valid_frame()
    original = frame.copy(deep=True)
    report = inspect_ohlcv(
        frame,
        "4h",
        now=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    assert report.ok
    assert report.valid_rows == 2
    assert report.issues == ()
    pd.testing.assert_frame_equal(frame, original)


def test_invalid_geometry_duplicates_and_incomplete_bar_fail_closed():
    frame = _valid_frame()
    frame.loc[1, "timestamp"] = frame.loc[0, "timestamp"]
    frame.loc[0, "high"] = 98.0
    report = inspect_ohlcv(
        frame,
        "4h",
        now=datetime(2024, 1, 1, 1, tzinfo=timezone.utc),
    )
    codes = {issue.code for issue in report.issues}
    assert report.status == "FAILED"
    assert "DUPLICATE_TIMESTAMP" in codes
    assert "INVALID_OHLC_GEOMETRY" in codes
    assert "INCOMPLETE_CANDLE" in codes


def test_zero_volume_warns_but_does_not_silently_fail():
    frame = _valid_frame()
    frame["volume"] = 0.0
    report = inspect_ohlcv(
        frame,
        "4h",
        now=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    assert report.ok
    assert [(issue.code, issue.severity) for issue in report.issues] == [
        ("ZERO_VOLUME", "WARNING")
    ]


def test_missing_required_column_is_blocked():
    report = inspect_ohlcv(_valid_frame().drop(columns=["volume"]), "4h")
    assert not report.ok
    assert report.issues[0].code == "MISSING_COLUMNS"


def test_infinite_numeric_value_is_blocked():
    frame = _valid_frame()
    frame.loc[0, "close"] = float("inf")
    report = inspect_ohlcv(
        frame,
        "4h",
        now=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    assert not report.ok
    assert "INVALID_NUMERIC_VALUE" in {issue.code for issue in report.issues}
