"""Chronological two-stage meta-label validation.

The primary DecisionEngine chooses direction. This module only estimates
whether that particular primary decision should be trusted. It never changes
the primary score or places an order.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from engine.model_contract import META_LABEL_MODEL_VERSION


DEFAULT_FEATURES = (
    "score", "trend_score", "momentum_score", "volume_score",
    "structure_score", "regime_score", "risk_penalty", "regime_confidence",
)


def _metrics(y: pd.Series, probability: np.ndarray, threshold: float, returns: pd.Series) -> Dict[str, Any]:
    accepted = probability >= threshold
    accepted_count = int(accepted.sum())
    true = y.to_numpy(dtype=int)
    precision = int(((true == 1) & accepted).sum()) / accepted_count if accepted_count else 0.0
    coverage = accepted_count / len(y) if len(y) else 0.0
    accepted_returns = returns.to_numpy(dtype=float)[accepted]
    return {
        "samples": int(len(y)), "accepted": accepted_count,
        "coverage_pct": round(coverage * 100, 2),
        "precision_pct": round(precision * 100, 2),
        "accepted_avg_net_pct": round(float(np.mean(accepted_returns)), 6) if accepted_count else 0.0,
    }


def run_meta_label_validation(
    frame: pd.DataFrame,
    *,
    return_column: str = "normalized_net_return",
    feature_columns: Iterable[str] = DEFAULT_FEATURES,
    min_samples: int = 120,
) -> Dict[str, Any]:
    run_id = "meta_label_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    work = frame.copy()
    side_column = "normalized_side" if "normalized_side" in work.columns else "side" if "side" in work.columns else ""
    if side_column:
        work = work[work[side_column].astype(str).isin(["LONG", "SHORT"])]
    if "candle_timestamp" in work.columns:
        work["_time"] = pd.to_datetime(work["candle_timestamp"], utc=True, errors="coerce")
        work = work.sort_values("_time")
    returns = pd.to_numeric(work.get(return_column), errors="coerce")
    work = work[returns.notna()].copy()
    work["_return"] = returns[returns.notna()].astype(float)
    features: List[str] = [column for column in feature_columns if column in work.columns]
    blockers: List[str] = []
    if len(work) < min_samples:
        blockers.append(f"Meta-labeling requires at least {min_samples} complete directional samples; found {len(work)}.")
    if not features:
        blockers.append("No declared meta-label features are present.")
    if blockers:
        return {"run_id": run_id, "version": META_LABEL_MODEL_VERSION, "status": "META_LABEL_BLOCKED", "samples": int(len(work)), "features": features, "blockers": blockers, "warnings": []}

    split_col = "normalized_split" if "normalized_split" in work.columns else "replay_split" if "replay_split" in work.columns else ""
    if split_col:
        train = work[work[split_col].astype(str) == "TRAIN_60"]
        validation = work[work[split_col].astype(str) == "VALIDATION_20"]
        test = work[work[split_col].astype(str) == "TEST_20"]
    else:
        first, second = int(len(work) * 0.60), int(len(work) * 0.80)
        train, validation, test = work.iloc[:first], work.iloc[first:second], work.iloc[second:]
    if min(len(train), len(validation), len(test)) < 20:
        return {"run_id": run_id, "version": META_LABEL_MODEL_VERSION, "status": "META_LABEL_BLOCKED", "samples": int(len(work)), "features": features, "blockers": [f"Chronological split too small: train={len(train)}, validation={len(validation)}, test={len(test)}."], "warnings": []}

    y_train = (train["_return"] > 0).astype(int)
    if y_train.nunique() < 2:
        return {"run_id": run_id, "version": META_LABEL_MODEL_VERSION, "status": "META_LABEL_BLOCKED", "samples": int(len(work)), "features": features, "blockers": ["TRAIN contains only one outcome class."], "warnings": []}
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    model.fit(train[features], y_train)
    val_probability = model.predict_proba(validation[features])[:, 1]
    val_y = (validation["_return"] > 0).astype(int)
    candidates = []
    for threshold in np.arange(0.50, 0.81, 0.05):
        metric = _metrics(val_y, val_probability, float(threshold), validation["_return"])
        if metric["accepted"] >= max(10, int(len(validation) * 0.10)):
            candidates.append((metric["accepted_avg_net_pct"], metric["precision_pct"], -metric["coverage_pct"], float(threshold), metric))
    selected = max(candidates) if candidates else (0.0, 0.0, 0.0, 0.5, _metrics(val_y, val_probability, 0.5, validation["_return"]))
    threshold = selected[3]
    test_probability = model.predict_proba(test[features])[:, 1]
    test_y = (test["_return"] > 0).astype(int)
    test_metric = _metrics(test_y, test_probability, threshold, test["_return"])
    baseline_net = float(test["_return"].mean())
    edge_delta = test_metric["accepted_avg_net_pct"] - baseline_net
    status = "META_LABEL_SHADOW_CANDIDATE" if test_metric["accepted"] >= 20 and edge_delta > 0 and test_metric["accepted_avg_net_pct"] > 0 else "META_LABEL_NO_STABLE_EDGE"
    coefficients = model.named_steps["classifier"].coef_[0]
    attribution = sorted(
        [{"feature": name, "coefficient": round(float(value), 6)} for name, value in zip(features, coefficients)],
        key=lambda item: abs(item["coefficient"]), reverse=True,
    )
    return {
        "run_id": run_id, "version": META_LABEL_MODEL_VERSION, "status": status,
        "samples": int(len(work)), "features": features,
        "train_samples": int(len(train)), "validation_samples": int(len(validation)), "test_samples": int(len(test)),
        "selected_threshold_from_validation": round(threshold, 4),
        "validation": selected[4], "test": test_metric,
        "test_baseline_avg_net_pct": round(baseline_net, 6), "test_edge_delta_pct": round(edge_delta, 6),
        "feature_attribution": attribution, "blockers": [],
        "warnings": ["Shadow-only meta-label; TEST was not used to select its threshold."],
    }
