from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from freakto.showcase_paper import controller
from freakto.showcase_paper import live_intraday
from freakto.showcase_paper.card import HEIGHT, WIDTH, render_trade_card
from freakto.showcase_paper.engine import ShowcaseEngine, ShowcaseSettings
from freakto.showcase_paper.performance import performance_summary, walk_forward_quality_comparison
from freakto.showcase_paper.quality import quality_admission_reason, quality_profile
from freakto.showcase_paper.replay_lab import AcceleratedReplayMarket
from freakto.showcase_paper.risk import admission_reason, risk_policy, session_preset


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


def test_manual_showcase_stop_uses_last_mark_without_waiting_for_market(tmp_path):
    now = datetime(2026, 7, 26, tzinfo=timezone.utc)
    market = FakeMarketData({"BTC/USDT": 100})
    engine = ShowcaseEngine(
        tmp_path,
        ShowcaseSettings(symbols=("BTC/USDT",), maximum_open_positions=1),
        market,
        signal,
        now_fn=lambda: now,
    )
    engine.open_available()

    def fail_if_fetched(_symbol):
        raise AssertionError("manual stop must not fetch remote market data")

    market.fetch_snapshot = fail_if_fetched
    closed = engine.mark_and_close(close_all=True)
    assert len(closed) == 1
    assert closed[0]["close_reason"] == "SESSION_STOP"
    assert closed[0]["exit_price"] == closed[0]["current_price"]
    assert Path(closed[0]["close_card"]).is_file()


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
        image.load()
    assert list(tmp_path.glob("*.tmp")) == []


