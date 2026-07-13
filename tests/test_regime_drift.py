from __future__ import annotations

import numpy as np
import pandas as pd

from engine.regime_drift import (
    RegimeDriftConfig,
    regime_findings,
    regime_side_matrix,
    summarize_regime_drift,
)


def _rows(era: str, regime: str, side: str, expectation: float, count: int, symbol: str = "BTC/USDT") -> pd.DataFrame:
    rng = np.random.default_rng(abs(hash((era, regime, side, expectation))) % (2**32))
    returns = rng.normal(expectation, 0.20, count)
    return pd.DataFrame(
        {
            "__era": era,
            "__return": returns,
            "regime": regime,
            "side": side,
            "symbol": symbol,
        }
    )


def config() -> RegimeDriftConfig:
    return RegimeDriftConfig(min_samples_per_cell=30, decay_tolerance_pct=0.08, share_drift_tolerance=0.10)


def test_regime_matrix_emits_all_and_symbol_scopes():
    frame = pd.concat([
        _rows("LEGACY", "BULL", "LONG", 0.2, 60),
        _rows("RECENT", "BULL", "LONG", 0.1, 60),
    ])
    matrix = regime_side_matrix(frame)
    assert {"ALL", "BTC/USDT"}.issubset(set(matrix["symbol_scope"]))
    assert set(matrix["era"]) == {"LEGACY", "RECENT"}


def test_decayed_regime_is_detected():
    frame = pd.concat([
        _rows("LEGACY", "BULL", "LONG", 0.25, 100),
        _rows("TRANSITION", "BULL", "LONG", 0.12, 100),
        _rows("RECENT", "BULL", "LONG", -0.15, 100),
    ])
    summary = summarize_regime_drift(regime_side_matrix(frame), config())
    row = summary[(summary["symbol_scope"] == "ALL") & (summary["regime"] == "BULL")].iloc[0]
    assert row["status"] == "DECAYED_EDGE"
    assert row["recent_minus_legacy_expectancy"] < 0


def test_chronically_negative_regime_is_detected():
    frame = pd.concat([
        _rows("LEGACY", "BEAR", "LONG", -0.15, 100),
        _rows("TRANSITION", "BEAR", "LONG", -0.10, 100),
        _rows("RECENT", "BEAR", "LONG", -0.20, 100),
    ])
    summary = summarize_regime_drift(regime_side_matrix(frame), config())
    row = summary[(summary["symbol_scope"] == "ALL") & (summary["regime"] == "BEAR")].iloc[0]
    assert row["status"] == "CHRONICALLY_NEGATIVE"


def test_unknown_regime_is_ineligible():
    frame = pd.concat([
        _rows("LEGACY", "UNKNOWN", "SHORT", 0.2, 100),
        _rows("RECENT", "UNKNOWN", "SHORT", 0.2, 100),
    ])
    summary = summarize_regime_drift(regime_side_matrix(frame), config())
    assert set(summary["status"]) == {"INELIGIBLE_UNKNOWN"}
    assert not summary["eligible"].any()


def test_stable_positive_is_diagnostic_only():
    frame = pd.concat([
        _rows("LEGACY", "SIDEWAYS", "LONG", 0.25, 120),
        _rows("TRANSITION", "SIDEWAYS", "LONG", 0.20, 120),
        _rows("RECENT", "SIDEWAYS", "LONG", 0.18, 120),
    ])
    summary = summarize_regime_drift(regime_side_matrix(frame), config())
    row = summary[(summary["symbol_scope"] == "ALL") & (summary["regime"] == "SIDEWAYS")].iloc[0]
    assert row["status"] == "STABLE_EDGE_DIAGNOSTIC"
    assert row["eligible"]


def test_share_drift_is_measured():
    frame = pd.concat([
        _rows("LEGACY", "BULL", "LONG", 0.1, 80),
        _rows("LEGACY", "BEAR", "LONG", -0.1, 320),
        _rows("RECENT", "BULL", "LONG", 0.1, 320),
        _rows("RECENT", "BEAR", "LONG", -0.1, 80),
    ])
    summary = summarize_regime_drift(regime_side_matrix(frame), config())
    bull = summary[(summary["symbol_scope"] == "ALL") & (summary["regime"] == "BULL")].iloc[0]
    assert bull["recent_minus_legacy_share"] > 0.5


def test_findings_report_decayed_and_chronic_cells():
    frame = pd.concat([
        _rows("LEGACY", "BULL", "LONG", 0.2, 100),
        _rows("RECENT", "BULL", "LONG", -0.2, 100),
        _rows("LEGACY", "BEAR", "SHORT", -0.1, 100),
        _rows("RECENT", "BEAR", "SHORT", -0.1, 100),
    ])
    summary = summarize_regime_drift(regime_side_matrix(frame), config())
    findings = regime_findings(summary, config())
    text = " ".join(findings)
    assert "decayed" in text.lower() or "previously positive" in text.lower()
    assert "chronically" in text.lower()
