from __future__ import annotations

from datetime import datetime, timezone
import subprocess

import ccxt

import data_fetcher
from data_fetcher import FetchStatus
from freakto.paper.cycle_contract import (
    NETWORK_EXHAUSTED_EXIT_CODE,
    STEP_NETWORK_SKIPPED,
)
from freakto.paper.orchestrator import run_step


class Exchange:
    def __init__(self, outcome):
        self.outcome = outcome

    def fetch_ohlcv(self, **_kwargs):
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def _candles():
    start = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    return [
        [start + index * 14_400_000, 100, 102, 99, 101, 1000]
        for index in range(3)
    ]


def test_provider_network_failure_then_fallback_success():
    exchanges = {
        "first": Exchange(ccxt.NetworkError("offline")),
        "second": Exchange(_candles()),
    }

    result = data_fetcher.fetch_ohlcv_result(
        exchange_order=("first", "second"),
        exchange_factory=exchanges.__getitem__,
    )

    assert result.status is FetchStatus.SUCCESS
    assert result.frame.attrs["provider"] == "second"
    assert [attempt.status for attempt in result.attempts] == [
        "NETWORK_ERROR",
        "SUCCESS",
    ]


def test_all_provider_network_failures_are_typed():
    errors = {
        "timeout": Exchange(ccxt.RequestTimeout("timeout")),
        "reset": Exchange(ccxt.NetworkError("connection reset")),
        "rate": Exchange(ccxt.RateLimitExceeded("retry later")),
    }

    result = data_fetcher.fetch_ohlcv_result(
        exchange_order=tuple(errors),
        exchange_factory=errors.__getitem__,
    )

    assert result.status is FetchStatus.NETWORK_EXHAUSTED
    assert result.frame.empty
    assert {attempt.status for attempt in result.attempts} == {"NETWORK_ERROR"}


def test_bad_symbol_is_not_misclassified_as_network():
    result = data_fetcher.fetch_ohlcv_result(
        exchange_order=("bad",),
        exchange_factory=lambda _name: Exchange(ccxt.BadSymbol("bad symbol")),
    )

    assert result.status is FetchStatus.CONFIGURATION_ERROR


def test_empty_valid_response_is_not_network_failure():
    result = data_fetcher.fetch_ohlcv_result(
        exchange_order=("empty",),
        exchange_factory=lambda _name: Exchange([]),
    )

    assert result.status is FetchStatus.EMPTY_RESPONSE


def test_no_closed_candle_is_distinct_from_network(monkeypatch):
    monkeypatch.setattr(
        data_fetcher,
        "keep_closed_candles_only",
        lambda frame, _timeframe: (frame.iloc[0:0], len(frame)),
    )

    result = data_fetcher.fetch_ohlcv_result(
        exchange_order=("open",),
        exchange_factory=lambda _name: Exchange(_candles()),
    )

    assert result.status is FetchStatus.NO_CLOSED_CANDLE


def test_error_logging_redacts_query_credentials():
    message = data_fetcher._safe_error(
        ccxt.NetworkError(
            "GET https://example.test/market?api_key=super-secret&signature=signed"
        )
    )

    assert "super-secret" not in message
    assert "signed" not in message
    assert "<redacted>" in message


def test_network_exit_code_maps_to_explicit_step_status(tmp_path):
    def runner(command, *, cwd, timeout_seconds):
        return subprocess.CompletedProcess(
            command,
            NETWORK_EXHAUSTED_EXIT_CODE,
            "",
            "network exhausted",
        )

    class Logger:
        def info(self, *_args, **_kwargs):
            pass

        warning = error = exception = info

    result = run_step(
        "market_monitor",
        ["python", "monitor.py", "--once"],
        cwd=tmp_path,
        timeout_seconds=1,
        retries=0,
        retry_delay_seconds=0,
        logger=Logger(),
        runner=runner,
    )

    assert result.status == STEP_NETWORK_SKIPPED
    assert result.exit_code == NETWORK_EXHAUSTED_EXIT_CODE
