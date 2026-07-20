from pathlib import Path

import pandas as pd

from engine.live_paper_dashboard import (
    DashboardData, equity_curve, excel_report, pdf_report,
    performance_attribution, regime_heatmap,
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
