from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest

from engine.event_opportunity_universe import (
    EventUniverseConfig,
    build_event_opportunity_universe,
    event_overlap_table,
    prepare_event_rows,
    validate_event_feature_names,
)


def synthetic_event_rows(rows: int = 1800, start: str = "2019-01-01") -> pd.DataFrame:
    rng = np.random.default_rng(7241)
    idx = np.arange(rows)
    timestamp = pd.date_range(start, periods=rows, freq="4h", tz="UTC")
    side = np.where(idx % 2 == 0, "LONG", "SHORT")
    regime = np.where(side == "LONG", "BULL", "BEAR").astype(object)
    trend = rng.uniform(8, 17, rows)
    volume = rng.uniform(1, 8, rows)
    structure = rng.uniform(1, 7, rows)
    momentum = rng.uniform(5, 25, rows)
    rsi = rng.uniform(38, 62, rows)
    atr = 1.0 + rng.normal(0, 0.05, rows)

    breakout = idx % 5 == 0
    trend[breakout] = 23
    volume[breakout] = 16
    structure[breakout] = 10

    reversion = idx % 7 == 0
    regime[reversion] = "SIDEWAYS"
    rsi[reversion & (side == "LONG")] = 25
    rsi[reversion & (side == "SHORT")] = 75

    vol_expansion = idx % 11 == 0
    atr[vol_expansion] = 2.2
    volume[vol_expansion] = 12

    liquidity = idx % 13 == 0
    structure[liquidity] = 11

    entry = 100 + rng.uniform(-5, 5, rows)
    target_distance = np.where(idx % 17 == 0, 0.4, 2.4)
    stop_distance = 1.4
    target = np.where(side == "LONG", entry * (1 + target_distance / 100), entry * (1 - target_distance / 100))
    stop = np.where(side == "LONG", entry * (1 - stop_distance / 100), entry * (1 + stop_distance / 100))
    cost = np.where(idx % 19 == 0, 0.8, 0.30)

    quality = breakout | liquidity | (vol_expansion & (volume >= 10))
    positive = quality & (idx % 3 != 0)
    target_hit = positive
    stop_hit = ~positive & ((breakout | reversion | vol_expansion | liquidity))
    fixed_return = np.where(positive, 1.1, -1.0) - cost

    return pd.DataFrame(
        {
            "run_id": "market_replay_synthetic",
            "decision_id": [f"event-{i}" for i in idx],
            "candle_timestamp": timestamp,
            "symbol": np.array(["BTC/USDT", "ETH/USDT", "SOL/USDT"])[idx % 3],
            "timeframe": "4h",
            "side": side,
            "regime": regime,
            "score": trend + momentum + volume + structure,
            "trend_score": trend,
            "momentum_score": momentum,
            "volume_score": volume,
            "structure_score": structure,
            "regime_score": np.where(regime == "BULL", 3.0, np.where(regime == "BEAR", -3.0, 0.0)),
            "risk_penalty": rng.uniform(0, 12, rows),
            "atr_pct": atr,
            "rsi_14": rsi,
            "macd_histogram": rng.normal(0, 0.8, rows),
            "round_trip_cost_pct": cost,
            "entry_price": entry,
            "target_1": target,
            "stop_price": stop,
            "volatility_expansion": vol_expansion,
            "liquidity_sweep": liquidity,
            "target_1_hit": target_hit,
            "stop_hit": stop_hit,
            "intrabar_ambiguity": target_hit & stop_hit,
            "first_exit_candle_offset": 3,
            "first_exit_reason": np.where(target_hit, "TARGET_1", np.where(stop_hit, "STOP", "TIME")),
            "gross_signed_return_after_6c_pct": fixed_return + cost,
            "net_signed_return_after_6c_pct": fixed_return,
            "market_return_after_6c_pct": rng.normal(0, 1.2, rows),
        }
    )


def config() -> EventUniverseConfig:
    return EventUniverseConfig(
        development_cutoff_utc="2026-07-09T12:00:00Z",
        volatility_lookback=10,
        minimum_target_to_cost=2.0,
        minimum_net_reward_risk=0.5,
    )


