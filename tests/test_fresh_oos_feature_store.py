import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from engine.fresh_oos_feature_store import (
    CostProfileRegistry,
    OUTCOME_ONLY_COLUMNS,
    build_feature_store_v2,
    freeze_development_dataset,
    load_freeze_manifest,
    strictly_fresh_rows,
    verify_frozen_source_unchanged,
)


def history(count=40):
    ts = pd.date_range("2024-01-01", periods=count, freq="4h", tz="UTC")
    close = np.linspace(100, 120, count)
    return pd.DataFrame({
        "timestamp": ts,
        "open": close - 0.2,
        "high": close + 1.0,
        "low": close - 1.0,
        "close": close,
        "volume": np.linspace(1000, 2000, count),
        "provider": "synthetic",
    })


def replay_row(hist, cutoff_idx=20):
    return pd.DataFrame([{
        "run_id": "fresh_run",
        "decision_id": "d1",
        "candle_timestamp": hist.iloc[cutoff_idx]["timestamp"].isoformat(),
        "feature_cutoff_timestamp": hist.iloc[cutoff_idx]["timestamp"].isoformat(),
        "execution_timestamp": hist.iloc[cutoff_idx + 1]["timestamp"].isoformat(),
        "symbol": "BTC/USDT",
        "timeframe": "4h",
        "provider": "synthetic",
        "side": "LONG",
        "score": 75,
        "entry_price": float(hist.iloc[cutoff_idx + 1]["open"]),
        "stop_zone": "105",
        "targets": json.dumps([115, 118]),
        "fee_bps_per_side": 10,
        "slippage_bps_per_side": 5,
        "net_return_pct": 99.0,
        "win": True,
    }])


class FreshOOSFeatureStoreTests(unittest.TestCase):
    def test_freeze_creates_hash_verified_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "replay.csv"
            frame = pd.DataFrame({
                "run_id": ["r1", "r1"],
                "candle_timestamp": ["2024-01-01T00:00:00Z", "2024-01-01T04:00:00Z"],
                "symbol": ["BTC/USDT", "BTC/USDT"],
                "timeframe": ["4h", "4h"],
                "provider": ["x", "x"],
                "side": ["LONG", "SHORT"],
            })
            frame.to_csv(source, index=False)
            manifest = freeze_development_dataset(source, Path(tmp) / "freeze")
            loaded = load_freeze_manifest(Path(tmp) / "freeze" / "development_freeze_manifest.json")
            self.assertEqual(manifest.dataset_id, loaded.dataset_id)
            self.assertEqual(manifest.row_count, 2)
            self.assertTrue(verify_frozen_source_unchanged(manifest))

    def test_source_mutation_is_detected_but_snapshot_stays_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "replay.csv"
            pd.DataFrame({
                "run_id": ["r1"], "candle_timestamp": ["2024-01-01T00:00:00Z"],
                "symbol": ["BTC/USDT"], "timeframe": ["4h"], "provider": ["x"], "side": ["LONG"],
            }).to_csv(source, index=False)
            manifest = freeze_development_dataset(source, Path(tmp) / "freeze")
            source.write_text(source.read_text() + "\n", encoding="utf-8")
            self.assertFalse(verify_frozen_source_unchanged(manifest))
            load_freeze_manifest(Path(tmp) / "freeze" / "development_freeze_manifest.json", verify=True)

    def test_strictly_fresh_rows_excludes_cutoff(self):
        frame = pd.DataFrame({
            "candle_timestamp": ["2024-01-01T00:00:00Z", "2024-01-01T04:00:00Z"]
        })
        fresh = strictly_fresh_rows(frame, "2024-01-01T00:00:00Z")
        self.assertEqual(len(fresh), 1)
        self.assertIn("04:00:00", fresh.iloc[0]["candle_timestamp"])

    def test_feature_and_outcome_tables_are_separated(self):
        hist = history()
        with tempfile.TemporaryDirectory() as tmp:
            result = build_feature_store_v2(
                replay_row(hist), {("BTC/USDT", "4h"): hist}, tmp, max_path_candles=5
            )
            features = pd.read_csv(result.feature_file)
            paths = pd.read_csv(result.path_file)
            self.assertEqual(result.status, "COMPLETE")
            self.assertEqual(len(features), 1)
            self.assertEqual(len(paths), 5)
            self.assertFalse(OUTCOME_ONLY_COLUMNS.intersection(features.columns))
            self.assertIn("net_signed_return_pct", paths.columns)
            self.assertFalse(bool(features.iloc[0]["retuning_allowed"]))

    def test_future_mutation_does_not_change_entry_features(self):
        hist = history()
        replay = replay_row(hist)
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            first = build_feature_store_v2(replay, {("BTC/USDT", "4h"): hist}, tmp1, max_path_candles=3)
            mutated = hist.copy()
            mutated.loc[mutated.index > 21, "close"] += 1000
            second = build_feature_store_v2(replay, {("BTC/USDT", "4h"): mutated}, tmp2, max_path_candles=3)
            f1 = pd.read_csv(first.feature_file)
            f2 = pd.read_csv(second.feature_file)
            feature_cols = [c for c in f1.columns if c.startswith("feature_")]
            pd.testing.assert_series_equal(f1.loc[0, feature_cols], f2.loc[0, feature_cols], check_names=False)
            p1 = pd.read_csv(first.path_file)
            p2 = pd.read_csv(second.path_file)
            self.assertFalse(p1["close"].equals(p2["close"]))

    def test_same_candle_target_stop_is_flagged_conservatively(self):
        hist = history()
        replay = replay_row(hist)
        replay.loc[0, "stop_zone"] = "109"
        replay.loc[0, "targets"] = json.dumps([112])
        hist.loc[22, "low"] = 108
        hist.loc[22, "high"] = 113
        with tempfile.TemporaryDirectory() as tmp:
            result = build_feature_store_v2(replay, {("BTC/USDT", "4h"): hist}, tmp, max_path_candles=2)
            paths = pd.read_csv(result.path_file)
            ambiguous = paths[paths["same_candle_ambiguity"].astype(bool)]
            self.assertEqual(len(ambiguous), 1)
            self.assertEqual(ambiguous.iloc[0]["first_exit_reason_so_far"], "STOP_FIRST_CONSERVATIVE_AMBIGUOUS")

    def test_recorded_cost_has_priority_over_fallback(self):
        registry = CostProfileRegistry()
        recorded = registry.resolve("okx", "BTC/USDT", recorded_fee_bps=3, recorded_slippage_bps=2)
        fallback = registry.resolve("okx", "BTC/USDT")
        self.assertEqual(recorded.source, "RECORDED_REPLAY_ESTIMATE")
        self.assertEqual(recorded.round_trip_cost_pct, 0.1)
        self.assertEqual(fallback.source, "CONSERVATIVE_BUILTIN_FALLBACK")