def test_showcase_controller_forces_all_live_flags_off(monkeypatch, tmp_path):
    called = {}

    class Process:
        pid = 7711

    monkeypatch.setattr(controller.subprocess, "Popen", lambda command, **kwargs: called.update(command=command, kwargs=kwargs) or Process())
    state = controller.start_showcase(root=tmp_path, daily_trade_limit=4, scan_interval_seconds=60, maximum_holding_minutes=30, leverage=2, risk_level=70, market_mode="ACCELERATED_REPLAY")
    assert state["pid"] == 7711
    assert state["official_evidence_eligible"] is False
    assert called["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"
    assert called["kwargs"]["env"]["REAL_CAPITAL_ENABLED"] == "false"
    assert called["kwargs"]["env"]["LIVE_DEMO_EXECUTION_ENABLED"] == "false"
    assert "--risk-level" in called["command"]
    assert "--quality-mode" in called["command"]
    assert "--replay-timeframe" in called["command"]
    assert "ACCELERATED_REPLAY" in called["command"]


def test_controller_state_writes_use_collision_safe_temporary_files(tmp_path):
    path = tmp_path / "runtime" / "worker.json"
    controller._write(path, {"status": "RUNNING", "pid": 1})
    controller._write(path, {"status": "STOPPED", "pid": 1})
    import json
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "STOPPED"
    assert list(path.parent.glob("*.tmp")) == []


def test_showcase_settings_reject_excessive_display_leverage():
    with pytest.raises(ValueError, match="leverage"):
        ShowcaseSettings(leverage=20).validated()


def test_risk_zero_is_strict_and_higher_risk_widens_admission():
    candidate = {"side": "LONG", "score": 62, "confidence": 58, "recommendation": "WATCHLIST"}
    assert admission_reason(candidate, risk_policy(0)) is not None
    assert admission_reason(candidate, risk_policy(70)) is None
    assert risk_policy(0).maximum_open_positions < risk_policy(100).maximum_open_positions
    assert len(risk_policy(0).technical_indicators) == 3
    assert len(risk_policy(100).technical_indicators) == 12
    assert risk_policy(100).reentry_cooldown_minutes == 0


def test_rapid_preset_is_short_and_uses_accelerated_replay():
    preset = session_preset("RAPID_TEST")
    assert preset.risk_level == 100
    assert preset.daily_trade_limit == 0
    assert preset.scan_interval_seconds == 15
    assert preset.maximum_holding_minutes == 5
    assert preset.market_mode == "ACCELERATED_REPLAY"


def test_quality_preset_is_the_strict_accelerated_default():
    preset = session_preset("QUALITY_TEST")
    assert preset.risk_level == 30
    assert preset.analysis_depth == 100
    assert preset.market_mode == "ACCELERATED_REPLAY"
    assert session_preset("").key == "QUALITY_TEST"


def test_showcase_reports_risk_rejections(tmp_path):
    weak_signal = lambda _symbol: SimpleNamespace(
        side="LONG", decision_timestamp="2026-07-26T00:00:00+00:00",
        score=55, confidence=51, recommendation="WATCHLIST", regime="RANGE",
    )
    engine = ShowcaseEngine(
        tmp_path,
        ShowcaseSettings(symbols=("BTC/USDT",), risk_level=0),
        FakeMarketData({"BTC/USDT": 100}),
        weak_signal,
    )
    assert engine.open_available() == []
    assert engine.state["last_scan"]["rejected"]["SCORE_BELOW_POLICY"] == 1


def test_accelerated_replay_advances_local_market_without_network(tmp_path):
    data_dir = tmp_path / "data" / "market_replay" / "4h"
    data_dir.mkdir(parents=True)
    rows = []
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for index in range(50):
        price = 100 + index
        rows.append({
            "timestamp": (start + timedelta(hours=4 * index)).isoformat(),
            "open": price - 1, "high": price + 1, "low": price - 2,
            "close": price, "volume": 1000, "provider": "test",
        })
    import pandas as pd
    pd.DataFrame(rows).to_csv(data_dir / "BTC_USDT.csv.gz", index=False, compression="gzip")

    replay = AcceleratedReplayMarket(tmp_path, ("BTC/USDT",))
    first = replay.fetch_snapshot("BTC/USDT").last
    signal_item = replay.signal("BTC/USDT")
    replay.advance()
    second = replay.fetch_snapshot("BTC/USDT").last

    assert signal_item.side == "LONG"
    assert signal_item.regime == "UPTREND"
    assert len(signal_item.indicators_used) == 10
    assert signal_item.technical_confluence_pct >= 50
    assert second > first


def test_unlimited_session_can_reopen_after_close(tmp_path):
    clock = {"now": datetime(2026, 7, 26, tzinfo=timezone.utc)}
    settings = ShowcaseSettings(
        symbols=("BTC/USDT",), daily_trade_limit=0, maximum_open_positions=1,
        risk_level=70, reentry_cooldown_minutes=0, take_profit_pct=0.5,
    )
    market = FakeMarketData({"BTC/USDT": 100})
    engine = ShowcaseEngine(tmp_path, settings, market, signal, now_fn=lambda: clock["now"])
    assert len(engine.open_available()) == 1
    market.prices["BTC/USDT"] = 101
    clock["now"] += timedelta(minutes=1)
    assert len(engine.mark_and_close()) == 1
    assert len(engine.open_available()) == 1
    assert len(engine.trades) == 2


def test_session_profit_guard_waits_for_minimum_trades_then_blocks_new_entries(tmp_path):
    clock = {"now": datetime(2026, 7, 26, tzinfo=timezone.utc)}
    settings = ShowcaseSettings(
        symbols=("BTC/USDT",), daily_trade_limit=0, maximum_open_positions=1,
        notional_usdt=100, risk_level=100, reentry_cooldown_minutes=0,
        take_profit_pct=0.5, session_equity_usdt=100,
        session_profit_target_pct=2.0, session_loss_limit_pct=10.0,
        minimum_closed_trades_for_profit_stop=3,
    )
    market = FakeMarketData({"BTC/USDT": 100})
    engine = ShowcaseEngine(tmp_path, settings, market, signal, now_fn=lambda: clock["now"])
    engine.start_session_guard()
    for index in range(3):
        market.prices["BTC/USDT"] = 100
        assert len(engine.open_available()) == 1
        market.prices["BTC/USDT"] = 102
        clock["now"] += timedelta(minutes=1)
        assert len(engine.mark_and_close()) == 1
        guard = engine.evaluate_session_guard()
        if index < 2:
            assert guard["status"] == "ACTIVE"
    assert guard["status"] == "PROFIT_TARGET_REACHED"
    assert guard["closed_trades"] == 3
    assert guard["session_return_pct"] >= 2
    assert engine.open_available() == []
    assert engine.state["last_scan"]["rejected"]["PROFIT_TARGET_REACHED"] == 1


def test_session_loss_guard_stops_without_minimum_trade_requirement(tmp_path):
    now = datetime(2026, 7, 26, tzinfo=timezone.utc)
    settings = ShowcaseSettings(
        symbols=("BTC/USDT",), maximum_open_positions=1, notional_usdt=100,
        risk_level=100, reentry_cooldown_minutes=0, session_equity_usdt=100,
        session_profit_target_pct=3.0, session_loss_limit_pct=1.0,
        minimum_closed_trades_for_profit_stop=3,
    )
    market = FakeMarketData({"BTC/USDT": 100})
    engine = ShowcaseEngine(tmp_path, settings, market, signal, now_fn=lambda: now)
    engine.start_session_guard()
    engine.open_available()
    market.prices["BTC/USDT"] = 95
    engine.mark_and_close()
    guard = engine.evaluate_session_guard()
    assert guard["status"] == "LOSS_LIMIT_REACHED"
    assert guard["closed_trades"] == 1
    assert guard["loss_limit_usdt"] == pytest.approx(1.0)
    assert guard["remaining_loss_buffer_pct"] == 0


def _quality_trade(index, *, symbol="BTC/USDT", side="LONG", pnl=-1.0):
    return {
        "trade_id": f"q-{index}", "status": "CLOSED", "close_reason": "STOP" if pnl <= 0 else "TARGET",
        "symbol": symbol, "side": side, "pnl_usdt": pnl, "pnl_pct": pnl,
        "opened_utc": f"2026-07-{index + 1:02d}T00:00:00+00:00",
        "recommendation": "WATCHLIST", "technical_confluence_pct": 65,
        "economics": {"net_expected_value_pct": 0.8},
        "trade_geometry": {"cost_adjusted_reward_risk": 1.4},
    }


def test_win_rate_quality_gate_quarantines_mature_weak_symbol_side_bucket():
    history = [_quality_trade(index, pnl=1.0 if index < 2 else -1.0) for index in range(10)]
    candidate = _quality_trade(11)
    reason, diagnostics = quality_admission_reason(candidate, history, quality_profile("WIN_RATE"))
    assert reason == "QUALITY_SYMBOL_SIDE_QUARANTINE"
    assert diagnostics["symbol_side"]["samples"] == 10
    assert diagnostics["symbol_side"]["win_rate"] == pytest.approx(0.2)


def test_healthy_exact_bucket_can_override_a_weak_global_side():
    healthy = [_quality_trade(index, pnl=1.0 if index < 5 else -1.0) for index in range(10)]
    weak_other = [
        _quality_trade(index + 10, symbol="ETH/USDT", pnl=1.0 if index < 5 else -1.0)
        for index in range(40)
    ]
    reason, _ = quality_admission_reason(_quality_trade(60), healthy + weak_other, quality_profile("WIN_RATE"))
    assert reason is None


def test_quality_walk_forward_comparison_never_uses_future_outcomes():
    rows = [_quality_trade(index, pnl=1.0 if index < 2 else -1.0) for index in range(15)]
    report = walk_forward_quality_comparison(rows)
    assert report["method"] == "CAUSAL_WALK_FORWARD_FILTER"
    assert report["official_evidence_eligible"] is False
    assert report["candidate"]["samples"] < report["baseline"]["samples"]
    assert performance_summary(rows)["profit_factor"] < 1


def test_replay_ohlc_barrier_uses_conservative_stop_first_fill(tmp_path):
    clock = {"now": datetime(2026, 7, 26, tzinfo=timezone.utc)}
    bar = {"index": 0, "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0}

    class BarMarket:
        def fetch_snapshot(self, symbol):
            return SimpleNamespace(
                symbol=symbol, last=bar["close"], bid=bar["close"], ask=bar["close"],
                provider="bar-test", bar_index=bar["index"], timestamp=str(bar["index"]),
                open=bar["open"], high=bar["high"], low=bar["low"],
            )

    engine = ShowcaseEngine(
        tmp_path,
        ShowcaseSettings(symbols=("BTC/USDT",), maximum_open_positions=1, stop_loss_pct=0.6, take_profit_pct=0.9),
        BarMarket(), signal, now_fn=lambda: clock["now"],
    )
    opened = engine.open_available()[0]
    bar.update(index=1, open=100.0, high=102.0, low=98.0, close=101.0)
    clock["now"] += timedelta(minutes=1)
    closed = engine.mark_and_close()[0]
    assert closed["close_reason"] == "STOP"
    assert closed["exit_price"] == pytest.approx(opened["initial_stop_price"])
    assert abs(closed["pnl_pct"]) < 1.0


def test_break_even_is_armed_on_close_and_applies_from_next_bar(tmp_path):
    clock = {"now": datetime(2026, 7, 26, tzinfo=timezone.utc)}
    bar = {"index": 0, "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0}

    class BarMarket:
        def fetch_snapshot(self, symbol):
            return SimpleNamespace(symbol=symbol, last=bar["close"], bid=bar["close"], ask=bar["close"], provider="bar-test", bar_index=bar["index"], timestamp=str(bar["index"]), open=bar["open"], high=bar["high"], low=bar["low"])

    engine = ShowcaseEngine(
        tmp_path,
        ShowcaseSettings(symbols=("BTC/USDT",), maximum_open_positions=1, stop_loss_pct=1.0, take_profit_pct=3.0, break_even_trigger_r=0.5),
        BarMarket(), signal, now_fn=lambda: clock["now"],
    )
    trade = engine.open_available()[0]
    bar.update(index=1, open=100.0, high=100.7, low=99.5, close=100.6)
    clock["now"] += timedelta(minutes=1)
    assert engine.mark_and_close() == []
    assert trade["break_even_armed"] is True
    bar.update(index=2, open=100.3, high=100.4, low=100.1, close=100.2)
    clock["now"] += timedelta(minutes=1)
    closed = engine.mark_and_close()[0]
    assert closed["close_reason"] == "BREAK_EVEN"
    assert abs(closed["pnl_pct"]) < 0.01


def test_strong_opposite_signal_closes_an_invalidated_position(tmp_path):
    current_side = {"value": "LONG"}

    def changing_signal(_symbol):
        return SimpleNamespace(
            side=current_side["value"], decision_timestamp=f'2026-07-26T00:00:0{0 if current_side["value"] == "LONG" else 1}+00:00',
            score=75, confidence=70, recommendation="ACTIONABLE", regime="RANGE", technical_confluence_pct=70,
        )

    engine = ShowcaseEngine(
        tmp_path, ShowcaseSettings(symbols=("BTC/USDT",), maximum_open_positions=1),
        FakeMarketData({"BTC/USDT": 100}), changing_signal,
    )
    engine.open_available()
    current_side["value"] = "SHORT"
    closed = engine.close_invalidated()
    assert len(closed) == 1
    assert closed[0]["close_reason"] == "SIGNAL_INVALIDATED"


def test_live_intraday_mode_uses_full_technical_stack(monkeypatch):
    import pandas as pd

    rows = []
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for index in range(45):
        price = 100 + index * 0.5
        rows.append({
            "timestamp": start + timedelta(minutes=5 * index),
            "open": price - 0.2, "high": price + 0.5, "low": price - 0.5,
            "close": price, "volume": 1000 + index,
        })
    frame = pd.DataFrame(rows)
    frame.attrs["provider"] = "fixture"
    monkeypatch.setattr(live_intraday, "fetch_ohlcv", lambda **_kwargs: frame)

    market = live_intraday.LiveIntradayTechnicalMarket(risk_level=100)
    item = market.signal("BTC/USDT")
    snapshot = market.fetch_snapshot("BTC/USDT")

    assert item.regime == "UPTREND"
    assert len(item.indicators_used) == 12
    assert item.technical_confluence_pct >= 50
    assert snapshot.provider == "fixture"
