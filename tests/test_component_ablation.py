import unittest
import tempfile

import numpy as np
import pandas as pd

from engine.component_ablation import (
    AblationConfig,
    ablated_score,
    run_component_ablation,
)


class ComponentAblationTests(unittest.TestCase):
    def test_ablated_score_removes_positive_component_points(self):
        frame = pd.DataFrame({"score": [70, 80], "trend_score": [20, 30]})
        self.assertEqual(ablated_score(frame, "trend_score").tolist(), [50, 50])

    def test_removing_negative_risk_penalty_increases_score(self):
        frame = pd.DataFrame({"score": [60, 75], "risk_penalty": [-10, -5]})
        self.assertEqual(ablated_score(frame, "risk_penalty").tolist(), [70, 80])

    def test_threshold_selection_uses_optimize_not_holdout(self):
        rows = 600
        timestamps = pd.date_range("2024-01-01", periods=rows, freq="4h", tz="UTC")
        score = np.full(rows, 75.0)
        returns = np.zeros(rows)
        returns[:360] = 0.1
        returns[360:474] = 1.0
        returns[480:] = -2.0
        frame = pd.DataFrame(
            {
                "_event_time": timestamps,
                "side": np.where(np.arange(rows) % 2 == 0, "LONG", "SHORT"),
                "_regime_group": "BULL",
                "score": score,
                "trend_score": np.full(rows, 20.0),
                "evaluated_return": returns,
            }
        )
        config = AblationConfig(
            minimum_total_rows=200,
            minimum_scope_rows=100,
            minimum_optimize_selected=20,
            minimum_holdout_selected=20,
            threshold_grid=(70,),
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            result, artifacts = run_component_ablation(
                frame,
                components=["trend_score"],
                output_dir=temp_dir,
                config=config,
            )
        full = artifacts.summary.query("scope == 'ALL' and variant == 'FULL'").iloc[0]
        self.assertEqual(full["selected_threshold"], 70)
        self.assertLess(full["optimized_expectancy"], 0)
        self.assertEqual(result.status, "COMPLETE")

    def test_harmful_component_is_flagged_when_removal_improves_holdout(self):
        rng = np.random.default_rng(3)
        rows = 800
        timestamps = pd.date_range("2024-01-01", periods=rows, freq="4h", tz="UTC")
        harmful = rng.integers(0, 31, rows)
        base = rng.integers(55, 76, rows)
        score = np.clip(base + harmful, 0, 100)
        returns = 1.0 - harmful * 0.12 + rng.normal(0, 0.05, rows)
        frame = pd.DataFrame(
            {
                "_event_time": timestamps,
                "side": np.where(np.arange(rows) % 2 == 0, "LONG", "SHORT"),
                "_regime_group": "BULL",
                "score": score,
                "volume_score": harmful,
                "evaluated_return": returns,
            }
        )
        config = AblationConfig(
            minimum_total_rows=200,
            minimum_scope_rows=100,
            minimum_optimize_selected=20,
            minimum_holdout_selected=20,
            effect_tolerance_pct=0.01,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            _, artifacts = run_component_ablation(
                frame,
                components=["volume_score"],
                output_dir=temp_dir,
                config=config,
            )
        row = artifacts.summary.query("scope == 'ALL' and removed_component == 'volume_score'").iloc[0]
        self.assertGreater(row["delta_fixed_expectancy_vs_full"], 0)
        self.assertEqual(row["diagnosis"], "REMOVAL_IMPROVES_BUT_NEGATIVE")

    def test_constant_component_is_inactive(self):
        rows = 400
        frame = pd.DataFrame(
            {
                "_event_time": pd.date_range("2024-01-01", periods=rows, freq="4h", tz="UTC"),
                "side": np.where(np.arange(rows) % 2 == 0, "LONG", "SHORT"),
                "_regime_group": "SIDEWAYS",
                "score": np.full(rows, 70.0),
                "historical_edge_score": np.zeros(rows),
                "evaluated_return": np.where(np.arange(rows) % 2 == 0, 1.0, -1.0),
            }
        )
        config = AblationConfig(
            minimum_total_rows=200,
            minimum_scope_rows=100,
            minimum_optimize_selected=20,
            minimum_holdout_selected=20,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            _, artifacts = run_component_ablation(
                frame,
                components=["historical_edge_score"],
                output_dir=temp_dir,
                config=config,
            )
        row = artifacts.summary.query("scope == 'ALL' and removed_component == 'historical_edge_score'").iloc[0]
        self.assertEqual(row["diagnosis"], "INACTIVE")


if __name__ == "__main__":
    unittest.main()
