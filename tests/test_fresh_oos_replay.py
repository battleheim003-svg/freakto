import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from engine.fresh_oos_replay import FreshOOSConfig, fixed_metrics, run_fresh_oos_pipeline


class FreshOOSReplayTests(unittest.TestCase):
    def test_fixed_metrics_are_deterministic_and_not_optimized(self):
        frame = pd.DataFrame({
            "candle_timestamp": pd.date_range("2024-01-01", periods=8, freq="4h", tz="UTC"),
            "net_return_pct": [1, -1, 2, -1, 1, -1, 2, -1],
        })
        result = fixed_metrics(frame)
        self.assertEqual(result.sample_count, 8)
        self.assertAlmostEqual(result.expectancy, 0.25)
        self.assertAlmostEqual(result.profit_factor, 1.5)
        self.assertEqual(result.total_time_folds, 4)

    def test_empty_metrics_fail_closed(self):
        result = fixed_metrics(pd.DataFrame())
        self.assertEqual(result.sample_count, 0)
        self.assertEqual(result.profit_factor, 0.0)

    def test_pipeline_waits_when_no_post_cutoff_rows_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            replay = Path(tmp) / "replay.csv"
            pd.DataFrame({
                "run_id": ["r1", "r1"],
                "candle_timestamp": ["2024-01-01T00:00:00Z", "2024-01-01T04:00:00Z"],
                "symbol": ["BTC/USDT", "BTC/USDT"],
                "timeframe": ["4h", "4h"],
                "provider": ["x", "x"],
                "side": ["LONG", "SHORT"],
                "score": [80, 80],
                "net_return_pct": [1.0, -1.0],
            }).to_csv(replay, index=False)
            config = FreshOOSConfig(
                development_replay_csv=str(replay),
                output_dir=str(Path(tmp) / "out"),
                symbols=["BTC/USDT"],
                timeframes=["4h"],
                min_fresh_directional_rows=1,
                min_rows_per_symbol=1,
                run_replay=False,
            )
            report = run_fresh_oos_pipeline(config)
            self.assertEqual(report.status, "READY_AWAITING_FRESH_DATA")
            self.assertFalse(report.promotion_applied)
            self.assertFalse(report.paper_live_enabled)

    def test_pipeline_uses_fixed_score_70_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            replay = Path(tmp) / "replay.csv"
            base = pd.DataFrame({
                "run_id": ["r1"],
                "candle_timestamp": ["2024-01-01T00:00:00Z"],
                "symbol": ["BTC/USDT"], "timeframe": ["4h"], "provider": ["x"],
                "side": ["LONG"], "score": [50], "net_return_pct": [-1.0],
            })
            base.to_csv(replay, index=False)
            fresh = pd.DataFrame({
                "run_id": ["fresh"] * 4,
                "candle_timestamp": pd.date_range("2024-01-02", periods=4, freq="4h", tz="UTC"),
                "feature_cutoff_timestamp": pd.date_range("2024-01-02", periods=4, freq="4h", tz="UTC"),
                "execution_timestamp": pd.date_range("2024-01-02 04:00", periods=4, freq="4h", tz="UTC"),
                "decision_id": [f"d{i}" for i in range(4)],
                "symbol": ["BTC/USDT"] * 4, "timeframe": ["4h"] * 4, "provider": ["x"] * 4,
                "side": ["LONG"] * 4, "score": [69, 70, 71, 90], "net_return_pct": [10, 1, 1, 1],
            })
            config = FreshOOSConfig(
                development_replay_csv=str(replay), output_dir=str(Path(tmp) / "out"),
                symbols=["BTC/USDT"], timeframes=["4h"], min_fresh_directional_rows=3,
                min_rows_per_symbol=1, run_replay=True,
            )
            with patch("engine.fresh_oos_replay._run_replay_after_cutoff", return_value=fresh), \
                 patch("engine.fresh_oos_replay._load_histories", return_value={}):
                report = run_fresh_oos_pipeline(config)
            self.assertEqual(report.fixed_gate["sample_count"], 3)
            self.assertEqual(report.fixed_threshold, 70.0)
            self.assertFalse(report.promotion_applied)

    def test_overlap_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            replay = Path(tmp) / "replay.csv"
            pd.DataFrame({
                "run_id": ["r1"], "candle_timestamp": ["2024-01-02T00:00:00Z"],
                "symbol": ["BTC/USDT"], "timeframe": ["4h"], "provider": ["x"],
                "side": ["LONG"], "score": [80], "net_return_pct": [-1.0],
            }).to_csv(replay, index=False)
            overlapping = pd.DataFrame({
                "run_id": ["fresh"], "candle_timestamp": ["2024-01-02T00:00:00Z"],
                "symbol": ["BTC/USDT"], "timeframe": ["4h"], "provider": ["x"],
                "side": ["LONG"], "score": [80], "net_return_pct": [10.0],
            })
            config = FreshOOSConfig(
                development_replay_csv=str(replay), output_dir=str(Path(tmp) / "out"),
                symbols=["BTC/USDT"], timeframes=["4h"], min_fresh_directional_rows=1,
                min_rows_per_symbol=1, run_replay=True,
            )
            with patch("engine.fresh_oos_replay._run_replay_after_cutoff", return_value=overlapping), \
                 patch("engine.fresh_oos_replay._load_histories", return_value={}):
                report = run_fresh_oos_pipeline(config)
            self.assertEqual(report.fresh_directional_rows, 0)
            self.assertTrue(any("overlap" in item for item in report.blockers))
