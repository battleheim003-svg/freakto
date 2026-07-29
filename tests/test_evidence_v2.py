from __future__ import annotations

import csv

import pytest

from freakto.evidence.evaluator import evaluate_path
from freakto.evidence.ledger import DecisionLedger, EvidenceContractError, OutcomeLedger, canonical_cohort, import_quarantine
from freakto.evidence.migration import migrate_decisions_csv
from freakto.evidence.read_model import INVALIDATED_LEGACY_STATUS, evidence_summary
from engine.edge_validation import decision_edge_metrics


def decision() -> dict:
    return {
        "decision_id": "d-1", "candle_timestamp_utc": "2026-01-01T00:00:00+00:00",
        "symbol": "BTC/USDT", "timeframe": "4h", "side": "LONG", "entry_price": 100,
        "stop_price": 95, "targets": [105], "features": {"score": 70},
    }


def candles(*rows: tuple[float, float, float, float]) -> list[dict]:
    return [
        {"timestamp": f"2026-01-01T0{i}:00:00+00:00", "open": o, "high": h, "low": l, "close": c}
        for i, (o, h, l, c) in enumerate(rows, 1)
    ]


def test_neutral_has_no_economic_outcome():
    neutral = decision() | {"side": "NEUTRAL"}
    assert evaluate_path(neutral, candles((100, 110, 90, 101)), horizon_candles=1) is None


def test_event_ordering_uses_next_open_and_stop_first_for_same_bar():
    outcome = evaluate_path(decision(), candles((101, 106, 94, 102)), horizon_candles=1, fee_bps_per_side=0, slippage_bps_per_side=0)
    assert outcome["entry_price"] == 101
    assert outcome["terminal_status"] == "STOP"
    assert outcome["intrabar_ambiguity"] is True
    assert outcome["terminal_offset"] == 1


def test_expiry_is_terminal_and_net_of_cost():
    outcome = evaluate_path(decision(), candles((101, 103, 99, 102), (102, 104, 100, 103)), horizon_candles=2, fee_bps_per_side=10, slippage_bps_per_side=5)
    assert outcome["terminal_status"] == "EXPIRED"
    assert outcome["cost_pct"] == pytest.approx(0.3)
    assert outcome["net_return_pct"] == pytest.approx(outcome["gross_return_pct"] - 0.3)


def test_decision_id_is_idempotent_and_cohort_is_directional(tmp_path):
    decisions = DecisionLedger(tmp_path)
    assert decisions.append(decision()) is True
    assert decisions.append(decision()) is False
    outcomes = OutcomeLedger(tmp_path)
    outcomes.upsert(evaluate_path(decision(), candles((100, 106, 99, 105)), horizon_candles=1, fee_bps_per_side=0, slippage_bps_per_side=0))
    assert len(canonical_cohort(tmp_path)) == 1


def test_legacy_schema_drift_is_quarantined(tmp_path):
    source = tmp_path / "decisions.csv"
    with source.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["decision_id", "candle_timestamp", "symbol", "timeframe", "side", "price", "targets"])
        writer.writeheader()
        writer.writerow({"decision_id": "bad", "candle_timestamp": "2026-01-01T00:00:00Z", "symbol": "BTC/USDT", "timeframe": "4h", "side": "LONG", "price": "100", "targets": '["Medium"]'})
    result = migrate_decisions_csv(source, tmp_path)
    assert result["quarantined"] == 1
    assert import_quarantine(tmp_path)[0]["reason"].startswith("schema drift")


def test_legacy_evidence_is_invalid_until_v2_has_terminal_outcomes(tmp_path):
    summary = evidence_summary(tmp_path)
    assert summary["status"] == INVALIDATED_LEGACY_STATUS
    assert "LEGACY_FORWARD_EDGE_INVALIDATED" in summary["blockers"]


def test_invalid_decision_fails_closed(tmp_path):
    with pytest.raises(EvidenceContractError):
        DecisionLedger(tmp_path).append(decision() | {"entry_price": 0})


def test_edge_validation_never_uses_legacy_csv_when_v2_is_empty(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "decision_evaluations.csv").write_text(
        "decision_id,side,evaluation_status,return_after_24h_pct\nold,NEUTRAL,COMPLETE,99\n",
        encoding="utf-8",
    )
    metrics = decision_edge_metrics()
    assert metrics.quality == "INVALIDATED_DATA_CONTRACT"
    assert metrics.sample_count == 0