def test_leakage_fields_are_rejected_for_event_detection():
    with pytest.raises(ValueError):
        validate_event_feature_names(["future_return"])
    with pytest.raises(ValueError):
        validate_event_feature_names(["mfe_pct"])


def test_prepare_event_rows_enforces_cutoff_and_deduplicates():
    frame = synthetic_event_rows(300)
    duplicate = frame.tail(1).copy()
    duplicate["candle_timestamp"] = pd.Timestamp("2027-01-01", tz="UTC")
    prepared = prepare_event_rows(pd.concat([frame, frame.tail(1), duplicate], ignore_index=True), config())
    assert prepared["decision_id"].is_unique
    assert prepared["__timestamp"].max() <= pd.Timestamp(config().development_cutoff_utc)
    assert set(prepared["side"]) == {"LONG", "SHORT"}


def test_breakout_proxy_is_detected_from_entry_time_fields():
    frame = synthetic_event_rows(100)
    events, diagnostics = build_event_opportunity_universe(frame, config())
    breakout_ids = set(frame.loc[frame.index % 5 == 0, "decision_id"])
    detected = set(events.loc[events["primary_event"].eq("BREAKOUT_CONFIRMATION"), "decision_id"])
    assert breakout_ids & detected
    assert diagnostics.aggregate_score_used is False
    assert diagnostics.outcome_fields_used is False


def test_mean_reversion_requires_extreme_rsi_and_range_regime():
    frame = synthetic_event_rows(120)
    events, _ = build_event_opportunity_universe(frame, config())
    mean_reversion = events[events["primary_event"].eq("EXTREME_MEAN_REVERSION")]
    assert not mean_reversion.empty
    assert mean_reversion["regime"].eq("SIDEWAYS").all()
    assert ((mean_reversion["side"].eq("LONG") & mean_reversion["rsi_14"].le(30)) | (
        mean_reversion["side"].eq("SHORT") & mean_reversion["rsi_14"].ge(70)
    )).all()


def test_explicit_volatility_and_liquidity_events_are_supported():
    frame = synthetic_event_rows(150)
    events, diagnostics = build_event_opportunity_universe(frame, config())
    assert diagnostics.explicit_volatility_rows > 0
    assert diagnostics.explicit_sweep_rows > 0
    assert "LIQUIDITY_SWEEP" in set(events["primary_event"])
    assert "VOLATILITY_EXPANSION" in set(events["primary_event"])


def test_event_priority_prevents_double_counting():
    frame = synthetic_event_rows(100)
    frame.loc[0, ["liquidity_sweep", "volatility_expansion"]] = True
    frame.loc[0, ["structure_score", "volume_score", "trend_score"]] = [11, 18, 24]
    events, diagnostics = build_event_opportunity_universe(frame, config())
    row = events[events["decision_id"].eq("event-0")].iloc[0]
    assert row["primary_event"] == "LIQUIDITY_SWEEP"
    assert len(json.loads(row["event_types"])) >= 2
    assert diagnostics.multi_event_decisions > 0
    assert events["decision_id"].is_unique


def test_cost_gate_uses_pretrade_geometry_only():
    frame = synthetic_event_rows(200)
    events, _ = build_event_opportunity_universe(frame, config())
    assert {"gross_target_to_cost", "net_reward_risk", "cost_gate_pass"}.issubset(events.columns)
    expensive = events[events["event_execution_cost_pct"].ge(0.8)]
    assert not expensive.empty
    assert (~expensive["cost_gate_pass"]).any()
    assert events.loc[events["cost_gate_pass"], "gross_target_to_cost"].ge(config().minimum_target_to_cost).all()


def test_mutating_future_outcomes_does_not_change_event_ids():
    frame = synthetic_event_rows(300)
    first, _ = build_event_opportunity_universe(frame, config())
    mutated = frame.copy()
    mutated["net_signed_return_after_6c_pct"] = mutated["net_signed_return_after_6c_pct"] * -100
    mutated["target_1_hit"] = ~mutated["target_1_hit"]
    second, _ = build_event_opportunity_universe(mutated, config())
    assert first[["decision_id", "primary_event", "cost_gate_pass"]].equals(
        second[["decision_id", "primary_event", "cost_gate_pass"]]
    )


