from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from engine.paper_observation_v2 import (
    PaperRiskConfig,
    arm_paper_mode,
    disarm_paper_mode,
    load_arm_state,
    record_paper_observations,
)
from engine.paper_readiness_v2 import PaperLaunchReadiness


def _readiness(research=True, strategy=False):
    return PaperLaunchReadiness(
        status="READY_FOR_STRATEGY_PAPER_VALIDATION" if strategy else "READY_FOR_RESEARCH_PAPER_COLLECTION",
        created_utc=datetime.now(timezone.utc).isoformat(),
        research_collection_ready=research,
        strategy_paper_ready=strategy,
        selected_policy="EVENT_COST_GATED" if strategy else None,
        event_rows=500,
        cost_gated_event_rows=200,
        fresh_directional_rows=350 if strategy else 0,
        fresh_fixed_gate_samples=70 if strategy else 0,
        fresh_expectancy_pct=0.2 if strategy else 0.0,
        fresh_profit_factor=1.2 if strategy else 0.0,
    )


def _paper_decisions() -> pd.DataFrame:
    ts = pd.Timestamp.now(tz="UTC").floor("h")
    rows = []
    for i in range(30):
        rows.append(
            {
                "decision_id": f"d{i}",
                "candle_timestamp": ts - pd.Timedelta(hours=4 * (29 - i)),
                "symbol": "BTC/USDT",
                "timeframe": "4h",
                "side": "LONG",
                "regime_label": "BULL",
                "score": 80,
                "long_score": 80,
                "short_score": 20,
                "trend_score": 28,
                "momentum_score": 20,
                "volume_score": 15,
                "structure_score": 10,
                "regime_score": 5,
                "risk_penalty": 0,
                "entry_price": 100.0,
                "stop_zone": 98.0,
                "targets": "[106.0]",
                "round_trip_cost_pct": 0.5,
                "breakout_confirmed": i == 29,
            }
        )
    return pd.DataFrame(rows)


def test_arm_research_is_zero_allocation(tmp_path: Path):
    path = arm_paper_mode(_readiness(), "RESEARCH", tmp_path)
    state = load_arm_state(tmp_path)
    assert path.exists()
    assert state["armed"] is True
    assert state["allocation_pct"] == 0.0
    assert state["live_orders_enabled"] is False


def test_strategy_arm_fails_closed(tmp_path: Path):
    with pytest.raises(PermissionError):
        arm_paper_mode(_readiness(), "STRATEGY", tmp_path)


def test_disarmed_scan_records_nothing(tmp_path: Path):
    result = record_paper_observations(
        _paper_decisions(),
        _readiness(),
        output_dir=tmp_path,
        ledger_path=tmp_path / "paper.csv",
    )
    assert result.recorded == 0
    assert result.status == "BLOCKED_DISARMED"


def test_research_scan_records_virtual_observation_only(tmp_path: Path):
    arm_paper_mode(_readiness(), "RESEARCH", tmp_path)
    ledger = tmp_path / "paper.csv"
    result = record_paper_observations(
        _paper_decisions(),
        _readiness(),
        risk=PaperRiskConfig(max_signal_age_hours=8, max_open_trades=2),
        output_dir=tmp_path,
        ledger_path=ledger,
    )
    assert result.recorded == 1
    saved = pd.read_csv(ledger)
    assert saved.loc[0, "allocation_pct"] == 0.0
    assert str(saved.loc[0, "live_orders_enabled"]).lower() in {"false", "0"}
    assert saved.loc[0, "source"] == "paper_launch_v2"


def test_duplicate_and_symbol_risk_limits_are_enforced(tmp_path: Path):
    arm_paper_mode(_readiness(), "RESEARCH", tmp_path)
    ledger = tmp_path / "paper.csv"
    first = record_paper_observations(_paper_decisions(), _readiness(), output_dir=tmp_path, ledger_path=ledger)
    second = record_paper_observations(_paper_decisions(), _readiness(), output_dir=tmp_path, ledger_path=ledger)
    assert first.recorded == 1
    assert second.recorded == 0
    assert second.duplicates >= 1 or second.skipped >= 1
