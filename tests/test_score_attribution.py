from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from engine.score_attribution import (
    AttributionConfig,
    component_univariate_attribution,
    economics_summary,
    load_attribution_dataset,
    ridge_out_of_sample_attribution,
    score_band_performance,
    validate_component_columns,
)


COMPONENTS = [
    "trend_score",
    "momentum_score",
    "volume_score",
    "structure_score",
    "regime_score",
    "risk_penalty",
    "adaptive_adjustment",
]


def synthetic_frame(rows=600, seed=7):
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range("2024-01-01", periods=rows, freq="4h", tz="UTC")
    trend = rng.integers(0, 29, rows)
    momentum = rng.integers(2, 31, rows)
    volume = rng.integers(0, 19, rows)
    structure = rng.integers(0, 11, rows)
    regime = rng.integers(-8, 6, rows)
    risk = -rng.integers(0, 11, rows)
    adaptive = rng.integers(-4, 5, rows)
    noise = rng.normal(0, 0.25, rows)
    evaluated_return = 0.05 * trend - 0.08 * volume + 0.02 * momentum + noise
    score = trend + momentum + volume + structure + regime + risk + adaptive
    score = np.clip(score, 0, 100)
    return pd.DataFrame(
        {
            "decision_id": [f"d{i}" for i in range(rows)],
            "run_id": "market_replay_20260101_000000",
            "candle_timestamp": timestamps,
            "symbol": "BTC/USDT",
            "timeframe": "4h",
            "side": np.where(np.arange(rows) % 2 == 0, "LONG", "SHORT"),
            "score": score,
            "regime_label": np.where(np.arange(rows) % 3 == 0, "TRENDING_BULL", "TRENDING_BEAR"),
            "trend_score": trend,
            "momentum_score": momentum,
            "volume_score": volume,
            "structure_score": structure,
            "regime_score": regime,
            "risk_penalty": risk,
            "adaptive_adjustment": adaptive,
            "evaluated_return": evaluated_return,
            "win": evaluated_return > 0,
            "_event_time": timestamps,
            "_regime_group": np.where(np.arange(rows) % 3 == 0, "BULL", "BEAR"),
        }
    )


class ScoreAttributionTests(unittest.TestCase):
    def test_loader_selects_latest_run_and_filters_neutral(self):
        frame = synthetic_frame(120)
        older = frame.iloc[:60].copy()
        older["run_id"] = "market_replay_20260101_000000"
        newer = frame.iloc[60:].copy()
        newer["run_id"] = "market_replay_20260102_000000"
        neutral = newer.iloc[:2].copy()
        neutral["side"] = "NEUTRAL"
        raw = pd.concat([older, newer, neutral], ignore_index=True)
        raw["evaluation_status"] = "COMPLETE"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "replay.csv"
            raw.drop(columns=["evaluated_return"]).assign(
                net_signed_return_after_6c_pct=raw["evaluated_return"]
            ).to_csv(path, index=False)
            loaded, metadata, warnings = load_attribution_dataset(
                path,
                components=COMPONENTS,
            )
        self.assertEqual(metadata["selected_run_id"], "market_replay_20260102_000000")
        self.assertEqual(len(loaded), 60)
        self.assertTrue(all(loaded["side"].isin(["LONG", "SHORT"])))
        self.assertTrue(any("ignored" in warning for warning in warnings))

    def test_loader_rejects_reduced_dataset_without_components(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "reduced.csv"
            pd.DataFrame(
                {
                    "candle_timestamp": pd.date_range("2024-01-01", periods=3, tz="UTC"),
                    "side": ["LONG", "SHORT", "LONG"],
                    "score": [60, 70, 80],
                    "evaluated_return": [1.0, -1.0, 0.5],
                }
            ).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, "No score-component"):
                load_attribution_dataset(path)

    def test_outcome_columns_cannot_be_components(self):
        with self.assertRaisesRegex(ValueError, "leakage"):
            validate_component_columns(["trend_score", "net_return_after_6c_pct"])

    def test_ridge_recovers_supportive_and_harmful_components_on_holdout(self):
        frame = synthetic_frame(800)
        config = AttributionConfig(minimum_total_rows=200, minimum_scope_rows=50, ridge_alpha=1.0)
        table, metrics = ridge_out_of_sample_attribution(frame, COMPONENTS, config)
        trend = table.set_index("component").loc["trend_score"]
        volume = table.set_index("component").loc["volume_score"]
        self.assertGreater(trend["standardized_coefficient"], 0)
        self.assertLess(volume["standardized_coefficient"], 0)
        self.assertGreater(trend["permutation_mse_increase"], 0)
        self.assertGreater(volume["permutation_mse_increase"], 0)
        self.assertGreater(metrics["holdout_r2"], 0.5)

    def test_univariate_attribution_and_score_bands_cover_overall_scope(self):
        frame = synthetic_frame(500)
        config = AttributionConfig(minimum_total_rows=200, minimum_scope_rows=50, minimum_bin_rows=10)
        summary, bins = component_univariate_attribution(frame, COMPONENTS, config)
        bands = score_band_performance(frame, config)
        self.assertIn("ALL", summary["scope"].unique())
        self.assertIn("trend_score", summary["component"].unique())
        self.assertFalse(bins.empty)
        self.assertFalse(bands[bands["scope"].eq("ALL")].empty)

    def test_economics_computes_break_even_rate_from_payoff(self):
        frame = synthetic_frame(200)
        frame["evaluated_return"] = [1.0, -2.0] * 100
        frame["win"] = frame["evaluated_return"] > 0
        config = AttributionConfig(minimum_total_rows=100, minimum_scope_rows=50)
        table = economics_summary(frame, config)
        overall = table.set_index("scope").loc["ALL"]
        self.assertAlmostEqual(overall["break_even_win_rate"], 2 / 3, places=5)
        self.assertAlmostEqual(overall["actual_minus_break_even_win_rate"], -1 / 6, places=5)


if __name__ == "__main__":
    unittest.main()
