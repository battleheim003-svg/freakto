"""Fail-closed go-live evidence gate.

Passing this gate only makes a frozen Paper evaluation eligible for independent
manual review. It never enables live orders or allocates capital.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from freakto.core import PAPER_SAFETY


STATUS_BLOCKED = "BLOCKED_GO_LIVE_REVIEW"
STATUS_ELIGIBLE = "ELIGIBLE_FOR_MANUAL_GO_LIVE_REVIEW"


@dataclass(frozen=True)
class Gate:
    name: str
    passed: bool
    actual: Any
    required: Any

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "actual": self.actual,
            "required": self.required,
        }


def _load_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def load_policy(path: Path) -> dict[str, Any]:
    return _load_object(path)


def load_evidence(path: Path) -> dict[str, Any]:
    return _load_object(path)


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def evaluate_go_live(policy: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, Any]:
    thresholds = dict(policy.get("thresholds") or {})
    frozen = dict(policy.get("frozen_contract") or {})
    observed = dict(evidence.get("frozen_contract") or {})
    metrics = dict(evidence.get("metrics") or {})
    operations = dict(evidence.get("operations") or {})
    kill_switch = dict(evidence.get("kill_switch") or {})
    window = dict(evidence.get("evaluation_window") or {})

    gates: list[Gate] = []

    def minimum(name: str, source: Mapping[str, Any], key: str, threshold_key: str) -> None:
        actual = _number(source.get(key))
        required = _number(thresholds.get(threshold_key))
        gates.append(Gate(name, actual >= required, actual, required))

    gates.append(Gate("policy_version", evidence.get("policy_version") == policy.get("policy_version"), evidence.get("policy_version"), policy.get("policy_version")))
    gates.append(Gate("frozen_contract", bool(frozen) and observed == frozen, observed, frozen))
    started = _timestamp(window.get("started_utc"))
    ended = _timestamp(window.get("ended_utc"))
    window_complete = bool(
        window.get("window_id")
        and window.get("data_fingerprint")
        and started
        and ended
        and started < ended <= datetime.now(timezone.utc)
    )
    gates.append(Gate("evaluation_window_frozen", window_complete, window, "window_id, start, end, and data fingerprint"))

    minimum("sample_size", metrics, "closed_trades", "minimum_closed_trades")
    minimum("observation_days", metrics, "observation_days", "minimum_observation_days")
    minimum("after_cost_expectancy", metrics, "after_cost_expectancy_r", "minimum_after_cost_expectancy_r")
    ci_lower = _number(metrics.get("expectancy_ci95_lower_r"))
    ci_floor = _number(thresholds.get("minimum_expectancy_ci95_lower_r"))
    gates.append(Gate("expectancy_confidence", ci_lower > ci_floor, ci_lower, f"> {ci_floor}"))
    minimum("profit_factor", metrics, "profit_factor", "minimum_profit_factor")
    allowed_drawdown = _number(thresholds.get("maximum_drawdown_r"))
    max_drawdown = abs(_number(metrics.get("max_drawdown_r"), allowed_drawdown + 1))
    gates.append(Gate("drawdown", max_drawdown <= allowed_drawdown, max_drawdown, allowed_drawdown))

    regimes = list(metrics.get("regimes") or [])
    min_regime_samples = int(_number(thresholds.get("minimum_trades_per_regime")))
    eligible_regimes = [row for row in regimes if int(_number(row.get("closed_trades"))) >= min_regime_samples]
    positive_regimes = [row for row in eligible_regimes if _number(row.get("after_cost_expectancy_r")) > 0]
    positive_fraction = len(positive_regimes) / len(eligible_regimes) if eligible_regimes else 0.0
    gates.append(Gate("regime_coverage", len(eligible_regimes) >= int(_number(thresholds.get("minimum_regimes"))), len(eligible_regimes), int(_number(thresholds.get("minimum_regimes")))))
    required_positive_fraction = _number(thresholds.get("minimum_positive_regime_fraction"))
    gates.append(Gate("regime_stability", positive_fraction + 1e-9 >= required_positive_fraction, positive_fraction, required_positive_fraction))

    minimum("cycle_reliability", operations, "cycle_success_rate", "minimum_cycle_success_rate")
    minimum("data_freshness", operations, "data_freshness_rate", "minimum_data_freshness_rate")
    max_incidents = int(_number(thresholds.get("maximum_critical_incidents")))
    incidents = int(_number(operations.get("critical_incidents"), max_incidents + 1))
    gates.append(Gate("critical_incidents", incidents <= max_incidents, incidents, max_incidents))

    required_switches = ("operator_stop_tested", "stale_data_stop_tested", "loss_limit_stop_tested", "restart_fail_closed_tested")
    gates.append(Gate("kill_switch", all(kill_switch.get(key) is True for key in required_switches), {key: kill_switch.get(key) for key in required_switches}, "all true"))
    approvals = list(evidence.get("approvals") or [])
    reviewers = {
        row.get("reviewer")
        for row in approvals
        if isinstance(row, dict) and row.get("reviewer") and _timestamp(row.get("approved_utc"))
    }
    required_approvals = int(_number(thresholds.get("minimum_independent_approvals")))
    gates.append(Gate("independent_approvals", len(reviewers) >= required_approvals, len(reviewers), required_approvals))

    blockers = [gate.name for gate in gates if not gate.passed]
    return {
        "status": STATUS_ELIGIBLE if not blockers else STATUS_BLOCKED,
        "policy_version": policy.get("policy_version"),
        "gates": [gate.to_dict() for gate in gates],
        "blockers": blockers,
        "manual_activation_required": True,
        "live_activation_implemented": False,
        **PAPER_SAFETY.payload(),
    }


def evaluate_files(policy_path: Path, evidence_path: Path) -> dict[str, Any]:
    return evaluate_go_live(load_policy(policy_path), load_evidence(evidence_path))
