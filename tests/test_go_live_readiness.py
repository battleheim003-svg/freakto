from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from freakto.paper.go_live import STATUS_BLOCKED, STATUS_ELIGIBLE, evaluate_go_live
from freakto.paper.service import PaperService
from engine.model_contract import CURRENT_MODEL_CONTRACT


ROOT = Path(__file__).parents[1]
POLICY = json.loads((ROOT / "config" / "paper_go_live_policy.json").read_text(encoding="utf-8"))


def test_frozen_policy_matches_current_model_contract():
    frozen = POLICY["frozen_contract"]
    for key, value in CURRENT_MODEL_CONTRACT.as_dict().items():
        assert frozen[key] == value


def complete_evidence():
    return {
        "policy_version": POLICY["policy_version"],
        "frozen_contract": copy.deepcopy(POLICY["frozen_contract"]),
        "evaluation_window": {
            "window_id": "paper-2026-q3",
            "started_utc": "2026-05-01T00:00:00Z",
            "ended_utc": "2026-07-20T00:00:00Z",
            "data_fingerprint": "sha256:fixture",
        },
        "metrics": {
            "closed_trades": 250,
            "observation_days": 75,
            "after_cost_expectancy_r": 0.08,
            "expectancy_ci95_lower_r": 0.01,
            "profit_factor": 1.2,
            "max_drawdown_r": -8.0,
            "regimes": [
                {"name": "bull", "closed_trades": 80, "after_cost_expectancy_r": 0.1},
                {"name": "bear", "closed_trades": 70, "after_cost_expectancy_r": 0.04},
                {"name": "range", "closed_trades": 60, "after_cost_expectancy_r": -0.01},
            ],
        },
        "operations": {
            "cycle_success_rate": 0.995,
            "data_freshness_rate": 1.0,
            "critical_incidents": 0,
        },
        "kill_switch": {
            "operator_stop_tested": True,
            "stale_data_stop_tested": True,
            "loss_limit_stop_tested": True,
            "restart_fail_closed_tested": True,
        },
        "approvals": [
            {"reviewer": "risk-owner", "approved_utc": "2026-07-21T10:00:00Z"},
            {"reviewer": "operations-owner", "approved_utc": "2026-07-21T11:00:00Z"},
        ],
    }


def test_complete_evidence_is_only_eligible_for_manual_review():
    result = evaluate_go_live(POLICY, complete_evidence())
    assert result["status"] == STATUS_ELIGIBLE
    assert result["blockers"] == []
    assert result["manual_activation_required"] is True
    assert result["live_activation_implemented"] is False
    assert result["live_orders_enabled"] is False
    assert result["real_capital_enabled"] is False
    assert result["allocation_pct"] == 0.0


@pytest.mark.parametrize(
    ("mutation", "blocker"),
    [
        (lambda row: row.update(policy_version="wrong"), "policy_version"),
        (lambda row: row["frozen_contract"].update(model_version="changed"), "frozen_contract"),
        (lambda row: row["evaluation_window"].update(data_fingerprint=""), "evaluation_window_frozen"),
        (lambda row: row["metrics"].update(closed_trades=199), "sample_size"),
        (lambda row: row["metrics"].update(observation_days=59), "observation_days"),
        (lambda row: row["metrics"].update(after_cost_expectancy_r=0.0), "after_cost_expectancy"),
        (lambda row: row["metrics"].update(expectancy_ci95_lower_r=0.0), "expectancy_confidence"),
        (lambda row: row["metrics"].update(max_drawdown_r=-12.1), "drawdown"),
        (lambda row: row["operations"].update(cycle_success_rate=0.98), "cycle_reliability"),
        (lambda row: row["operations"].update(critical_incidents=1), "critical_incidents"),
        (lambda row: row["kill_switch"].update(operator_stop_tested=False), "kill_switch"),
        (lambda row: row.update(approvals=row["approvals"][:1]), "independent_approvals"),
    ],
)
def test_every_critical_gate_fails_closed(mutation, blocker):
    evidence = complete_evidence()
    mutation(evidence)
    result = evaluate_go_live(POLICY, evidence)
    assert result["status"] == STATUS_BLOCKED
    assert blocker in result["blockers"]
    assert result["live_orders_enabled"] is False


def test_missing_evidence_file_is_blocked_by_service(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "paper_go_live_policy.json").write_text(
        json.dumps(POLICY), encoding="utf-8"
    )
    service = PaperService(tmp_path, lambda *_: 0, readiness_loader=lambda: None)
    code, result = service.execute("go-live-check")
    assert code == 2
    assert result["status"] == STATUS_BLOCKED
    assert result["live_orders_enabled"] is False
