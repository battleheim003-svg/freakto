from pathlib import Path

import pandas as pd

from engine.paper_performance_dashboard import (
    build_dashboard,
    build_equity_curve,
    build_regime_performance,
    merge_paper_ledger,
    summarize_performance,
)


def sample_frames():
    trades = pd.DataFrame([
        {"paper_trade_id":"a","entry_time":"2026-01-01T00:00:00Z","symbol":"BTC/USDT","side":"LONG","primary_event":"BREAKOUT_CONFIRMATION","status":"OPEN"},
        {"paper_trade_id":"b","entry_time":"2026-01-02T00:00:00Z","symbol":"ETH/USDT","side":"SHORT","primary_event":"VOLATILITY_EXPANSION","status":"OPEN"},
        {"paper_trade_id":"c","entry_time":"2026-01-03T00:00:00Z","symbol":"SOL/USDT","side":"LONG","primary_event":"BREAKOUT_CONFIRMATION","status":"OPEN"},
    ])
    evaluations = pd.DataFrame([
        {"paper_trade_id":"a","evaluated_at_utc":"2026-01-04T00:00:00Z","exit_time":"2026-01-04T00:00:00Z","status":"CLOSED","result":"WIN","net_r_multiple":2.0},
        {"paper_trade_id":"b","evaluated_at_utc":"2026-01-05T00:00:00Z","exit_time":"2026-01-05T00:00:00Z","status":"CLOSED","result":"LOSS","net_r_multiple":-1.0},
        {"paper_trade_id":"c","evaluated_at_utc":"2026-01-05T00:00:00Z","status":"OPEN","result":"OPEN","net_r_multiple":0.4},
    ])
    return trades, evaluations


def test_summary_metrics_are_net_r_based():
    ledger = merge_paper_ledger(*sample_frames())
    summary = summarize_performance(ledger)
    assert summary.total_signals == 3
    assert summary.closed_trades == 2
    assert summary.open_trades == 1
    assert summary.win_rate_pct == 50.0
    assert summary.profit_factor == 2.0
    assert summary.expectancy_r == 0.5
    assert summary.cumulative_r == 1.0
    assert summary.max_drawdown_r == 1.0


def test_equity_curve_uses_chronological_closed_trades_only():
    ledger = merge_paper_ledger(*sample_frames())
    curve = build_equity_curve(ledger)
    assert curve["paper_trade_id"].tolist() == ["a", "b"]
    assert curve["cumulative_r"].tolist() == [2.0, 1.0]
    assert curve["drawdown_r"].tolist() == [0.0, -1.0]


def test_regime_performance_is_joined_from_trade_metadata():
    ledger = merge_paper_ledger(*sample_frames())
    regimes = build_regime_performance(ledger)
    breakout = regimes[regimes["regime"] == "BREAKOUT_CONFIRMATION"].iloc[0]
    assert breakout["signals"] == 2
    assert breakout["closed"] == 1
    assert breakout["expectancy_r"] == 2.0


def test_latest_evaluation_wins_for_duplicate_trade_id():
    trades, evaluations = sample_frames()
    evaluations = pd.concat([evaluations, pd.DataFrame([{"paper_trade_id":"a","evaluated_at_utc":"2026-01-06T00:00:00Z","status":"CLOSED","result":"LOSS","net_r_multiple":-1.0}])], ignore_index=True)
    ledger = merge_paper_ledger(trades, evaluations)
    row = ledger[ledger["paper_trade_id"] == "a"].iloc[0]
    assert row["net_r"] == -1.0


def test_empty_dashboard_is_valid_and_writes_outputs(tmp_path: Path):
    trades = tmp_path / "trades.csv"
    evaluations = tmp_path / "evals.csv"
    output = tmp_path / "dashboard"
    summary, ledger, regimes, equity, outputs = build_dashboard(trades, evaluations, output, make_plot=False)
    assert summary.status == "NO_PAPER_TRADES"
    assert ledger.empty and regimes.empty and equity.empty
    assert Path(outputs["json"]).exists()
    assert Path(outputs["markdown"]).exists()


def test_dashboard_writes_csv_and_png(tmp_path: Path):
    trades, evaluations = sample_frames()
    trades_path = tmp_path / "trades.csv"
    evals_path = tmp_path / "evals.csv"
    trades.to_csv(trades_path, index=False)
    evaluations.to_csv(evals_path, index=False)
    summary, _ledger, _regimes, _equity, outputs = build_dashboard(trades_path, evals_path, tmp_path / "out")
    assert summary.closed_trades == 2
    for key in ("json", "markdown", "ledger", "regimes", "equity_csv", "equity_png"):
        assert Path(outputs[key]).exists()
