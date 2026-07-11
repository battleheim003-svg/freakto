import tempfile
import unittest
from pathlib import Path

import pandas as pd

from engine.replay_evaluation_recorder import backfill_replay_file, record_canonical_metrics
from engine.replay_real_metrics_evaluator import evaluate


class ReplayEvaluationRecorderTests(unittest.TestCase):
    def sample_frame(self):
        return pd.DataFrame([
            {
                "decision_id": "a", "side": "LONG", "score": 70, "timeframe": "4h",
                "replay_split": "TRAIN_60", "evaluation_status": "COMPLETE",
                "entry_price": 100.0, "market_return_after_6c_pct": 2.0,
                "gross_signed_return_after_6c_pct": 2.0,
                "net_signed_return_after_6c_pct": 1.7,
                "direction_correct_after_6c": True, "target_1_hit": True,
            },
            {
                "decision_id": "b", "side": "SHORT", "score": 80, "timeframe": "4h",
                "replay_split": "VALIDATION_20", "evaluation_status": "COMPLETE",
                "entry_price": 100.0, "market_return_after_6c_pct": 1.0,
                "gross_signed_return_after_6c_pct": -1.0,
                "net_signed_return_after_6c_pct": -1.3,
                "direction_correct_after_6c": False, "target_1_hit": False,
            },
            {
                "decision_id": "c", "side": "LONG", "score": 85, "timeframe": "4h",
                "replay_split": "TEST_20", "evaluation_status": "COMPLETE",
                "entry_price": 200.0, "market_return_after_6c_pct": 1.5,
                "gross_signed_return_after_6c_pct": 1.5,
                "net_signed_return_after_6c_pct": 1.2,
                "direction_correct_after_6c": True, "target_1_hit": True,
            },
        ])

    def test_records_canonical_fields(self):
        result, report = record_canonical_metrics(self.sample_frame())
        self.assertEqual(report.schema_status, "CANONICAL_METRICS_RECORDED")
        self.assertEqual(report.primary_horizon_candles, 6)
        self.assertEqual(report.rows_recorded, 3)
        self.assertAlmostEqual(float(result.iloc[0]["exit_price"]), 102.0)
        self.assertAlmostEqual(float(result.iloc[0]["net_return_pct"]), 1.7)
        self.assertEqual(result.iloc[0]["outcome_label"], "WIN")
        self.assertEqual(result.iloc[1]["outcome_label"], "LOSS")

    def test_apply_creates_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "replay.csv"
            self.sample_frame().to_csv(path, index=False)
            repaired, report = backfill_replay_file(path, apply=True)
            self.assertTrue(path.exists())
            self.assertTrue(Path(report.backup_file).exists())
            loaded = pd.read_csv(path)
            self.assertIn("net_return_pct", loaded.columns)

    def test_real_metrics_uses_actual_horizon_fields(self):
        result = evaluate(self.sample_frame())
        self.assertFalse(result["blockers"])
        self.assertEqual(result["schema_detected"]["net_return"], "net_return_pct")
        self.assertEqual(len(result["threshold_results"]), 6)


if __name__ == "__main__":
    unittest.main()
