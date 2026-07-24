from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from freakto.markets import TwelveDataAdapter, TwelveDataError, persist_replay_dataset
from freakto.markets.compatibility import audit_replay_compatibility
from freakto.markets.forex import config as forex_config
from freakto.markets.gold import config as gold_config


class Response:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def _payload(*, include_volume=True):
    values = [
        {
            "datetime": "2024-01-01 00:00:00",
            "open": "1.10",
            "high": "1.20",
            "low": "1.00",
            "close": "1.15",
        },
        {
            "datetime": "2024-01-01 04:00:00",
            "open": "1.15",
            "high": "1.25",
            "low": "1.10",
            "close": "1.20",
        },
    ]
    if include_volume:
        for value in values:
            value["volume"] = "100"
    return {"status": "ok", "meta": {"symbol": "EUR/USD"}, "values": values}


def test_configs_are_research_only_and_fail_closed():
    forex = forex_config()
    gold = gold_config()
    assert forex.research_only and not forex.paper_enabled and not forex.live_enabled
    assert gold.research_only and not gold.paper_enabled and not gold.live_enabled
    assert forex.cost_model_status == gold.cost_model_status == "UNVERIFIED"


def test_twelve_data_adapter_maps_and_validates_closed_candles():
    captured = {}

    def get(url, **kwargs):
        captured.update(kwargs)
        return Response(_payload())

    adapter = TwelveDataAdapter("secret", get=get)
    frame, report = adapter.fetch_validated(
        "EUR/USD",
        "4h",
        limit=2,
        now=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    assert report.ok
    assert frame["timestamp"].dt.tz is not None
    assert captured["params"]["timezone"] == "UTC"
    assert captured["params"]["interval"] == "4h"
    assert captured["params"]["apikey"] == "secret"


def test_range_fetch_uses_explicit_provider_boundaries_without_outputsize():
    captured = {}

    def get(url, **kwargs):
        captured.update(kwargs)
        return Response(_payload())

    adapter = TwelveDataAdapter("secret", get=get)
    _, report = adapter.fetch_range(
        "EUR/USD",
        "4h",
        start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        end=datetime(2024, 1, 2, tzinfo=timezone.utc),
        now=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    assert report.ok
    assert captured["params"]["start_date"] == "2024-01-01T00:00:00"
    assert captured["params"]["end_date"] == "2024-01-02T00:00:00"
    assert "outputsize" not in captured["params"]


def test_missing_provider_volume_is_blocked_not_fabricated():
    adapter = TwelveDataAdapter("secret", get=lambda *a, **k: Response(_payload(include_volume=False)))
    frame, report = adapter.fetch_validated(
        "EUR/USD",
        "4h",
        now=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    assert frame["volume"].isna().all()
    assert not report.ok
    assert "INVALID_NUMERIC_VALUE" in {issue.code for issue in report.issues}


def test_provider_error_is_explicit():
    adapter = TwelveDataAdapter(
        "secret",
        get=lambda *a, **k: Response({"status": "error", "code": 401, "message": "bad key"}),
    )
    with pytest.raises(TwelveDataError, match="bad key"):
        adapter.fetch_ohlcv("EUR/USD", "4h")


def test_valid_dataset_is_persisted_in_replay_layout_without_overwrite(tmp_path):
    frame = pd.DataFrame(_payload()["values"]).rename(columns={"datetime": "timestamp"})
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column])
    frame["provider"] = "twelve_data"
    data_path, manifest_path, manifest = persist_replay_dataset(
        frame,
        symbol="EUR/USD",
        timeframe="4h",
        config=forex_config(),
        data_dir=tmp_path,
        now=datetime(2024, 1, 2, tzinfo=timezone.utc),
    )
    assert data_path == tmp_path / "4h" / "EUR_USD.csv.gz"
    assert manifest_path.exists()
    assert manifest.asset_class == "forex"
    with pytest.raises(FileExistsError):
        persist_replay_dataset(
            frame,
            symbol="EUR/USD",
            timeframe="4h",
            config=forex_config(),
            data_dir=tmp_path,
            now=datetime(2024, 1, 2, tzinfo=timezone.utc),
        )


def test_compatibility_stays_research_only_until_session_and_cost_audits_pass():
    frame = pd.DataFrame(_payload()["values"]).rename(columns={"datetime": "timestamp"})
    report = audit_replay_compatibility(
        frame,
        timeframe="4h",
        config=forex_config(),
        min_rows=2,
    )
    assert report.schema_ready
    assert report.status == "RESEARCH_DATA_ONLY"
    assert not report.evidence_replay_ready
    assert "EXECUTION_COST_MODEL_UNVERIFIED" in report.blockers
    assert "SESSION_CALENDAR_UNVERIFIED" in report.blockers
