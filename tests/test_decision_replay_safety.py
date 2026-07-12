from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from engine.common import ScoreComponent
from engine.decision import DecisionEngine


def component(name: str, points: int = 0, max_points: int = 10) -> ScoreComponent:
    return ScoreComponent(name=name, points=points, max_points=max_points)


def test_constructor_accepts_replay_safety_flags():
    engine = DecisionEngine(
        min_side_score=50,
        allow_learning_overrides=False,
        allow_historical_edge=False,
    )

    assert engine.allow_learning_overrides is False
    assert engine.allow_historical_edge is False


def test_historical_edge_is_not_read_when_disabled():
    engine = DecisionEngine(allow_historical_edge=False)
    regime = SimpleNamespace(label="SIDEWAYS")
    base_component = component("Base", 1)

    with (
        patch("engine.decision.score_trend", return_value=base_component),
        patch("engine.decision.score_momentum", return_value=base_component),
        patch("engine.decision.score_volume", return_value=base_component),
        patch("engine.decision.score_structure", return_value=base_component),
        patch("engine.decision.score_risk", return_value=component("Risk Penalty", 0, 25)),
        patch.object(engine, "_regime_component", return_value=component("Regime Adjustment", 0)),
        patch("engine.decision.score_adaptive_adjustment", return_value=component("Adaptive Adjustment", 0)),
        patch("engine.decision.score_historical_edge") as historical_edge,
    ):
        _, components = engine._analyze_side(
            prev_row=pd.Series(dtype=float),
            row=pd.Series(dtype=float),
            recent_df=pd.DataFrame(),
            side="LONG",
            regime=regime,
            symbol="BTC/USDT",
            timeframe="4h",
            latest_timestamp="2026-01-01T00:00:00Z",
        )

    historical_edge.assert_not_called()
    edge_component = next(item for item in components if item.name == "Historical Edge")
    assert edge_component.points == 0


def test_analysis_exports_replay_safety_metadata():
    engine = DecisionEngine(
        min_side_score=50,
        allow_learning_overrides=False,
        allow_historical_edge=False,
    )
    frame = pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=40, freq="4h", tz="UTC"),
            "close": [100.0] * 40,
            "sma_10": [99.0] * 40,
            "sma_30": [98.0] * 40,
            "ema_10": [99.5] * 40,
            "rsi_14": [60.0] * 40,
            "macd_diff": [1.0] * 40,
            "atr_pct": [0.01] * 40,
        }
    )
    components = [
        component("Trend", 25, 28),
        component("Momentum", 20, 30),
        component("Volume", 5, 20),
        component("Structure", 6, 12),
        component("Regime Adjustment", 0, 10),
        component("Risk Penalty", 0, 25),
        component("Historical Edge", 0, 12),
    ]
    regime = SimpleNamespace(
        label="TRENDING_BULL",
        confidence=80,
        adjustment=5,
        reasons=[],
        warnings=[],
    )

    with (
        patch("engine.decision.detect_market_regime", return_value=regime),
        patch.object(engine, "_analyze_side", side_effect=[(75, components), (20, components)]),
    ):
        opportunity = engine.analyze(frame, "BTC/USDT", "4h")

    assert opportunity.raw["allow_learning_overrides"] is False
    assert opportunity.raw["allow_historical_edge"] is False
    assert opportunity.raw["replay_safe"] is True
