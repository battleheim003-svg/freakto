from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from freakto.showcase_paper import controller
from freakto.showcase_paper.card import HEIGHT, WIDTH, render_trade_card
from freakto.showcase_paper.engine import ShowcaseEngine, ShowcaseSettings


class FakeMarketData:
    def __init__(self, prices):
        self.prices = prices

    def fetch_snapshot(self, symbol):
        price = float(self.prices[symbol])
        return SimpleNamespace(symbol=symbol, last=price, bid=price, ask=price, provider="test")


def signal(symbol):
    return SimpleNamespace(
        side="SHORT" if symbol.startswith("ETH") else "LONG",
        decision_timestamp="2026-07-26T00:00:00+00:00",
        score=72,
        confidence=68,
        recommendation="WATCHLIST",
        regime="TREND",
    )


def test_showcase_opens_multiple_isolated_trades_and_cards(tmp_path):
    now = datetime(2026, 7, 26, tzinfo=timezone.utc)
    settings = ShowcaseSettings(
        symbols=("BTC/USDT", "ETH/USDT"),
        daily_trade_limit=2,
        maximum_open_positions=2,
        notional_usdt=100,
    )
    market = FakeMarketData({"BTC/USDT": 100, "ETH/USDT": 50})
    engine = ShowcaseEngine(tmp_path, settings, market, signal, now_fn=lambda: now)
    opened = engine.open_available()
    assert len(opened) == 2
    assert {trade["side"] for trade in opened} == {"LONG", "SHORT"}
    assert all(trade["official_evidence_eligible"] is False for trade in opened)
    assert all(Path(trade["open_card"]).is_file() for trade in opened)
    assert (tmp_path / "session.json").is_file()
    assert not (tmp_path / "go_live_evidence.json").exists()


def test_showcase_marks_long_and_short_and_closes_on_target(tmp_path):
    clock = {"now": datetime(2026, 7, 26, tzinfo=timezone.utc)}
    settings = ShowcaseSettings(
        symbols=("BTC/USDT", "ETH/USDT"), daily_trade_limit=2,
        maximum_open_positions=2, notional_usdt=100, take_profit_pct=0.5,
    )
    market = FakeMarketData({"BTC/USDT": 100, "ETH/USDT": 50})
    engine = ShowcaseEngine(tmp_path, settings, market, signal, now_fn=lambda: clock["now"])
    engine.open_available()
    market.prices.update({"BTC/USDT": 101, "ETH/USDT": 49})
    clock["now"] += timedelta(minutes=1)
    closed = engine.mark_and_close()
    assert len(closed) == 2
    assert all(trade["close_reason"] == "TARGET" for trade in closed)
    assert all(trade["pnl_pct"] > 0 for trade in closed)
    assert all(Path(trade["close_card"]).is_file() for trade in closed)


def test_trade_card_is_portrait_and_explicitly_simulated(tmp_path):
    path = render_trade_card(
        {
            "trade_id": "demo-1", "symbol": "BTC/USDT", "side": "LONG", "status": "CLOSED",
            "leverage": 1, "pnl_pct": 1.25, "pnl_usdt": 3.12, "entry_price": 100,
            "exit_price": 101.25, "current_price": 101.25, "stop_price": 99.4,
            "target_price": 100.9, "notional_usdt": 250, "updated_utc": "2026-07-26T00:00:00+00:00",
        },
        tmp_path / "card.png",
    )
    with Image.open(path) as image:
        assert image.size == (WIDTH, HEIGHT)


def test_showcase_controller_forces_all_live_flags_off(monkeypatch, tmp_path):
    called = {}

    class Process:
        pid = 7711

    monkeypatch.setattr(controller.subprocess, "Popen", lambda command, **kwargs: called.update(command=command, kwargs=kwargs) or Process())
    state = controller.start_showcase(root=tmp_path, daily_trade_limit=4, scan_interval_seconds=60, maximum_holding_minutes=30, leverage=2)
    assert state["pid"] == 7711
    assert state["official_evidence_eligible"] is False
    assert called["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"
    assert called["kwargs"]["env"]["REAL_CAPITAL_ENABLED"] == "false"
    assert called["kwargs"]["env"]["LIVE_DEMO_EXECUTION_ENABLED"] == "false"


def test_showcase_settings_reject_excessive_display_leverage():
    with pytest.raises(ValueError, match="leverage"):
        ShowcaseSettings(leverage=20).validated()
