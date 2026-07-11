from __future__ import annotations

import unittest

import pandas as pd

from engine.replay_score_calibration import run_replay_score_calibration


class ReplayScoreCalibrationTests(unittest.TestCase):
    def _frame(self, inverse: bool = False) -> pd.DataFrame:
        rows = []
        for split, count in (("TRAIN_60", 240), ("VALIDATION_20", 100), ("TEST_20", 100)):
            for i in range(count):
                score = 50 + (i % 40)
                direction = -1 if inverse else 1
                net = direction * (score - 70) / 50.0
                rows.append({
                    "side": "LONG",
                    "score": score,
                    "long_score": score,
                    "short_score": 0,
                    "trend_score": score / 4,
                    "momentum_score": score / 5,
                    "volume_score": i % 15,
                    "structure_score": i % 12,
                    "regime_score": 5,
                    "risk_penalty": 0,
                    "regime_confidence": 75,
                    "replay_split": split,
                    "evaluation_status": "COMPLETE",
                    "gross_signed_return_after_6c_pct": net + 0.3,
                    "net_signed_return_after_6c_pct": net,
                    "market_return_after_6c_pct": net + 0.3,
                    "direction_correct_after_6c": net > 0,
                    "symbol": "BTC/USDT",
                    "regime_label": "TRENDING_BULL",
                })
        return pd.DataFrame(rows)

    def test_monotonic_score_is_detected(self) -> None:
        frame = self._frame(inverse=False)
        path = "/tmp/freakto_score_calibration_positive.csv"
        frame.to_csv(path, index=False)
        result = run_replay_score_calibration(path)
        self.assertFalse(result["blockers"])
        self.assertIn(result["score_calibration"]["verdict"], {"SCORE_MONOTONIC_RESEARCH_SIGNAL", "SCORE_WEAK_OR_NON_MONOTONIC"})
        self.assertGreater(result["rows_analyzed"], 0)

    def test_inverse_score_is_detected(self) -> None:
        frame = self._frame(inverse=True)
        path = "/tmp/freakto_score_calibration_inverse.csv"
        frame.to_csv(path, index=False)
        result = run_replay_score_calibration(path)
        self.assertEqual(result["score_calibration"]["verdict"], "SCORE_INVERTED_OR_MISCALIBRATED")

    def test_missing_file_is_blocked(self) -> None:
        result = run_replay_score_calibration("/tmp/does_not_exist_replay.csv")
        self.assertEqual(result["status"], "SCORE_CALIBRATION_BLOCKED")
        self.assertTrue(result["blockers"])


if __name__ == "__main__":
    unittest.main()
