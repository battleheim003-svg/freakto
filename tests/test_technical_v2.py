from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from freakto.research.adapters.technical_v2_adapter import TechnicalV2FrameAdapter
from freakto.technical_v2.calibration import calibration_summary
from freakto.technical_v2.ensemble import aggregate_families
from freakto.technical_v2.evaluator import compare_challengers, evaluate_decisions
from freakto.technical_v2.features import extract_evidence
from freakto.technical_v2.regime import assess_regime
from freakto.technical_v2.risk_overlay import assess_risk
from freakto.technical_v2.service import TechnicalEngineV2, analysis_profile
from freakto.technical_v2.trade_geometry import build_trade_geometry


def frame(*, slope: float = 0.4, rows: int = 140, spike_last: float = 0.0) -> pd.DataFrame:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    records = []
    for index in range(rows):
        price = 100 + index * slope + ((index % 7) - 3) * 0.05
        if index == rows - 1:
            price += spike_last
        records.append(
            {
                "timestamp": start + timedelta(minutes=index * 5),
                "open": price - slope * 0.4,
                "high": price + 0.8,
                "low": price - 0.8,
                "close": price,
                "volume": 1000 + index * 3,
            }
        )
    return pd.DataFrame(records)


def test_continuous_features_are_bounded_and_family_grouped():
    evidence = extract_evidence(frame(), timeframe="5m", depth=100)
    assert len(evidence) == 10
    assert all(-1 <= item.direction <= 1 and 0 <= item.strength <= 1 for item in evidence)
    assert {item.family for item in evidence} >= {"trend", "momentum", "structure", "volume"}


def test_family_ensemble_counts_correlated_indicators_once_per_family():
    data = frame()
    evidence = extract_evidence(data, depth=100)
    families, aggregate = aggregate_families(evidence, assess_regime(data))
    trend = next(item for item in families if item.family == "trend")
    assert trend.evidence_count == 2
    assert len(families) < len(evidence)
    assert -1 <= aggregate <= 1


def test_closed_candle_adapter_ignores_forming_candle_mutation():
    adapter = TechnicalV2FrameAdapter(risk_level=35, analysis_depth=100)
    normal = frame()
    spiked = frame(spike_last=1000)
    first = adapter.signal("BTC/USDT", {"5m": normal}, timestamp="t", provider="test", drop_forming=True)
    second = adapter.signal("BTC/USDT", {"5m": spiked}, timestamp="t", provider="test", drop_forming=True)
    assert first.technical_v2["raw_score"] == second.technical_v2["raw_score"]
    assert first.trade_geometry == second.trade_geometry


def test_adapter_calibrates_from_closed_paper_outcomes():
    adapter = TechnicalV2FrameAdapter(risk_level=35, analysis_depth=100)
    adapter.set_calibration_observations([(0.95, True)] * 40 + [(0.05, False)] * 20)
    signal = adapter.signal("BTC/USDT", {"5m": frame()}, timestamp="t", provider="test")
    assert signal.calibration["status"] == "CALIBRATED"
    assert signal.calibration["samples"] == 60


def test_professional_decision_has_mtf_regime_geometry_and_explanation_fields():
    decision = TechnicalEngineV2(analysis_depth=100, risk_level=40).analyse(
        "BTC/USDT", {"5m": frame(slope=0.5), "1h": frame(slope=0.2)}, timestamp="2026-01-02"
    )
    payload = decision.to_dict()
    assert decision.side == "LONG"
    assert decision.timeframe_agreement > 0.5
    assert decision.geometry.reward_risk > 1
    assert decision.geometry.cost_adjusted_reward_risk < decision.geometry.reward_risk
    assert payload["regime"]["label"].startswith("UPTREND")
    assert payload["reasons"]
    assert payload["engine_version"] == "technical-v2.0"


def test_analysis_depth_is_independent_from_risk_tolerance():
    assert analysis_profile(100)["timeframes"] == ("5m", "15m", "1h", "4h")
    low_risk = assess_risk(0, confidence=0.8, timeframe_agreement=0.8, geometry_rr=1.5)
    high_risk = assess_risk(100, confidence=0.8, timeframe_agreement=0.8, geometry_rr=1.5)
    assert low_risk.position_scale < high_risk.position_scale
    assert low_risk.admission_threshold > high_risk.admission_threshold


def test_geometry_is_directional_and_cost_aware():
    long = build_trade_geometry(frame(), "LONG")
    short = build_trade_geometry(frame(), "SHORT")
    assert long.stop < long.entry < long.target
    assert short.target < short.entry < short.stop
    assert 0 < long.cost_adjusted_reward_risk < long.reward_risk


def test_calibration_fails_closed_until_sample_is_sufficient():
    small = calibration_summary([(0.7, True)] * 10)
    reliable = calibration_summary([(0.95, True)] * 40 + [(0.05, False)] * 20)
    assert small.status == "UNCALIBRATED"
    assert reliable.status == "CALIBRATED"
    assert reliable.samples == 60


def test_evaluator_attributes_families_and_requires_comparison_samples():
    records = [
        {"pnl_pct": 1.0, "family_scores": [{"family": "trend", "score": 0.8}], "technical_v2": {"evidence": [{"name": "EMA", "direction": 0.8}]}},
        {"pnl_pct": -0.5, "family_scores": [{"family": "trend", "score": -0.5}]},
    ]
    report = evaluate_decisions(records)
    comparison = compare_challengers(report, report, minimum_samples=50)
    assert report["samples"] == 2
    assert report["family_attribution"]["trend"] > 0
    assert report["tool_attribution"]["EMA"] > 0
    assert comparison["eligible"] is False
