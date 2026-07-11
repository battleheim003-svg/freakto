import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from engine.historical_data_store import HistoricalDataRequest, build_symbol_history, save_history
from engine.market_replay import (
    MarketReplayConfig,
    _evaluate_replay_path,
    attach_historical_context,
    run_market_replay,
)


class FakeExchange:
    def __init__(self, rows):
        self.rows = rows
        self.markets = {"BTC/USDT": {}}

    def load_markets(self):
        return self.markets

    def fetch_ohlcv(self, symbol, timeframe, since, limit):
        return [row for row in self.rows if row[0] >= since][:limit]

    def close(self):
        return None


class MarketReplayTests(unittest.TestCase):
    def test_paginated_history_build(self):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        timeframe_ms = 4 * 60 * 60 * 1000
        rows = []
        price = 100.0
        for index in range(300):
            timestamp = int(start.timestamp() * 1000) + index * timeframe_ms
            rows.append([timestamp, price, price + 2, price - 2, price + 1, 1000 + index])
            price += 1

        with tempfile.TemporaryDirectory() as temp_dir:
            request = HistoricalDataRequest(
                symbols=["BTC/USDT"],
                timeframe="4h",
                start_utc=start.isoformat(),
                end_utc=(start + timedelta(hours=4 * 299)).isoformat(),
                exchange="fake",
                batch_limit=50,
                data_dir=temp_dir,
            )
            with patch("engine.historical_data_store._write_quality"):
                result = build_symbol_history(
                    request,
                    "BTC/USDT",
                    exchange_factory=lambda _: FakeExchange(rows),
                )
            self.assertTrue(result.ok)
            self.assertEqual(result.rows, 300)
            self.assertEqual(result.quality.coverage_pct, 100.0)
            self.assertEqual(result.quality.gap_count, 0)

    def test_replay_is_no_lookahead_and_disables_persisted_learning(self):
        rng = np.random.default_rng(42)
        count = 360
        timestamps = pd.date_range("2023-01-01", periods=count, freq="4h", tz="UTC")
        returns = rng.normal(0.0002, 0.008, count)
        close = 20_000 * np.exp(np.cumsum(returns))
        open_price = np.r_[close[0], close[:-1]]
        high = np.maximum(open_price, close) * (1 + rng.uniform(0.001, 0.01, count))
        low = np.minimum(open_price, close) * (1 - rng.uniform(0.001, 0.01, count))
        volume = rng.lognormal(10, 0.4, count)
        frame = pd.DataFrame({
            "timestamp": timestamps,
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "provider": "synthetic",
        })

        with tempfile.TemporaryDirectory() as temp_dir:
            save_history(frame, "BTC/USDT", "4h", temp_dir)
            config = MarketReplayConfig(
                symbols=["BTC/USDT"],
                timeframe="4h",
                data_dir=temp_dir,
                min_window=120,
                step=12,
                max_decisions_per_symbol=10,
                strict_leakage_audit=True,
            )
            run, summary, rows = run_market_replay(config, save=False)
            self.assertTrue(run.ok)
            self.assertEqual(summary.leakage_audit_status, "PASSED_NO_LOOKAHEAD")
            self.assertFalse(rows.empty)
            self.assertTrue(rows["replay_safe"].astype(bool).all())
            self.assertFalse(rows["learning_overrides_enabled"].astype(bool).any())
            self.assertFalse(rows["historical_edge_enabled"].astype(bool).any())
            self.assertTrue((pd.to_numeric(rows["historical_edge_score"]) == 0).all())
            self.assertTrue(rows["dynamic_execution_costs"].astype(bool).all())
            self.assertTrue((rows["execution_price_basis"] == "NEXT_AVAILABLE_BAR_OPEN").all())
            self.assertTrue((pd.to_datetime(rows["execution_timestamp"]) > pd.to_datetime(rows["candle_timestamp"])).all())
            self.assertTrue(rows["feature_set_version"].astype(str).str.len().gt(0).all())

    def test_historical_context_uses_backward_only_merge(self):
        market = pd.DataFrame({
            "timestamp": pd.to_datetime(["2024-01-01T04:00:00Z", "2024-01-01T08:00:00Z"]),
            "open": [100, 101], "high": [102, 103], "low": [99, 100],
            "close": [101, 102], "volume": [10, 11],
        })
        context = pd.DataFrame({
            "timestamp": pd.to_datetime(["2024-01-01T02:00:00Z", "2024-01-01T10:00:00Z"]),
            "symbol": ["BTC/USDT", "BTC/USDT"],
            "news_sentiment_score": [0.4, -0.9],
        })
        merged, matched = attach_historical_context(
            market, context, symbol="BTC/USDT", max_age_hours=24
        )
        self.assertEqual(matched, 2)
        self.assertEqual(float(merged.iloc[0]["news_sentiment_score"]), 0.4)
        self.assertEqual(float(merged.iloc[1]["news_sentiment_score"]), 0.4)

    def test_intrabar_stop_target_ambiguity_is_conservative(self):
        frame = pd.DataFrame({
            "timestamp": pd.to_datetime(["2024-01-01T00:00:00Z", "2024-01-01T04:00:00Z"]),
            "open": [100, 100], "high": [101, 106], "low": [99, 94],
            "close": [100, 101], "volume": [10, 10],
        })
        frame.attrs["timeframe"] = "4h"
        result = _evaluate_replay_path(
            frame, signal_idx=0, side="LONG", entry_price=100, stop_price=95,
            targets=[105], horizons=[1], fee_bps_per_side=0, slippage_bps_per_side=0
        )
        self.assertTrue(result["intrabar_ambiguity"])
        self.assertEqual(result["first_exit_reason"], "STOP_FIRST_CONSERVATIVE_AMBIGUOUS")
        self.assertTrue(result["target_1_hit"])
        self.assertTrue(result["stop_hit"])


if __name__ == "__main__":
    unittest.main()
