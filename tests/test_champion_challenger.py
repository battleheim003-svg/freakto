from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from engine.champion_challenger import (
    ChampionChallengerConfig,
    apply_challenger_threshold,
    champion_mask,
    chronological_three_way_split,
    run_champion_challenger,
    select_expected_value_threshold,
)
from engine.expectancy_challenger import ChallengerConfig, ChallengerVariant


def canonical_frame(count: int = 1200, seed: int = 11, negative_edge: bool = True) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    timestamp = pd.date_range("2023-01-01", periods=count, freq="4h", tz="UTC")
    side = np.where(np.arange(count) % 2 == 0, "LONG", "SHORT")
    trend = rng.integers(10, 29, count)
    momentum = rng.integers(10, 31, count)
    volume = rng.integers(0, 21, count)
    structure = rng.integers(0, 13, count)
    regime_score = rng.choice([-8, -5, -4, -2, 5], count)
    risk = -rng.integers(0, 16, count)
    adaptive = rng.integers(-6, 7, count)
    if negative_edge:
        returns = rng.normal(-0.15, 1.0, count)
    else:
        latent = 0.03 * trend + 0.05 * volume + 0.02 * risk - 0.8
        probability = 1 / (1 + np.exp(-latent))
        wins = rng.random(count) < probability
        returns = np.where(wins, rng.uniform(0.7, 1.8, count), -rng.uniform(0.5, 1.2, count))
    score = np.clip(trend + momentum + volume + structure + regime_score + risk + adaptive, 0, 100)
    regime = np.where(regime_score == 5, "TRENDING_BULL", np.where(regime_score == -8, "TRENDING_BEAR", "QUIET"))
    frame = pd.DataFrame(
        {
            "run_id": "market_replay_test",
            "decision_id": [f"d-{index}" for index in range(count)],
            "candle_timestamp": timestamp,
            "symbol": np.where(np.arange(count) % 3 == 0, "BTC/USDT", "ETH/USDT"),
            "timeframe": "4h",
            "side": side,
            "score": score,
            "regime_label": regime,
            "trend_score": trend,
            "momentum_score": momentum,
            "volume_score": volume,
            "structure_score": structure,
            "regime_score": regime_score,
            "risk_penalty": risk,
            "external_context_score": 0,
            "adaptive_adjustment": adaptive,
            "historical_edge_score": 0,
            "evaluation_status": "COMPLETE",
            "net_signed_return_after_6c_pct": returns,
            "replay_safe": True,
            "learning_overrides_enabled": False,
            "historical_edge_enabled": False,
        }
    )
    frame["evaluated_return"] = returns
    frame["_event_time"] = timestamp
    frame["win"] = returns > 0
    frame["_regime_group"] = frame["regime_label"].replace(
        {"TRENDING_BULL": "BULL", "TRENDING_BEAR": "BEAR"}
    )
    frame["_row_order"] = np.arange(count)
    return frame


