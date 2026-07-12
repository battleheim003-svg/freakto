from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from engine.expectancy_challenger import (
    ChallengerConfig,
    ChallengerVariant,
    ExpectancyChallenger,
    build_feature_frame,
    expected_value_pct,
    validate_feature_columns,
)


def synthetic_frame(count: int = 600, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    side = np.where(np.arange(count) % 2 == 0, "LONG", "SHORT")
    trend = rng.integers(0, 29, count)
    momentum = rng.integers(0, 31, count)
    volume = rng.integers(0, 21, count)
    structure = rng.integers(0, 13, count)
    regime_score = rng.choice([-8, -5, -4, -2, 5], count)
    risk = -rng.integers(0, 16, count)
    adaptive = rng.integers(-6, 7, count)
    latent = (
        -0.7
        + 0.045 * trend
        + 0.055 * volume
        + 0.035 * regime_score
        + 0.025 * adaptive
        + 0.020 * risk
        - 0.020 * np.maximum(momentum - 20, 0)
    )
    probability = 1.0 / (1.0 + np.exp(-latent))
    wins = rng.random(count) < probability
    win_magnitude = np.clip(0.8 + trend * 0.02 + volume * 0.015 + rng.normal(0, 0.2, count), 0.1, None)
    loss_magnitude = np.clip(0.9 + np.abs(risk) * 0.025 + rng.normal(0, 0.2, count), 0.1, None)
    evaluated = np.where(wins, win_magnitude, -loss_magnitude)
    regimes = np.where(regime_score == 5, "BULL", np.where(regime_score == -8, "BEAR", "QUIET"))
    return pd.DataFrame(
        {
            "side": side,
            "evaluated_return": evaluated,
            "trend_score": trend,
            "momentum_score": momentum,
            "volume_score": volume,
            "structure_score": structure,
            "regime_score": regime_score,
            "risk_penalty": risk,
            "external_context_score": 0,
            "adaptive_adjustment": adaptive,
            "historical_edge_score": 0,
            "_regime_group": regimes,
        }
    )


class ExpectancyChallengerTests(unittest.TestCase):
    def test_expected_value_formula_includes_costs(self):
        value = expected_value_pct(
            0.60,
            2.0,
            1.0,
            execution_cost_pct=0.10,
            risk_cost_pct=0.05,
        )
        self.assertAlmostEqual(value, 0.65, places=8)

    def test_outcome_columns_are_rejected_as_features(self):
        with self.assertRaises(ValueError):
            validate_feature_columns(["trend_score", "future_return_after_6c"])

    def test_momentum_is_capped_or_removed_by_variant(self):
        frame = synthetic_frame(10)
        frame["momentum_score"] = 99
        config = ChallengerConfig(momentum_cap=20)
        with_momentum = build_feature_frame(
            frame,
            ChallengerVariant("WITH_MOMENTUM", include_momentum=True),
            config,
        )
        without_momentum = build_feature_frame(
            frame,
            ChallengerVariant("NO_MOMENTUM", include_momentum=False),
            config,
        )
        self.assertTrue((with_momentum["momentum_capped"] == 20).all())
        self.assertNotIn("momentum_capped", without_momentum.columns)
        self.assertNotIn("structure_score", with_momentum.columns)

    def test_fit_fails_closed_when_side_support_is_too_small(self):
        frame = synthetic_frame(40)
        model = ExpectancyChallenger(
            ChallengerVariant("BASE"),
            ChallengerConfig(
                minimum_side_train_rows=100,
                minimum_class_rows=5,
                minimum_payoff_rows=5,
            ),
        )
        summary = model.fit(frame)
        self.assertEqual(summary.status, "FAIL_CLOSED")
        predictions = model.predict(frame.head(4))
        self.assertFalse(predictions["model_available"].any())
        self.assertTrue(predictions["shadow_only"].all())
        self.assertFalse(predictions["paper_live_enabled"].any())

    def test_predictions_are_shadow_only_and_structure_volume_fail_closed(self):
        frame = synthetic_frame(800)
        model = ExpectancyChallenger(
            ChallengerVariant("STRUCTURE_GATE", structure_gate=True),
            ChallengerConfig(
                minimum_side_train_rows=200,
                minimum_class_rows=30,
                minimum_payoff_rows=25,
                minimum_volume_score=5,
                minimum_structure_score=6,
            ),
        )
        summary = model.fit(frame.iloc[:700])
        self.assertEqual(summary.status, "READY")
        test = frame.iloc[700:704].copy()
        test["volume_score"] = [4, 10, 10, 10]
        test["structure_score"] = [10, 5, 10, 10]
        predictions = model.predict(test)
        self.assertTrue(predictions["shadow_only"].all())
        self.assertFalse(predictions["paper_live_enabled"].any())
        self.assertIn("VOLUME_CONFIRMATION_FAILED", predictions.iloc[0]["shadow_blockers"])
        self.assertIn("STRUCTURE_GATE_FAILED", predictions.iloc[1]["shadow_blockers"])
        self.assertTrue(np.isfinite(predictions.iloc[2]["predicted_expected_value_pct"]))

    def test_disabled_short_side_is_never_available(self):
        frame = synthetic_frame(800)
        model = ExpectancyChallenger(
            ChallengerVariant("LONG_ONLY", structure_gate=True, allowed_sides=("LONG",)),
            ChallengerConfig(
                minimum_side_train_rows=150,
                minimum_class_rows=20,
                minimum_payoff_rows=20,
            ),
        )
        model.fit(frame.iloc[:700])
        short_row = frame[frame["side"].eq("SHORT")].iloc[[0]]
        prediction = model.predict(short_row).iloc[0]
        self.assertFalse(prediction["model_available"])
        self.assertFalse(prediction["base_gate_passed"])
        self.assertIn("SIDE_DISABLED", prediction["shadow_blockers"])


if __name__ == "__main__":
    unittest.main()
