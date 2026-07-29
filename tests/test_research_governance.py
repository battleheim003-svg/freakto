from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest
import pandas as pd

from engine.artifact_protocols import GLOBAL_UTC_SELECTOR
from engine.experiment_registry import (
    DEFAULT_GOVERNANCE_PATH,
    ResearchGovernanceRegistry,
    TERMINAL_HOLDOUT_STATUS,
    TERMINAL_RESEARCH_OUTCOME,
)
from engine.research_contracts import (
    FUTURE_EVENT_META_WALK_FORWARD_CONTRACT,
    FUTURE_WALK_FORWARD_CONTRACT,
    LEGACY_EVENT_META_WALK_FORWARD_CONTRACT,
    research_contract_fingerprint,
)
from freakto.paper import campaign
from freakto.technical_v2.promotion import promotion_recommendation
from engine import paper_readiness_v2 as readiness_module


EXPERIMENT_ID = "market_replay_20260728_183716"


def _document() -> dict:
    return json.loads(DEFAULT_GOVERNANCE_PATH.read_text(encoding="utf-8"))


def _write_document(tmp_path: Path, document: dict) -> Path:
    path = tmp_path / "governance.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_phase6g_terminal_record_loads_with_real_identity():
    record = ResearchGovernanceRegistry().get(EXPERIMENT_ID)
    assert record is not None
    assert record.payload["experiment_status"] == TERMINAL_HOLDOUT_STATUS
    assert record.payload["research_outcome"] == TERMINAL_RESEARCH_OUTCOME
    assert record.payload["promotion_eligible"] is False
    assert record.payload["terminal"] is True
    assert record.payload["replay_fingerprint"].startswith("d3963dd9")
    assert record.payload["walk_forward_contract_version"] == LEGACY_EVENT_META_WALK_FORWARD_CONTRACT
    assert record.payload["walk_forward_folds"] == 3


def test_conflicting_duplicate_and_unknown_status_fail_closed(tmp_path):
    document = _document()
    duplicate = dict(document["experiments"][0])
    duplicate["event_rows"] = 999
    document["experiments"].append(duplicate)
    with pytest.raises(ValueError, match="GOVERNANCE_RECORD_CONFLICT"):
        ResearchGovernanceRegistry(_write_document(tmp_path, document))

    document = _document()
    document["experiments"][0]["experiment_status"] = "READY"
    with pytest.raises(ValueError, match="unknown experiment status"):
        ResearchGovernanceRegistry(_write_document(tmp_path, document))


def test_terminal_record_fingerprint_and_missing_governance_block_promotion():
    registry = ResearchGovernanceRegistry()
    with pytest.raises(ValueError, match="HOLDOUT_CONSUMED_NOT_VALIDATED"):
        registry.require_promotion_eligible(experiment_id=EXPERIMENT_ID)
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        registry.require_promotion_eligible(
            experiment_id=EXPERIMENT_ID,
            replay_fingerprint="0" * 64,
        )
    with pytest.raises(ValueError, match="governance record is missing"):
        registry.require_promotion_eligible(experiment_id="missing")


def test_legacy_record_cannot_be_reinterpreted_as_future_four_fold():
    registry = ResearchGovernanceRegistry()
    registry.require_contract(EXPERIMENT_ID, LEGACY_EVENT_META_WALK_FORWARD_CONTRACT)
    with pytest.raises(ValueError, match="LEGACY_REINTERPRETATION_FORBIDDEN"):
        registry.require_contract(EXPERIMENT_ID, FUTURE_EVENT_META_WALK_FORWARD_CONTRACT)


def test_future_contract_is_authoritative_and_versioned_in_fingerprint():
    contract = FUTURE_WALK_FORWARD_CONTRACT
    contract.validate()
    assert contract.walk_forward_folds == 4
    assert contract.purge_timestamps == 6
    assert contract.minimum_valid_folds == 3
    assert contract.minimum_positive_fraction == 2 / 3
    first = research_contract_fingerprint({"replay": "abc"})
    assert first == research_contract_fingerprint({"replay": "abc"})
    changed_version = replace(contract, version="event-meta-walk-forward-4fold-purge6-v3")
    with pytest.raises(ValueError, match="without a version bump"):
        research_contract_fingerprint({"replay": "abc"}, changed_version)
    changed_fold = replace(contract, walk_forward_folds=5)
    with pytest.raises(ValueError, match="without a version bump"):
        research_contract_fingerprint({"replay": "abc"}, changed_fold)


def test_backend_campaign_and_promotion_reject_terminal_experiment(monkeypatch, tmp_path):
    monkeypatch.setattr(
        campaign.subprocess,
        "Popen",
        lambda *args, **kwargs: pytest.fail("terminal governance must not spawn"),
    )
    with pytest.raises(RuntimeError, match="HOLDOUT_CONSUMED_NOT_VALIDATED"):
        campaign.start_campaign(
            tmp_path,
            artifact_selector=GLOBAL_UTC_SELECTOR,
            experiment_id=EXPERIMENT_ID,
        )
    result = promotion_recommendation(
        {"expectancy_pct": 0.0, "maximum_drawdown_pct": 10},
        {"samples": 999, "expectancy_pct": 1.0, "maximum_drawdown_pct": 1},
        {"status": "PASSED"},
        artifact_selector=GLOBAL_UTC_SELECTOR,
        experiment_id=EXPERIMENT_ID,
    )
    assert result["status"] == "KEEP_RESEARCH"
    assert "HOLDOUT_CONSUMED_NOT_VALIDATED" in result["blockers"]
    assert result["live_eligible"] is False


def test_selector_cannot_bypass_terminal_governance():
    with pytest.raises(ValueError, match="PROMOTION_NOT_ELIGIBLE"):
        ResearchGovernanceRegistry().require_promotion_eligible(
            artifact_selector=GLOBAL_UTC_SELECTOR
        )


def test_general_readiness_cannot_override_terminal_governance(monkeypatch):
    universe = pd.DataFrame(
        {
            "__timestamp": pd.date_range("2024-01-01", periods=20, freq="4h", tz="UTC"),
            "cost_gate_pass": True,
            "primary_event": "BREAKOUT_CONFIRMATION",
            "realized_net_return_pct": 1.0,
        }
    )
    holdout = pd.DataFrame(
        {
            "strategy": ["EVENT_COST_GATED"],
            "sample_count": [200],
            "expectancy": [1.0],
            "profit_factor": [2.0],
            "expectancy_ci_low": [0.2],
            "expectancy_ci_high": [1.8],
        }
    )
    monkeypatch.setattr(
        readiness_module,
        "_read_csv",
        lambda path: holdout if path.name == "holdout_benchmarks.csv" else universe,
    )
    monkeypatch.setattr(
        readiness_module,
        "_read_json",
        lambda path: (
            {"event_rows": 500, "cost_gated_event_rows": 200}
            if "event_opportunity" in path.name
            else {"status": "COMPLETE_DIAGNOSTIC_ONLY"}
            if "cost_gate" in path.name
            else {
                "fresh_directional_rows": 500,
                "fixed_gate_samples": 100,
                "fixed_gate_expectancy": 1.0,
                "fixed_gate_profit_factor": 2.0,
            }
        ),
    )
    readiness, _ = readiness_module.build_paper_launch_readiness(
        artifact_selector=GLOBAL_UTC_SELECTOR,
        experiment_id=EXPERIMENT_ID,
    )
    assert readiness.research_collection_ready is False
    assert readiness.strategy_paper_ready is False
    assert "HOLDOUT_CONSUMED_NOT_VALIDATED" in readiness.blockers
