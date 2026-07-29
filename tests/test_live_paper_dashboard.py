from pathlib import Path

import pandas as pd

from engine.live_paper_dashboard import (
    DashboardData, equity_curve, excel_report, pdf_report,
    load_dashboard_data, open_positions, performance_attribution, regime_heatmap,
)


def _sample_data() -> DashboardData:
    fills = pd.DataFrame([
        {"timestamp_utc": "2026-07-20T00:00:00Z", "symbol": "BTC/USDT", "side": "BUY", "notional_usdt": 1000, "fee_usdt": 1, "equity_usdt": 9999},
        {"timestamp_utc": "2026-07-20T04:00:00Z", "symbol": "BTC/USDT", "side": "SELL", "notional_usdt": 1050, "fee_usdt": 1.05, "equity_usdt": 10048},
    ])
    intents = pd.DataFrame([
        {"regime": "TREND", "status": "SHADOW_CANDIDATE"},
        {"regime": "TREND", "status": "BLOCKED"},
    ])
    return DashboardData(
        mode="paper", root=Path("unused"),
        state={"metrics": {"unique_decisions": 2, "complete_4h_candles": 2, "unhandled_crashes": 0}},
        gate={"passed": True, "days": 7.1, "provider_freshness_pct": 100, "checks": {"minimum_days": True}},
        account={}, intents=intents, fills=fills, events=pd.DataFrame(),
    )


def test_equity_regime_and_attribution_views():
    data = _sample_data()
    curve = equity_curve(data)
    assert list(curve["equity_usdt"]) == [9999, 10048]
    assert curve.iloc[-1]["drawdown_pct"] == 0
    assert regime_heatmap(data).loc["TREND", "BLOCKED"] == 1
    result = performance_attribution(data).iloc[0]
    assert result["symbol"] == "BTC/USDT"
    assert round(result["net_cash_flow"], 2) == 47.95


def test_excel_and_pdf_reports_are_downloadable_files():
    data = _sample_data()
    assert excel_report(data).startswith(b"PK")
    assert pdf_report(data).startswith(b"%PDF")


def test_learning_dashboard_uses_separate_operational_root(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(
        '{"schema_version":1,"initial_balance_usdt":10000,"timeframe":"4h",'
        '"data_dir":"data","state_roots":{"shadow":"logs/shadow","paper":"logs/paper",'
        '"learning":"logs/learning"},"risk":{},"execution":{},"rollout":{},'
        '"shadow_gate":{"minimum_days":7,"minimum_unique_decisions":20,'
        '"minimum_complete_4h_candles":30,"maximum_duplicate_executions":0,'
        '"maximum_open_candle_decisions":0,"maximum_state_corruptions":0,'
        '"maximum_unhandled_crashes":0,"minimum_provider_freshness_pct":95},'
        '"notifications":{}}',
        encoding="utf-8",
    )
    operational = tmp_path / "operational"
    learning = operational / "logs" / "learning"
    learning.mkdir(parents=True)
    (learning / "runtime_state.json").write_text(
        '{"mode":"learning","evidence_scope":"LEARNING_ONLY","metrics":{}}',
        encoding="utf-8",
    )

    data = load_dashboard_data("learning", config, operational_root=operational)

    assert data.root == learning
    assert data.state["evidence_scope"] == "LEARNING_ONLY"


def test_open_positions_join_account_with_stop_and_target_controls():
    data = _sample_data()
    data.account.update(positions={"BTC/USDT": {"amount": 0.1, "average_entry": 65000}})
    data.state.update(
        evidence_scope="LEARNING_ONLY",
        managed_positions={
            "BTC/USDT": {
                "stop": 64000,
                "targets": [67000],
                "decision_id": "probe-1",
                "opened_at_utc": "2026-07-27T00:00:00Z",
            }
        },
    )

    row = open_positions(data).iloc[0]

    assert row["symbol"] == "BTC/USDT"
    assert row["stop"] == 64000
    assert row["targets"] == "67000"
    assert row["evidence_scope"] == "LEARNING_ONLY"
