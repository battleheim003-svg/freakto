import json

import pytest

from engine.live_demo import MarketSnapshot, MockBroker, run_live_universe_loop
from engine.live_demo_universe import load_universe, select_symbols


class SymbolMarketData:
    def fetch_snapshot(self, symbol):
        if symbol == "BAD/USDT":
            raise RuntimeError("not listed")
        return MarketSnapshot("2026-01-01T00:00:00+00:00", symbol, 100, 99, 101, provider="kucoin")


def write_universe(path):
    path.write_text(json.dumps({
        "schema_version": 1,
        "groups": {"core": ["BTC/USDT", "ETH/USDT"], "growth": ["SUI/USDT"], "meme": ["DOGE/USDT", "PEPE/USDT"]},
        "history": {"timeframe": "4h", "target_years": 3, "minimum_coverage_pct": 90, "discover_listing_boundary": True},
    }), encoding="utf-8")


def test_universe_groups_are_deduplicated_and_meme_is_selectable(tmp_path):
    path = tmp_path / "universe.json"
    write_universe(path)
    universe = load_universe(path)
    assert select_symbols(universe, groups=("meme",)) == ("DOGE/USDT", "PEPE/USDT")
    assert len(universe.all_symbols) == 5


def test_explicit_symbols_override_groups(tmp_path):
    path = tmp_path / "universe.json"
    write_universe(path)
    universe = load_universe(path)
    assert select_symbols(universe, groups=("meme",), explicit_symbols=("LINK/USDT",)) == ("LINK/USDT",)


def test_unknown_group_fails_closed(tmp_path):
    path = tmp_path / "universe.json"
    write_universe(path)
    with pytest.raises(ValueError):
        select_symbols(load_universe(path), groups=("unknown",))


def test_universe_loop_isolates_unavailable_symbol_and_keeps_scanning(tmp_path, capsys):
    source = SymbolMarketData()
    broker = MockBroker(source, state_path=tmp_path / "state.json", trade_log_path=tmp_path / "trades.csv")
    run_live_universe_loop(
        ("BTC/USDT", "BAD/USDT", "DOGE/USDT"),
        source,
        broker,
        lambda _snapshot, _broker: ("HOLD", 0),
        once=True,
    )
    output = capsys.readouterr().out
    assert "Universe cycle complete: 2/3" in output
    assert "[BAD/USDT]" in output
