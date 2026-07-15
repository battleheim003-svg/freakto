import pandas as pd

from engine.event_opportunity_universe import EventUniverseConfig, build_event_opportunity_universe


def test_paper_mode_does_not_require_future_return_columns():
    now = pd.Timestamp.now(tz="UTC")
    frame = pd.DataFrame(
        [
            {
                "decision_id": "paper-1",
                "candle_timestamp": now,
                "symbol": "BTC/USDT",
                "timeframe": "4h",
                "side": "LONG",
                "regime_label": "BULL",
                "trend_score": 28,
                "momentum_score": 20,
                "volume_score": 15,
                "structure_score": 10,
                "risk_penalty": 0,
                "entry_price": 100,
                "stop_zone": 98,
                "targets": "[106]",
                "round_trip_cost_pct": 0.5,
                "breakout_confirmed": True,
            }
        ]
    )
    events, diagnostics = build_event_opportunity_universe(frame, EventUniverseConfig(), time_scope="paper")
    assert len(events) == 1
    assert events.iloc[0]["cost_gate_pass"]
    assert diagnostics.outcome_fields_used is False


def test_paper_mode_derives_cost_from_fee_and_slippage_bps():
    now = pd.Timestamp.now(tz="UTC")
    frame = pd.DataFrame(
        [
            {
                "decision_id": "paper-cost-1",
                "candle_timestamp": now,
                "symbol": "ETH/USDT",
                "timeframe": "4h",
                "side": "LONG",
                "regime_label": "BULL",
                "trend_score": 28,
                "momentum_score": 20,
                "volume_score": 15,
                "structure_score": 10,
                "risk_penalty": 0,
                "entry_price": 100,
                "stop_zone": 98,
                "targets": "[106]",
                "fee_bps_per_side": 10,
                "slippage_bps_per_side": 5,
                "breakout_confirmed": True,
            }
        ]
    )
    events, _ = build_event_opportunity_universe(frame, EventUniverseConfig(), time_scope="paper")
    assert len(events) == 1
    assert events.iloc[0]["event_execution_cost_pct"] == 0.3
    assert events.iloc[0]["cost_gate_pass"]
