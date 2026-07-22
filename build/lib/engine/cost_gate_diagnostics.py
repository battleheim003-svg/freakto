"""Cost-gate funnel diagnostics and train-derived geometry thresholds."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

VERSION = "1.0.0"
MODE = "COST_GATE_DIAGNOSTIC_ONLY"


@dataclass(frozen=True)
class TrainDerivedCostThresholds:
    maximum_cost_pct: float
    minimum_target_to_cost: float
    minimum_net_reward_risk: float
    maximum_risk_penalty: float
    source_rows: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def derive_train_thresholds(train: pd.DataFrame) -> TrainDerivedCostThresholds:
    if train is None or train.empty:
        return TrainDerivedCostThresholds(1.25, 2.0, 0.50, 25.0, 0)
    valid = train[train.get("geometry_valid", False).astype(bool)].copy()
    if valid.empty:
        return TrainDerivedCostThresholds(1.25, 2.0, 0.50, 25.0, 0)
    def q(column: str, quantile: float, fallback: float) -> float:
        values = pd.to_numeric(valid.get(column), errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        return float(values.quantile(quantile)) if not values.empty else fallback
    # Diagnostics only: deliberately broad enough to describe the train distribution,
    # never optimized against future returns.
    return TrainDerivedCostThresholds(
        maximum_cost_pct=max(0.01, q("event_execution_cost_pct", 0.95, 1.25)),
        minimum_target_to_cost=max(0.0, q("gross_target_to_cost", 0.25, 2.0)),
        minimum_net_reward_risk=max(0.0, q("net_reward_risk", 0.25, 0.50)),
        maximum_risk_penalty=max(0.0, q("risk_penalty", 0.90, 25.0)),
        source_rows=int(len(valid)),
    )


def apply_thresholds(frame: pd.DataFrame, thresholds: TrainDerivedCostThresholds, prefix: str = "train_derived") -> pd.DataFrame:
    work = frame.copy()
    cost = pd.to_numeric(work.get("event_execution_cost_pct"), errors="coerce")
    risk = pd.to_numeric(work.get("risk_penalty", 0.0), errors="coerce").fillna(0.0)
    geometry = work.get("geometry_valid", pd.Series(False, index=work.index)).astype(bool)
    work[f"{prefix}_cost_gate_pass"] = (
        work.get("has_event", pd.Series(True, index=work.index)).astype(bool)
        & geometry
        & cost.notna()
        & cost.le(thresholds.maximum_cost_pct)
        & pd.to_numeric(work.get("gross_target_to_cost"), errors="coerce").ge(thresholds.minimum_target_to_cost)
        & pd.to_numeric(work.get("net_reward_risk"), errors="coerce").ge(thresholds.minimum_net_reward_risk)
        & risk.le(thresholds.maximum_risk_penalty)
    )
    return work


def rejection_reason(frame: pd.DataFrame, *, maximum_cost_pct: float, minimum_target_to_cost: float,
                     minimum_net_reward_risk: float, maximum_risk_penalty: float) -> pd.Series:
    reasons = pd.Series("PASS", index=frame.index, dtype=object)
    checks = [
        ("INVALID_ENTRY", ~frame.get("entry_valid", pd.Series(False, index=frame.index)).astype(bool)),
        ("INVALID_STOP", ~frame.get("stop_valid", pd.Series(False, index=frame.index)).astype(bool)),
        ("INVALID_TARGET", ~frame.get("target_valid", pd.Series(False, index=frame.index)).astype(bool)),
        ("INVALID_COST", pd.to_numeric(frame.get("event_execution_cost_pct"), errors="coerce").isna()),
        ("COST_TOO_HIGH", pd.to_numeric(frame.get("event_execution_cost_pct"), errors="coerce").gt(maximum_cost_pct)),
        ("TARGET_TO_COST_TOO_LOW", pd.to_numeric(frame.get("gross_target_to_cost"), errors="coerce").lt(minimum_target_to_cost)),
        ("NET_RR_TOO_LOW", pd.to_numeric(frame.get("net_reward_risk"), errors="coerce").lt(minimum_net_reward_risk)),
        ("RISK_PENALTY_TOO_HIGH", pd.to_numeric(frame.get("risk_penalty", 0.0), errors="coerce").fillna(0.0).gt(maximum_risk_penalty)),
    ]
    unresolved = reasons.eq("PASS")
    for name, mask in checks:
        hit = unresolved & mask.fillna(True)
        reasons.loc[hit] = name
        unresolved = reasons.eq("PASS")
    return reasons


def funnel_table(frame: pd.DataFrame, pass_column: str = "cost_gate_pass") -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame(columns=["stage", "rows", "retention_from_events"])
    total = len(frame)
    stages = [
        ("EVENT_DETECTED", pd.Series(True, index=frame.index)),
        ("VALID_ENTRY", frame.get("entry_valid", False).astype(bool)),
        ("VALID_STOP", frame.get("entry_valid", False).astype(bool) & frame.get("stop_valid", False).astype(bool)),
        ("VALID_TARGET", frame.get("entry_valid", False).astype(bool) & frame.get("stop_valid", False).astype(bool) & frame.get("target_valid", False).astype(bool)),
        ("VALID_COST", frame.get("geometry_valid", False).astype(bool) & pd.to_numeric(frame.get("event_execution_cost_pct"), errors="coerce").notna()),
        ("TARGET_TO_COST_PASS", frame.get("geometry_valid", False).astype(bool) & pd.to_numeric(frame.get("gross_target_to_cost"), errors="coerce").ge(2.0)),
        ("NET_RR_PASS", frame.get("geometry_valid", False).astype(bool) & pd.to_numeric(frame.get("net_reward_risk"), errors="coerce").ge(0.50)),
        ("FINAL_COST_GATE", frame.get(pass_column, pd.Series(False, index=frame.index)).astype(bool)),
    ]
    return pd.DataFrame([{"stage": name, "rows": int(mask.sum()), "retention_from_events": float(mask.mean())} for name, mask in stages])


def distribution_summary(frame: pd.DataFrame) -> pd.DataFrame:
    columns = ["target_distance_pct", "stop_distance_pct", "event_execution_cost_pct", "gross_target_to_cost", "net_reward_risk"]
    records = []
    for column in columns:
        values = pd.to_numeric(frame.get(column), errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        if values.empty:
            records.append({"metric": column, "count": 0})
            continue
        records.append({"metric": column, "count": int(len(values)), "min": float(values.min()), "p10": float(values.quantile(.1)), "p25": float(values.quantile(.25)), "median": float(values.median()), "p75": float(values.quantile(.75)), "p90": float(values.quantile(.9)), "max": float(values.max())})
    return pd.DataFrame(records)
