import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from engine.live_demo import MarketSnapshot
from engine.live_demo_universe import UniverseConfig
from engine.live_paper_runtime import (
    RuntimeStore,
    RuntimeLock,
    LivePaperRuntime,
    evaluate_eligibility,
    intent_from_portfolio_item,
    load_runtime_config,
    position_size,
    shadow_gate_status,
    validate_intent,
)


def config(tmp_path):
    payload = json.loads(open("live_paper_config.json", encoding="utf-8").read())
    payload["data_dir"] = str(tmp_path / "data")
    payload["state_roots"] = {"shadow": str(tmp_path / "shadow"), "paper": str(tmp_path / "paper")}
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return load_runtime_config(path)


def manifest(tmp_path, symbol="BTC_USDT", status="REPLAY_READY"):
    path = tmp_path / "data" / "4h" / f"{symbol}.manifest.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"result": {"quality": {"readiness_status": status}}}), encoding="utf-8")


def snapshot():
    return MarketSnapshot(datetime.now(timezone.utc).isoformat(), "BTC/USDT", 100, 99.9, 100.1, provider="kucoin")


def item():
    closed = datetime.now(timezone.utc) - timedelta(hours=8)
    return SimpleNamespace(symbol="BTC/USDT", timeframe="4h", side="LONG", entry_zone="100", stop_zone="95", targets=["110"], price=100, decision_timestamp=closed.isoformat(), score=80, confidence=75, recommendation="ACTIONABLE", first_rr=2.0, regime="TRENDING_BULL", mtf_direction="LONG", mtf_consensus=80, expected_r=0.2, calibration_status="PROMOTED", opportunity_score=80, trade_quality_grade="A", notes=[])


def test_eligibility_requires_history_and_spread(tmp_path):
    cfg = config(tmp_path)
    assert not evaluate_eligibility("BTC/USDT", snapshot(), cfg).eligible
    manifest(tmp_path)
    assert evaluate_eligibility("BTC/USDT", snapshot(), cfg).eligible


def test_intent_contract_and_risk_sizing(tmp_path):
    cfg = config(tmp_path)
    manifest(tmp_path)
    eligibility = evaluate_eligibility("BTC/USDT", snapshot(), cfg)
    intent = intent_from_portfolio_item(item(), "core")
    valid, blockers = validate_intent(intent, cfg, eligibility)
    assert valid and not blockers
    amount, details = position_size(10_000, intent, "core", cfg)
    assert details["risk_usdt"] == 50
    assert amount == pytest.approx(10.0)


def test_shadow_gate_is_fail_closed_until_every_condition_passes(tmp_path):
    cfg = config(tmp_path)
    store = RuntimeStore(tmp_path / "shadow")
    assert not shadow_gate_status(store, cfg)["passed"]
    store.state["started_at_utc"] = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    store.state["metrics"].update(unique_decisions=20, complete_4h_candles=30, provider_checks=100, provider_fresh=95)
    store.save()
    assert shadow_gate_status(store, cfg)["passed"]


def test_shadow_and_paper_state_roots_are_distinct(tmp_path):
    cfg = config(tmp_path)
    assert cfg.state_roots["shadow"] != cfg.state_roots["paper"]


def test_meme_risk_is_lower_than_core(tmp_path):
    cfg = config(tmp_path)
    intent = intent_from_portfolio_item(item(), "core")
    core, _ = position_size(10_000, intent, "core", cfg)
    meme, _ = position_size(10_000, intent, "meme", cfg)
    assert meme < core


def test_runtime_lock_rejects_parallel_instance(tmp_path):
    lock_path = tmp_path / "runtime.lock"
    with RuntimeLock(lock_path):
        with pytest.raises(RuntimeError):
            with RuntimeLock(lock_path):
                pass
    assert not lock_path.exists()


class FakeMarket:
    def __init__(self, price=100):
        self.price = price

    def fetch_snapshot(self, symbol):
        return MarketSnapshot(datetime.now(timezone.utc).isoformat(), symbol, self.price, self.price - 0.1, self.price + 0.1, provider="kucoin")


def universe():
    return UniverseConfig(groups={"core": ("BTC/USDT",), "growth": (), "meme": ()}, timeframe="4h", target_years=3, minimum_coverage_pct=90, discover_listing_boundary=True)


def test_shadow_records_evidence_but_never_changes_virtual_balance(tmp_path):
    cfg = config(tmp_path)
    manifest(tmp_path)
    runtime = LivePaperRuntime(cfg, universe(), FakeMarket(), mode="shadow", analyzer=lambda _symbol: item())
    result = runtime.process_symbol("BTC/USDT")
    assert result["status"] == "SHADOW_CANDIDATE"
    assert runtime.broker.cash_balance == 10_000
    assert not runtime.broker.positions
    assert (tmp_path / "shadow" / "evidence" / f"{result['decision_id']}.json").exists()


def test_paper_entry_requires_flag_and_passed_shadow_gate(tmp_path, monkeypatch):
    cfg = config(tmp_path)
    manifest(tmp_path)
    shadow = RuntimeStore(tmp_path / "shadow")
    shadow.state["started_at_utc"] = (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
    shadow.state["metrics"].update(unique_decisions=20, complete_4h_candles=30, provider_checks=100, provider_fresh=95)
    shadow.save()
    monkeypatch.setenv("LIVE_DEMO_EXECUTION_ENABLED", "true")
    runtime = LivePaperRuntime(cfg, universe(), FakeMarket(), mode="paper", analyzer=lambda _symbol: item())
    result = runtime.process_symbol("BTC/USDT")
    assert result["status"] == "PAPER_ENTRY"
    assert runtime.broker.positions["BTC/USDT"].amount > 0
