from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from engine.economic_calibration import build_economic_calibration, estimate_score_economics
from engine.evidence_quality import assess_evidence
from engine.market_narrative import _row_is_noise
from engine.portfolio_optimizer import build_portfolio_decision


class DecisionEconomicsTests(unittest.TestCase):
    def _calibration_frame(self) -> pd.DataFrame:
        rng = np.random.default_rng(11)
        rows = []
        for split, count in (("TRAIN_60", 900), ("VALIDATION_20", 350), ("TEST_20", 300)):
            for index in range(count):
                score = 50 + index % 40
                net = (score - 65) / 25.0 + float(rng.normal(0, 0.20))
                rows.append({
                    "run_id": "synthetic", "side": "LONG", "evaluation_status": "COMPLETE",
                    "replay_split": split, "score": score, "net_return_pct": net,
                    "entry_price": 100.0, "stop_zone": "98.0",
                })
        return pd.DataFrame(rows)

    def test_economic_calibration_uses_development_splits(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "replay.csv"
            self._calibration_frame().to_csv(path, index=False)
            artifact = build_economic_calibration(
                path, min_train_samples=500, min_validation_samples=100, min_band_samples=50
            )
        self.assertEqual(artifact.train_samples, 900)
        self.assertEqual(artifact.validation_samples, 350)
        self.assertTrue(artifact.usable_for_allocation)
        estimate = estimate_score_economics(75, artifact)
        self.assertGreater(estimate.historical_win_probability, 0.5)
        self.assertGreater(estimate.expected_r, 0)

    def test_evidence_requires_independence_relevance_and_agreement(self):
        weak = assess_evidence([
            {"source_id": "one", "source_tier": "TIER_1_OFFICIAL_MACRO", "direction": "BEARISH", "title": "unrelated bank administration"}
        ], claimed_direction="BEARISH")
        strong = assess_evidence([
            {"source_id": f"source_{index}", "source_tier": "TIER_1_OFFICIAL_MACRO", "direction": "BEARISH", "title": "Bitcoin liquidity and monetary policy"}
            for index in range(3)
        ], claimed_direction="BEARISH")
        self.assertIn(weak.claim_status, {"WEAK_HYPOTHESIS", "INSUFFICIENT_EVIDENCE"})
        self.assertEqual(strong.claim_status, "SUPPORTED_HYPOTHESIS")
        self.assertGreater(strong.strength, weak.strength)
        self.assertGreaterEqual(len(strong.alternative_explanations), 3)

    def test_example_event_is_never_evidence(self):
        is_noise, reason = _row_is_noise({"description": "Example: fake catalyst"})
        self.assertTrue(is_noise)
        self.assertIn("example", reason)

    def test_portfolio_stays_cash_without_validated_edge(self):
        returns = list(np.linspace(-0.01, 0.01, 90))
        item = SimpleNamespace(
            symbol="BTC/USDT", side="LONG", recommendation="ACTIONABLE",
            opportunity_score=80, historical_win_probability=0.40, expected_r=-0.10,
            calibration_usable=False, return_history=returns,
        )
        decision = build_portfolio_decision([item])
        self.assertEqual(decision.status, "PORTFOLIO_SHADOW_ONLY")
        self.assertEqual(decision.gross_allocation_pct, 0.0)
        self.assertEqual(decision.cash_allocation_pct, 100.0)
        self.assertGreater(decision.allocations[0].shadow_allocation_pct, 0.0)

    def test_portfolio_allocates_only_validated_positive_edge(self):
        rng = np.random.default_rng(5)
        items = []
        for symbol, expected_r in (("BTC/USDT", 0.25), ("ETH/USDT", 0.15)):
            items.append(SimpleNamespace(
                symbol=symbol, side="LONG", recommendation="ACTIONABLE",
                opportunity_score=75, historical_win_probability=0.60,
                expected_r=expected_r, calibration_usable=True,
                return_history=list(rng.normal(0, 0.01, 120)),
            ))
        decision = build_portfolio_decision(items)
        self.assertEqual(decision.status, "PORTFOLIO_ALLOCATION_READY_FOR_PAPER")
        self.assertAlmostEqual(decision.gross_allocation_pct, 75.0, places=1)
        self.assertAlmostEqual(sum(item.allocation_pct for item in decision.allocations), 75.0, places=1)


if __name__ == "__main__":
    unittest.main()