def test_fresh_scope_is_strictly_after_cutoff():
    frame = synthetic_event_rows(100)
    frame.loc[frame.index[-20:], "candle_timestamp"] = pd.date_range("2026-07-10", periods=20, freq="4h", tz="UTC")
    development = prepare_event_rows(frame, config(), time_scope="development")
    fresh = prepare_event_rows(frame, config(), time_scope="fresh")
    cutoff = pd.Timestamp(config().development_cutoff_utc)
    assert development["__timestamp"].max() <= cutoff
    assert fresh["__timestamp"].min() > cutoff
    assert set(development["decision_id"]).isdisjoint(set(fresh["decision_id"]))


def test_overlap_table_reports_pairs():
    events, _ = build_event_opportunity_universe(synthetic_event_rows(300), config())
    overlap = event_overlap_table(events)
    assert not overlap.empty
    assert {"event_a", "event_b", "overlap_count"}.issubset(overlap.columns)
    assert overlap["overlap_count"].gt(0).all()


def production_replay_schema(rows: int = 1200) -> pd.DataFrame:
    rng = np.random.default_rng(991)
    idx = np.arange(rows)
    side = np.where(idx % 2 == 0, "LONG", "SHORT")
    regime = np.where(idx % 9 < 3, "BULL", np.where(idx % 9 < 6, "BEAR", "SIDEWAYS"))
    trend = rng.integers(0, 29, rows)
    volume = rng.integers(0, 21, rows)
    structure = rng.integers(0, 13, rows)
    momentum = rng.integers(0, 31, rows)
    long_score = trend + momentum + volume + structure
    short_score = np.maximum(0, 80 - long_score)
    volatility = 1.0 + rng.normal(0, 0.12, rows)
    volatility[idx % 37 == 0] = 1.8
    return pd.DataFrame({
        "run_id": "market_replay_real_schema",
        "decision_id": [f"real-{i}" for i in idx],
        "candle_timestamp": pd.date_range("2020-01-01", periods=rows, freq="4h", tz="UTC"),
        "symbol": np.array(["BTC/USDT", "ETH/USDT", "SOL/USDT"])[idx % 3],
        "timeframe": "4h",
        "side": side,
        "score": np.maximum(long_score, short_score),
        "regime_label": regime,
        "long_score": long_score,
        "short_score": short_score,
        "trend_score": trend,
        "momentum_score": momentum,
        "volume_score": volume,
        "structure_score": structure,
        "regime_score": rng.integers(0, 9, rows),
        "risk_penalty": rng.integers(0, 12, rows),
        "execution_volatility_multiplier": volatility,
        "round_trip_cost_pct": 0.55,
        "entry_price": 100.0,
        "targets": "[102.0, 104.0, 106.0]",
        "stop_zone": "98.0 - 98.5",
        "net_signed_return_after_6c_pct": rng.normal(-0.2, 1.5, rows),
    })


def test_real_replay_component_schema_produces_sparse_events_without_raw_indicators():
    frame = production_replay_schema()
    events, diagnostics = build_event_opportunity_universe(frame, config())
    assert diagnostics.schema_mode == "REPLAY_COMPONENT_SCHEMA"
    assert diagnostics.event_rows > 0
    assert diagnostics.event_rows < diagnostics.rows_usable
    assert diagnostics.breakout_rows > 0
    assert diagnostics.volatility_expansion_rows > 0
    assert "LIQUIDITY_SWEEP" in diagnostics.unavailable_event_families


def test_component_schema_does_not_fabricate_liquidity_sweeps():
    events, diagnostics = build_event_opportunity_universe(production_replay_schema(), config())
    assert diagnostics.liquidity_sweep_rows == 0
    assert not events["primary_event"].eq("LIQUIDITY_SWEEP").any()


def test_event_family_counts_match_detected_masks():
    events, diagnostics = build_event_opportunity_universe(production_replay_schema(), config())
    assert diagnostics.breakout_rows >= int(events["primary_event"].eq("BREAKOUT_CONFIRMATION").sum())
    assert diagnostics.mean_reversion_rows >= int(events["primary_event"].eq("EXTREME_MEAN_REVERSION").sum())