class ChampionChallengerTests(unittest.TestCase):
    def test_chronological_split_purges_boundaries(self):
        frame = canonical_frame(1000)
        config = ChampionChallengerConfig(
            minimum_total_rows=300,
            train_ratio=0.6,
            optimize_ratio=0.2,
            purge_rows=6,
        )
        train, optimize, holdout, summaries = chronological_three_way_split(frame, config)
        self.assertEqual(len(train), 594)
        self.assertEqual(len(optimize), 194)
        self.assertEqual(len(holdout), 200)
        self.assertLess(train["_event_time"].max(), optimize["_event_time"].min())
        self.assertLess(optimize["_event_time"].max(), holdout["_event_time"].min())
        self.assertEqual([item.name for item in summaries], ["train", "optimize", "holdout"])

    def test_split_never_places_same_timestamp_in_multiple_parts(self):
        frame = canonical_frame(600)
        duplicated = pd.concat([frame, frame.assign(symbol="SOL/USDT")], ignore_index=True)
        duplicated["_row_order"] = np.arange(len(duplicated))
        config = ChampionChallengerConfig(
            minimum_total_rows=300, train_ratio=0.6, optimize_ratio=0.2, purge_rows=6
        )
        train, optimize, holdout, _ = chronological_three_way_split(duplicated, config)
        train_times = set(train["_event_time"])
        optimize_times = set(optimize["_event_time"])
        holdout_times = set(holdout["_event_time"])
        self.assertFalse(train_times & optimize_times)
        self.assertFalse(optimize_times & holdout_times)
        self.assertFalse(train_times & holdout_times)

    def test_champion_mask_uses_existing_technical_contract(self):
        frame = canonical_frame(2)
        frame.loc[:, "score"] = [80, 80]
        frame.loc[:, "trend_score"] = [25, 25]
        frame.loc[:, "momentum_score"] = [20, 20]
        frame.loc[:, "volume_score"] = [8, 8]
        frame.loc[:, "structure_score"] = [8, 2]
        frame.loc[:, "risk_penalty"] = [-2, -2]
        frame.loc[:, "_regime_group"] = ["BULL", "BULL"]
        mask = champion_mask(frame, ChampionChallengerConfig(minimum_total_rows=1))
        self.assertEqual(mask.tolist(), [True, False])

    def test_expected_value_threshold_is_selected_on_optimize_only(self):
        optimize = pd.DataFrame({"evaluated_return": [1.0, 1.0, -2.0, -2.0]})
        predictions = pd.DataFrame(
            {
                "shadow_only": True,
                "paper_live_enabled": False,
                "model_available": True,
                "base_gate_passed": True,
                "predicted_expected_value_pct": [0.3, 0.3, 0.1, 0.1],
            }
        )
        config = ChampionChallengerConfig(
            minimum_total_rows=1,
            minimum_optimize_selected=2,
            minimum_holdout_selected=2,
            minimum_profit_factor=1.0,
            threshold_grid=(0.0, 0.2),
        )
        threshold, candidates = select_expected_value_threshold(
            optimize,
            predictions,
            config,
            variant_name="TEST",
        )
        self.assertEqual(threshold, 0.2)
        self.assertTrue(candidates.iloc[0]["viable"])
        # A hypothetical Holdout mutation cannot affect this Optimize-only call.
        optimize_copy = optimize.copy()
        threshold_again, _ = select_expected_value_threshold(
            optimize_copy,
            predictions,
            config,
            variant_name="TEST",
        )
        self.assertEqual(threshold_again, threshold)

    def test_threshold_requires_shadow_safety_flags(self):
        predictions = pd.DataFrame(
            {
                "shadow_only": [True, True, False],
                "paper_live_enabled": [False, True, False],
                "model_available": [True, True, True],
                "base_gate_passed": [True, True, True],
                "predicted_expected_value_pct": [0.5, 0.5, 0.5],
            }
        )
        self.assertEqual(apply_challenger_threshold(predictions, 0.1).tolist(), [True, False, False])

    def test_full_run_is_fail_closed_and_writes_research_artifacts(self):
        raw = canonical_frame(1600, negative_edge=True).drop(
            columns=["evaluated_return", "_event_time", "win", "_regime_group", "_row_order"]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "replay.csv"
            output = Path(temp_dir) / "out"
            raw.to_csv(source, index=False)
            config = ChampionChallengerConfig(
                minimum_total_rows=600,
                minimum_optimize_selected=20,
                minimum_holdout_selected=25,
                minimum_side_holdout=5,
                walk_forward_folds=1,
                minimum_positive_holdout_quarters=1,
                threshold_grid=(0.0, 0.1, 0.2, 0.3),
            )
            challenger_config = ChallengerConfig(
                minimum_side_train_rows=150,
                minimum_class_rows=30,
                minimum_payoff_rows=25,
            )
            result, artifacts = run_champion_challenger(
                source,
                output_dir=output,
                variants=(ChallengerVariant("TEST_BASE"),),
                config=config,
                challenger_config=challenger_config,
            )
            self.assertFalse(result.promotion_applied)
            self.assertFalse(result.paper_live_enabled)
            self.assertTrue(result.shadow_only)
            self.assertIn(result.status, {"FAIL", "PASS_RESEARCH_ONLY"})
            self.assertTrue((output / "champion_challenger_report.json").exists())
            self.assertTrue((output / "challenger_holdout_shadow_predictions.csv").exists())
            self.assertFalse(artifacts.summary.empty)
            self.assertTrue((artifacts.holdout_predictions["shadow_only"] == True).all())
            self.assertTrue((artifacts.holdout_predictions["paper_live_enabled"] == False).all())


if __name__ == "__main__":
    unittest.main()
