from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from freakto.showcase_paper.risk import admission_reason, risk_policy
from freakto.technical_v2.data_quality import assess_data_quality
from freakto.technical_v2.economics import assess_economics
from freakto.technical_v2.execution_simulator import estimate_execution
from freakto.technical_v2.futures_microstructure import microstructure_evidence
from freakto.technical_v2.portfolio_risk import assess_portfolio
from freakto.technical_v2.promotion import promotion_recommendation
from freakto.technical_v2.segmented_calibration import segmented_calibration
from freakto.technical_v2.service import TechnicalEngineV2
from freakto.technical_v2.trade_geometry import build_trade_geometry
from freakto.technical_v2.triple_barrier import evaluate_triple_barrier
from freakto.technical_v2.validation import purged_walk_forward_splits, sequential_oos_report


def candles(*, rows: int = 140, timeframe_minutes: int = 5, slope: float = 0.2, now: datetime | None = None) -> pd.DataFrame:
    end = now or datetime.now(timezone.utc)
    start = end - timedelta(minutes=timeframe_minutes * (rows - 1))
    records = []
    for index in range(rows):
        price = 100 + index * slope
        records.append({
            "timestamp": start + timedelta(minutes=timeframe_minutes * index),
            "open": price - 0.1, "high": price + 0.5, "low": price - 0.5,
            "close": price, "volume": 1000 + index,
        })
    return pd.DataFrame(records)


def test_data_quality_detects_staleness_duplicates_and_source_divergence():
    now = datetime.now(timezone.utc)
    fresh = candles(now=now)
    assert assess_data_quality(fresh, timeframe="5m", now=now, require_fresh=True).status == "PASS"
    duplicated = pd.concat([fresh, fresh.tail(1)], ignore_index=True)
    report = assess_data_quality(duplicated, timeframe="5m", now=now, require_fresh=True)
    assert report.status == "WARN"
    assert "DUPLICATE_TIMESTAMPS" in report.reasons
    stale = assess_data_quality(fresh, timeframe="5m", now=now + timedelta(hours=2), require_fresh=True)
    assert stale.status == "FAIL"
    divergent = assess_data_quality(fresh, timeframe="5m", reference_close=200)
    assert divergent.status == "FAIL"


def test_execution_cost_increases_with_volatility_and_thin_volume():
    liquid = estimate_execution(100, "LONG", volatility_percentile=0.2, relative_volume=2)
    stressed = estimate_execution(100, "LONG", volatility_percentile=0.95, relative_volume=0.2)
    assert stressed.estimated_round_trip_cost_pct > liquid.estimated_round_trip_cost_pct
    assert stressed.effective_entry_price > liquid.effective_entry_price


def test_expected_value_includes_costs_and_can_fail_trade():
    geometry = build_trade_geometry(candles(), "LONG")
    cheap = estimate_execution(geometry.entry, "LONG", spread_bps=0, base_slippage_bps=0, latency_ms=0)
    expensive = estimate_execution(geometry.entry, "LONG", spread_bps=40, base_slippage_bps=30, latency_ms=3000)
    positive = assess_economics(0.8, geometry, cheap, fee_bps_per_side=0)
    negative = assess_economics(0.52, geometry, expensive, fee_bps_per_side=20)
    assert positive.net_expected_value_pct > 0
    assert negative.net_expected_value_pct < positive.net_expected_value_pct
    assert negative.status == "NEGATIVE"


def test_triple_barrier_is_conservative_when_both_barriers_hit():
    future = pd.DataFrame([{"open": 100, "high": 110, "low": 90, "close": 105}])
    result = evaluate_triple_barrier(future, side="LONG", stop=95, target=105, maximum_bars=5)
    assert result["label"] == "STOP"
    assert result["intrabar_ambiguous"] is True


def test_triple_barrier_prices_adverse_stop_gap_at_open():
    future = pd.DataFrame([{"open": 90, "high": 92, "low": 88, "close": 91}])
    result = evaluate_triple_barrier(future, side="LONG", stop=95, target=110, maximum_bars=5)
    assert result["label"] == "STOP"
    assert result["exit_price"] == 90
    assert result["gap"] is True


