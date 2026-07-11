from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from engine.execution_model import adaptive_horizon, estimate_execution_cost
from engine.experiment_registry import ExperimentRegistry
from engine.market_data_contract import keep_closed_candles_only
from engine.meta_labeling import run_meta_label_validation
from engine.paper_trading import _evaluate_one_trade
from engine.research_validation import benjamini_hochberg


class ResearchSafetyTests(unittest.TestCase):
    def test_incomplete_bar_is_removed(self):
        frame = pd.DataFrame({
            "timestamp": pd.to_datetime(["2024-01-01T00:00:00Z", "2024-01-01T04:00:00Z"]),
            "open": [1, 1], "high": [2, 2], "low": [0.5, 0.5], "close": [1, 1], "volume": [1, 1],
        })
        closed, removed = keep_closed_candles_only(
            frame, "4h", now=datetime(2024, 1, 1, 6, tzinfo=timezone.utc)
        )
        self.assertEqual(len(closed), 1)
        self.assertEqual(removed, 1)
        self.assertTrue(closed.attrs["closed_candles_only"])

    def test_dynamic_cost_is_never_better_than_base(self):
        base = estimate_execution_cost(
            {"atr_pct": 0.01, "cross_exchange_volume_ratio": 1.0},
            fee_bps_per_side=10, base_slippage_bps_per_side=5,
        )
        stressed = estimate_execution_cost(
            {"atr_pct": 0.05, "cross_exchange_volume_ratio": 0.4},
            fee_bps_per_side=10, base_slippage_bps_per_side=5,
        )
        self.assertGreater(stressed.slippage_bps_per_side, base.slippage_bps_per_side)
        self.assertEqual(adaptive_horizon(6, "TRENDING_BULL"), 12)
        self.assertEqual(adaptive_horizon(6, "SIDEWAYS"), 3)

    def test_holdout_claim_is_atomic_and_one_shot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = ExperimentRegistry(Path(temp_dir) / "registry.sqlite3")
            registry.start_run("a", "CALIBRATION")
            registry.start_run("b", "CALIBRATION")
            self.assertTrue(registry.claim_holdout("dataset", "family", "a"))
            self.assertFalse(registry.claim_holdout("dataset", "family", "b"))

    def test_bh_adjustment_is_monotonic_in_rank(self):
        q = benjamini_hochberg([0.001, 0.02, 0.9])
        self.assertLessEqual(q[0], q[1])
        self.assertLessEqual(q[1], q[2])

    def test_meta_label_threshold_is_selected_before_test(self):
        rng = np.random.default_rng(7)
        rows = []
        for split, count in (("TRAIN_60", 120), ("VALIDATION_20", 50), ("TEST_20", 50)):
            for index in range(count):
                score = float(rng.uniform(0, 100))
                outcome = (score - 50.0) / 50.0 + float(rng.normal(0, 0.25))
                rows.append({
                    "side": "LONG", "score": score, "trend_score": score / 4,
                    "momentum_score": score / 5, "volume_score": score / 8,
                    "structure_score": score / 10, "regime_score": 1,
                    "risk_penalty": 0, "regime_confidence": 70,
                    "normalized_net_return": outcome, "replay_split": split,
                })
        report = run_meta_label_validation(pd.DataFrame(rows), min_samples=120)
        self.assertFalse(report["blockers"])
        self.assertIn("selected_threshold_from_validation", report)
        self.assertEqual(report["test_samples"], 50)

    def test_paper_evaluation_reports_net_of_cost_r(self):
        market = pd.DataFrame({
            "timestamp": pd.to_datetime(["2024-01-01T00:00:00Z", "2024-01-01T04:00:00Z"]),
            "open": [100, 100], "high": [101, 111], "low": [99, 99],
            "close": [100, 110], "volume": [1000, 1000],
        }).set_index("timestamp")
        trade = {
            "paper_trade_id": "x", "entry_time": "2024-01-01T00:00:00Z",
            "symbol": "BTC/USDT", "timeframe": "4h", "side": "LONG",
            "entry": 100, "stop": 95, "target_1": 110,
            "fee_bps_per_side": 10, "base_slippage_bps_per_side": 5,
            "dynamic_execution_costs": True,
        }
        result = _evaluate_one_trade(trade, market)
        self.assertEqual(result["result"], "WIN")
        self.assertGreater(result["gross_r_multiple"], result["net_r_multiple"])
        self.assertEqual(result["r_multiple"], result["net_r_multiple"])


if __name__ == "__main__":
    unittest.main()
