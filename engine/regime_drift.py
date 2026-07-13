"""Regime and side drift diagnostics for Freakto multi-cycle replay archives.

The module is descriptive and fail-closed. It never tunes a strategy, changes
runtime weights, promotes a policy, or enables Paper/Live trading.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import numpy as np
import pandas as pd

from engine.multi_cycle_validation import metric_payload, return_metrics

VERSION = "1.0.0"
ERA_ORDER = ("LEGACY", "TRANSITION", "RECENT")


@dataclass(frozen=True)
class RegimeDriftConfig:
    min_samples_per_cell: int = 40
    stable_expectancy_floor: float = 0.0
    profit_factor_floor: float = 1.0
    decay_tolerance_pct: float = 0.10
    share_drift_tolerance: float = 0.10


@dataclass(frozen=True)
class RegimeDriftRecord:
    symbol_scope: str
    regime: str
    side: str
    status: str
    eligible: bool
    legacy_samples: int
    transition_samples: int
    recent_samples: int
    legacy_expectancy: float
    transition_expectancy: float
    recent_expectancy: float
    legacy_profit_factor: float
    transition_profit_factor: float
    recent_profit_factor: float
    legacy_share: float
    transition_share: float
    recent_share: float
    recent_minus_legacy_expectancy: float
    recent_minus_legacy_share: float
    positive_eras: int
    total_eras: int


def _finite_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _normalize_label(value: Any, default: str = "UNKNOWN") -> str:
    text = str(value if value is not None else default).strip().upper()
    return text or default


def regime_side_matrix(frame: pd.DataFrame, min_samples: int = 1) -> pd.DataFrame:
    """Return metrics for every era × symbol-scope × regime × side cell.

    ``frame`` must already contain ``__era``, ``__return``, ``regime``, ``side``
    and optionally ``symbol``. The ALL scope is emitted alongside per-symbol
    scopes so portfolio-level and asset-specific drift can be separated.
    """
    required = {"__era", "__return", "regime", "side"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"regime drift input is missing columns: {missing}")
    if frame.empty:
        return pd.DataFrame()

    work = frame.copy()
    work["regime"] = work["regime"].map(_normalize_label)
    work["side"] = work["side"].map(_normalize_label)
    if "symbol" not in work.columns:
        work["symbol"] = "UNKNOWN"
    work["symbol"] = work["symbol"].map(_normalize_label)

    scopes: List[tuple[str, pd.DataFrame]] = [("ALL", work)]
    scopes.extend((symbol, group.copy()) for symbol, group in work.groupby("symbol", dropna=False))

    records: List[Dict[str, Any]] = []
    for symbol_scope, scoped in scopes:
        era_totals = scoped.groupby("__era", dropna=False).size().to_dict()
        grouped = scoped.groupby(["__era", "regime", "side"], dropna=False)
        for (era, regime, side), group in grouped:
            metrics = return_metrics(group)
            if metrics.sample_count < max(1, int(min_samples)):
                continue
            records.append(
                {
                    "symbol_scope": str(symbol_scope),
                    "era": str(era),
                    "regime": str(regime),
                    "side": str(side),
                    **metric_payload(metrics),
                    "sample_share": float(metrics.sample_count / max(1, int(era_totals.get(era, 0)))),
                }
            )
    return pd.DataFrame(records)


def _cell(matrix: pd.DataFrame, era: str, symbol_scope: str, regime: str, side: str) -> Mapping[str, Any]:
    subset = matrix[
        matrix["era"].eq(era)
        & matrix["symbol_scope"].eq(symbol_scope)
        & matrix["regime"].eq(regime)
        & matrix["side"].eq(side)
    ]
    return subset.iloc[0].to_dict() if len(subset) else {}


def _classify_regime(
    rows: Mapping[str, Mapping[str, Any]],
    regime: str,
    config: RegimeDriftConfig,
) -> tuple[str, bool]:
    if regime == "UNKNOWN":
        return "INELIGIBLE_UNKNOWN", False

    recent = rows.get("RECENT", {})
    recent_n = int(recent.get("sample_count", 0) or 0)
    if recent_n < config.min_samples_per_cell:
        return "INSUFFICIENT_RECENT_DATA", False

    available = [row for row in rows.values() if int(row.get("sample_count", 0) or 0) >= config.min_samples_per_cell]
    if len(available) < 2:
        return "INSUFFICIENT_MULTI_ERA_DATA", False

    expectations = [_finite_float(row.get("expectancy")) for row in available]
    recent_exp = _finite_float(recent.get("expectancy"))
    recent_pf = _finite_float(recent.get("profit_factor"))
    old = rows.get("LEGACY", {})
    old_n = int(old.get("sample_count", 0) or 0)
    old_exp = _finite_float(old.get("expectancy")) if old_n else 0.0

    all_positive = all(value > config.stable_expectancy_floor for value in expectations)
    all_negative = all(value <= config.stable_expectancy_floor for value in expectations)
    if all_positive and recent_pf >= config.profit_factor_floor:
        return "STABLE_EDGE_DIAGNOSTIC", True
    if all_negative:
        return "CHRONICALLY_NEGATIVE", False
    if old_n >= config.min_samples_per_cell and old_exp > config.stable_expectancy_floor:
        if recent_exp <= config.stable_expectancy_floor or recent_exp < old_exp - config.decay_tolerance_pct:
            return "DECAYED_EDGE", False
    if recent_exp > config.stable_expectancy_floor and recent_pf >= config.profit_factor_floor:
        return "RECENT_IMPROVEMENT_UNCONFIRMED", False
    return "UNSTABLE", False


def summarize_regime_drift(matrix: pd.DataFrame, config: RegimeDriftConfig) -> pd.DataFrame:
    if matrix is None or matrix.empty:
        return pd.DataFrame()
    required = {"symbol_scope", "era", "regime", "side"}
    missing = sorted(required - set(matrix.columns))
    if missing:
        raise ValueError(f"regime matrix is missing columns: {missing}")

    records: List[Dict[str, Any]] = []
    keys = matrix[["symbol_scope", "regime", "side"]].drop_duplicates()
    for key in keys.to_dict(orient="records"):
        symbol_scope = str(key["symbol_scope"])
        regime = str(key["regime"])
        side = str(key["side"])
        rows = {era: _cell(matrix, era, symbol_scope, regime, side) for era in ERA_ORDER}
        status, eligible = _classify_regime(rows, regime, config)

        payload: Dict[str, Any] = {
            "symbol_scope": symbol_scope,
            "regime": regime,
            "side": side,
            "status": status,
            "eligible": bool(eligible),
        }
        for era in ERA_ORDER:
            prefix = era.lower()
            row = rows[era]
            payload[f"{prefix}_samples"] = int(row.get("sample_count", 0) or 0)
            payload[f"{prefix}_expectancy"] = _finite_float(row.get("expectancy"))
            payload[f"{prefix}_profit_factor"] = _finite_float(row.get("profit_factor"))
            payload[f"{prefix}_share"] = _finite_float(row.get("sample_share"))

        payload["recent_minus_legacy_expectancy"] = (
            payload["recent_expectancy"] - payload["legacy_expectancy"]
        )
        payload["recent_minus_legacy_share"] = payload["recent_share"] - payload["legacy_share"]
        available_eras = [
            era for era in ERA_ORDER if payload[f"{era.lower()}_samples"] >= config.min_samples_per_cell
        ]
        payload["positive_eras"] = int(
            sum(payload[f"{era.lower()}_expectancy"] > config.stable_expectancy_floor for era in available_eras)
        )
        payload["total_eras"] = int(len(available_eras))
        records.append(payload)

    result = pd.DataFrame(records)
    if result.empty:
        return result
    status_order = {
        "DECAYED_EDGE": 0,
        "CHRONICALLY_NEGATIVE": 1,
        "UNSTABLE": 2,
        "RECENT_IMPROVEMENT_UNCONFIRMED": 3,
        "STABLE_EDGE_DIAGNOSTIC": 4,
        "INSUFFICIENT_RECENT_DATA": 5,
        "INSUFFICIENT_MULTI_ERA_DATA": 6,
        "INELIGIBLE_UNKNOWN": 7,
    }
    result["__order"] = result["status"].map(status_order).fillna(99)
    return result.sort_values(
        ["__order", "recent_expectancy", "recent_samples"], ascending=[True, True, False]
    ).drop(columns="__order").reset_index(drop=True)


def regime_findings(summary: pd.DataFrame, config: RegimeDriftConfig) -> List[str]:
    if summary is None or summary.empty:
        return ["No adequately sampled regime/side cells were available for drift analysis."]
    findings: List[str] = []
    decayed = summary[summary["status"].eq("DECAYED_EDGE")]
    chronic = summary[summary["status"].eq("CHRONICALLY_NEGATIVE")]
    stable = summary[summary["status"].eq("STABLE_EDGE_DIAGNOSTIC")]
    share_drift = summary[summary["recent_minus_legacy_share"].abs().ge(config.share_drift_tolerance)]
    if len(decayed):
        labels = ", ".join(
            f"{row.symbol_scope}:{row.regime}/{row.side}" for row in decayed.head(8).itertuples()
        )
        findings.append(f"Previously positive regime/side cells decayed in the recent era: {labels}.")
    if len(chronic):
        labels = ", ".join(
            f"{row.symbol_scope}:{row.regime}/{row.side}" for row in chronic.head(8).itertuples()
        )
        findings.append(f"Chronically non-positive regime/side cells were observed: {labels}.")
    if len(stable):
        labels = ", ".join(
            f"{row.symbol_scope}:{row.regime}/{row.side}" for row in stable.head(8).itertuples()
        )
        findings.append(
            "Positive multi-era cells exist only as diagnostics and are not automatically promotable: " + labels + "."
        )
    if len(share_drift):
        findings.append(
            f"{len(share_drift)} regime/side cells changed portfolio share by at least "
            f"{config.share_drift_tolerance:.0%} between legacy and recent eras."
        )
    if not findings:
        findings.append("Regime composition changed, but no single adequately sampled cell met a decisive drift rule.")
    return findings


__all__ = [
    "ERA_ORDER",
    "RegimeDriftConfig",
    "RegimeDriftRecord",
    "regime_side_matrix",
    "summarize_regime_drift",
    "regime_findings",
]
