import csv
import json
import sys
from types import SimpleNamespace

import pytest

from engine.live_demo import CcxtPublicMarketData, MarketSnapshot, MockBroker, run_live_loop


class FakeMarketData:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def fetch_snapshot(self, _symbol):
        return self.snapshot


def snapshot():
    return MarketSnapshot("2026-01-01T00:00:00+00:00", "BTC/USDT", 100.0, 99.0, 101.0, 2.0, 3.0)


def broker(tmp_path):
    return MockBroker(
        FakeMarketData(snapshot()),
        initial_balance=10_000,
        fee_bps=10,
        slippage_bps=0,
        state_path=tmp_path / "state.json",
        trade_log_path=tmp_path / "trades.csv",
    )


def test_buy_and_sell_update_cash_position_state_and_append_only_log(tmp_path):
    item = broker(tmp_path)
    buy = item.buy_market("BTC/USDT", 1.0)
    assert buy.execution_price == 101.0
    assert buy.fee_usdt == pytest.approx(0.101)
    assert item.cash_balance == pytest.approx(9898.899)
    assert item.positions["BTC/USDT"].amount == 1.0

    sell = item.sell_market("BTC/USDT", 0.4)
    assert sell.execution_price == 99.0
    assert item.positions["BTC/USDT"].amount == pytest.approx(0.6)
    assert json.loads((tmp_path / "state.json").read_text())["paper_only"] is True
    with (tmp_path / "trades.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["side"] for row in rows] == ["BUY", "SELL"]


def test_broker_rejects_overspending_short_selling_and_invalid_amounts(tmp_path):
    item = broker(tmp_path)
    with pytest.raises(ValueError):
        item.buy_market("BTC/USDT", 1_000)
    with pytest.raises(ValueError):
        item.sell_market("BTC/USDT", 1)
    with pytest.raises(ValueError):
        item.buy_market("BTC/USDT", 0)


def test_state_survives_restart(tmp_path):
    first = broker(tmp_path)
    first.buy_market("BTC/USDT", 1.0)
    second = broker(tmp_path)
    assert second.cash_balance == pytest.approx(first.cash_balance)
    assert second.positions["BTC/USDT"].amount == 1.0


def test_loop_is_hold_by_default_and_once_does_not_trade(tmp_path, capsys):
    item = broker(tmp_path)
    run_live_loop(
        "BTC/USDT",
        item.market_data,
        item,
        lambda _snapshot, _broker: ("HOLD", 0.0),
        once=True,
    )
    assert not (tmp_path / "trades.csv").exists()
    assert "action=HOLD" in capsys.readouterr().out


def test_loop_routes_explicit_buy_decision(tmp_path):
    item = broker(tmp_path)
    run_live_loop(
        "BTC/USDT",
        item.market_data,
        item,
        lambda _snapshot, _broker: ("BUY", 0.5),
        once=True,
    )
    assert item.positions["BTC/USDT"].amount == 0.5


def test_public_data_falls_back_and_reports_provider(monkeypatch):
    class BrokenExchange:
        def __init__(self, _options):
            pass

        def fetch_ticker(self, _symbol):
            raise TimeoutError("blocked endpoint")

    class WorkingExchange:
        def __init__(self, _options):
            pass

        def fetch_ticker(self, _symbol):
            return {"last": 100, "bid": 99, "ask": 101}

        def fetch_order_book(self, _symbol, limit=5):
            assert limit == 5
            return {"bids": [[99, 2]], "asks": [[101, 3]]}

    monkeypatch.setitem(sys.modules, "ccxt", SimpleNamespace(broken=BrokenExchange, working=WorkingExchange))
    source = CcxtPublicMarketData(("broken", "working"), retries=0)
    result = source.fetch_snapshot("BTC/USDT")
    assert result.provider == "working"
    assert result.last == 100


def test_public_data_failure_contains_provider_root_causes(monkeypatch):
    class BrokenExchange:
        def __init__(self, _options):
            pass

        def fetch_ticker(self, _symbol):
            raise TimeoutError("blocked endpoint")

    monkeypatch.setitem(sys.modules, "ccxt", SimpleNamespace(broken=BrokenExchange))
    source = CcxtPublicMarketData("broken", retries=0)
    with pytest.raises(RuntimeError, match=r"broken\[1\].*blocked endpoint"):
        source.fetch_snapshot("BTC/USDT")


def test_ctrl_c_during_wait_exits_without_traceback(tmp_path, capsys):
    item = broker(tmp_path)

    def interrupt(_seconds):
        raise KeyboardInterrupt

    run_live_loop(
        "BTC/USDT",
        item.market_data,
        item,
        lambda _snapshot, _broker: ("HOLD", 0.0),
        sleeper=interrupt,
    )
    assert "stopped safely" in capsys.readouterr().out