def test_segmented_calibration_uses_specific_segment_then_global_fallback():
    rows = [
        {"probability": 0.95, "outcome": True, "symbol": "BTC", "setup": "BREAKOUT", "regime": "UP", "side": "LONG", "timeframe": "1m"}
        for _ in range(60)
    ]
    summary, segment = segmented_calibration(rows, {"symbol": "BTC", "setup": "BREAKOUT", "regime": "UP", "side": "LONG", "timeframe": "1m"})
    fallback, fallback_segment = segmented_calibration(rows, {"symbol": "ETH", "setup": "OTHER", "regime": "DOWN", "side": "SHORT", "timeframe": "5m"})
    assert summary.status == "CALIBRATED"
    assert segment == "symbol+setup+regime+side+timeframe"
    assert fallback.samples == 60
    assert fallback_segment == "global"


def test_microstructure_never_fabricates_missing_data():
    missing, status = microstructure_evidence(None)
    evidence, available = microstructure_evidence({"funding_rate_pct": 0.08, "taker_buy_ratio": 0.7})
    assert missing == () and status["status"] == "UNAVAILABLE"
    assert {item.name for item in evidence} == {"FUNDING_EXTREME", "TAKER_IMBALANCE"}
    assert available["status"] == "AVAILABLE"


def test_portfolio_overlay_reduces_correlated_same_side_exposure():
    positions = [
        {"symbol": symbol, "side": "LONG", "status": "OPEN", "notional_usdt": 500}
        for symbol in ("BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT")
    ]
    report = assess_portfolio("ADA/USDT", "LONG", positions)
    assert report.status == "REDUCE"
    assert report.size_multiplier < 1
    assert report.correlated_positions == 4


def test_purged_walk_forward_has_explicit_gaps_and_no_overlap():
    splits = purged_walk_forward_splits(120, train_size=50, test_size=20, purge_bars=3, embargo_bars=2)
    assert len(splits) >= 2
    for fold in splits:
        assert fold["train"][1] <= fold["purge"][0] < fold["test"][0]
        assert fold["test"][1] <= fold["embargo"][1]
    for previous, current in zip(splits, splits[1:]):
        assert current["train"][1] >= previous["embargo"][1]


def test_automatic_promotion_is_fail_closed():
    validation = sequential_oos_report([{"pnl_pct": 1.0}] * 9)
    blocked = promotion_recommendation({"expectancy_pct": 0.1}, {"samples": 10, "expectancy_pct": 0.3}, validation)
    approved = promotion_recommendation(
        {"expectancy_pct": 0.1, "maximum_drawdown_pct": 5},
        {"samples": 250, "expectancy_pct": 0.3, "maximum_drawdown_pct": 3},
        validation,
    )
    assert blocked["status"] == "KEEP_RESEARCH"
    assert approved["status"] == "PROMOTE_TO_SHADOW"
    assert approved["live_eligible"] is False


def test_professional_decision_contains_complete_audit_packet():
    frames = {"1m": candles(timeframe_minutes=1), "5m": candles(timeframe_minutes=5), "1h": candles(timeframe_minutes=60)}
    decision = TechnicalEngineV2(analysis_depth=100, risk_level=40).analyse(
        "BTC/USDT",
        frames,
        timestamp="now",
        microstructure_data={"funding_rate_pct": 0.01, "taker_buy_ratio": 0.6},
        portfolio_positions=[],
    )
    payload = decision.to_dict()
    assert payload["data_quality"]["status"] in {"PASS", "WARN"}
    assert payload["setup"]["name"] != "NO_VALID_SETUP"
    assert payload["economics"]["cost_breakdown"]["fees"] > 0
    assert payload["execution"]["fill_ratio"] > 0
    assert payload["portfolio"]["status"] == "PASS"
    assert any(item["family"] == "microstructure" for item in payload["family_scores"])


def test_showcase_admission_rejects_bad_data_and_non_positive_ev():
    policy = risk_policy(100)
    base = {"side": "LONG", "score": 90, "confidence": 90, "recommendation": "ELITE"}
    assert admission_reason({**base, "data_quality": {"status": "FAIL"}}, policy) == "DATA_QUALITY_REJECTED"
    assert admission_reason({**base, "data_quality": {"status": "PASS"}, "setup": {"status": "ACTIONABLE"}, "economics": {"net_expected_value_pct": -0.01}}, policy) == "NON_POSITIVE_EXPECTED_VALUE"
