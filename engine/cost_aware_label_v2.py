"""Cost-aware Triple-Barrier labels and meta-label research for Freakto.

Labels use future outcome fields only after the event universe has been frozen.
No label field is permitted to detect an event or pass the pre-trade gate.
Intrabar ambiguity is conservatively resolved STOP_FIRST.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from engine.baseline_benchmarks import block_bootstrap_expectancy_ci, strategy_metrics
from engine.event_opportunity_universe import EventUniverseConfig, build_event_opportunity_universe
from engine.artifact_protocols import (
    DEFAULT_ARTIFACT_SELECTOR,
    GLOBAL_UTC_SELECTOR,
    resolve_artifact_route,
    validate_v3_upstream_purge_manifest,
    validate_v3_upstream_purge_metadata,
)
from engine.research_contracts import FUTURE_WALK_FORWARD_CONTRACT

VERSION = "2.0.0"
MODE = "COST_AWARE_EVENT_META_LABEL_DEVELOPMENT_ONLY"
SPLIT_PROTOCOL_VERSION = "upstream-preserving-60-20-20-purge6-v1"
UPSTREAM_SPLIT_COLUMN = "replay_split"
UPSTREAM_TO_DOWNSTREAM = {
    "TRAIN_60": "train",
    "VALIDATION_20": "optimize",
    "TEST_20": "holdout",
}

NET_RETURN_CANDIDATES = (
    "net_signed_return_after_{h}c_pct",
    "net_return_pct",
    "net_return_after_24h_pct",
)
GROSS_RETURN_CANDIDATES = (
    "gross_signed_return_after_{h}c_pct",
    "gross_return_pct",
)
COST_CANDIDATES = (
    "event_execution_cost_pct",
    "round_trip_cost_pct",
    "execution_cost_pct",
    "total_cost_pct",
    "estimated_round_trip_cost_pct",
    "fee_slippage_pct",
)

META_NUMERIC_FEATURES = (
    "trend_score",
    "momentum_score",
    "volume_score",
    "structure_score",
    "regime_score",
    "risk_penalty",
    "atr_pct",
    "rsi_14",
    "macd_histogram",
    "event_atr_expansion_ratio",
    "event_execution_cost_pct",
    "gross_target_to_cost",
    "net_reward_risk",
    "target_distance_pct",
    "stop_distance_pct",
    "event_count",
)
META_CATEGORICAL_FEATURES = ("primary_event", "side", "regime", "symbol", "timeframe", "event_source")


@dataclass(frozen=True)
class CostAwareLabelConfig:
    horizon_candles: int = 6
    ambiguity_policy: str = "STOP_FIRST"
    minimum_positive_net_pct: float = 0.0
    minimum_geometry_target_pct: float = 0.10

    def validate(self) -> None:
        if self.horizon_candles <= 0:
            raise ValueError("horizon_candles must be positive")
        if self.ambiguity_policy != "STOP_FIRST":
            raise ValueError("Only conservative STOP_FIRST is promotion-eligible")


@dataclass(frozen=True)
class EventMetaLabelConfig:
    event: EventUniverseConfig = field(default_factory=EventUniverseConfig)
    label: CostAwareLabelConfig = field(default_factory=CostAwareLabelConfig)
    train_fraction: float = 0.60
    optimize_fraction: float = 0.20
    purge_timestamps: int = FUTURE_WALK_FORWARD_CONTRACT.purge_timestamps
    minimum_train_events: int = 300
    minimum_optimize_events: int = 80
    minimum_holdout_events: int = 100
    probability_thresholds: Tuple[float, ...] = (0.50, 0.55, 0.60, 0.65, 0.70, 0.75)
    minimum_predicted_ev_pct: float = 0.0
    optimize_min_samples: int = 40
    optimize_min_expectancy_pct: float = 0.0
    optimize_min_profit_factor: float = 1.0
    walk_forward_folds: int = FUTURE_WALK_FORWARD_CONTRACT.walk_forward_folds
    minimum_walk_forward_train_events: int = FUTURE_WALK_FORWARD_CONTRACT.event_meta_minimum_fit_rows
    minimum_walk_forward_test_events: int = 60
    bootstrap_samples: int = 300
    bootstrap_block_size: int = 24
    random_seed: int = 42
    promotion_min_samples: int = 200
    promotion_min_expectancy_pct: float = 0.0
    promotion_min_profit_factor: float = 1.05
    promotion_min_positive_walk_forward_fraction: float = 2.0 / 3.0
    minimum_valid_walk_forward_folds: int = FUTURE_WALK_FORWARD_CONTRACT.minimum_valid_folds
    promotion_min_ci_low_pct: float = 0.0
    promotion_baseline_margin_pct: float = 0.02
    split_protocol_version: str = SPLIT_PROTOCOL_VERSION
    upstream_split_column: str = UPSTREAM_SPLIT_COLUMN
    artifact_selector: str = DEFAULT_ARTIFACT_SELECTOR
    upstream_split_manifest: Optional[Mapping[str, Any]] = None

    def validate(self) -> None:
        FUTURE_WALK_FORWARD_CONTRACT.validate()
        resolve_artifact_route(self.artifact_selector)
        if self.artifact_selector == GLOBAL_UTC_SELECTOR:
            validate_v3_upstream_purge_manifest(self.upstream_split_manifest)
        self.event.validate()
        self.label.validate()
        if not 0.40 <= self.train_fraction < 0.85:
            raise ValueError("train_fraction must be in [0.40, 0.85)")
        if not 0.05 <= self.optimize_fraction < 0.40:
            raise ValueError("optimize_fraction must be in [0.05, 0.40)")
        if self.train_fraction + self.optimize_fraction >= 0.95:
            raise ValueError("train + optimize must leave Holdout")
        if not self.probability_thresholds:
            raise ValueError("probability_thresholds cannot be empty")
        if self.split_protocol_version != SPLIT_PROTOCOL_VERSION:
            raise ValueError(f"split_protocol_version must be {SPLIT_PROTOCOL_VERSION}")
        if self.upstream_split_column != UPSTREAM_SPLIT_COLUMN:
            raise ValueError(f"upstream_split_column must be {UPSTREAM_SPLIT_COLUMN}")
        if int(self.purge_timestamps) != 6:
            raise ValueError("upstream-preserving split requires exactly 6 unique timestamp purges")
        if int(self.walk_forward_folds) != FUTURE_WALK_FORWARD_CONTRACT.walk_forward_folds:
            raise ValueError("future Event meta experiments require the authoritative four-fold contract")
        if int(self.minimum_valid_walk_forward_folds) != FUTURE_WALK_FORWARD_CONTRACT.minimum_valid_folds:
            raise ValueError("minimum valid folds must match the authoritative contract")


@dataclass(frozen=True)
class EventChronologicalSplit:
    train: pd.DataFrame
    optimize: pd.DataFrame
    holdout: pd.DataFrame
    boundaries: Dict[str, str]
    manifest: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventMetaModel:
    pipeline: Pipeline
    numeric_features: List[str]
    categorical_features: List[str]
    average_win_pct: float
    average_loss_pct: float
    train_rows: int
    train_positive_rate: float


@dataclass(frozen=True)
class MetaThresholdSelection:
    threshold: Optional[float]
    eligible: bool
    reason: str
    candidate_rows: List[Dict[str, Any]]


def _first_existing(frame: pd.DataFrame, candidates: Sequence[str]) -> Optional[str]:
    return next((column for column in candidates if column in frame.columns), None)


def _bool_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(False, index=frame.index, dtype=bool)
    values = frame[column]
    numeric = pd.to_numeric(values, errors="coerce")
    text = values.astype("string").fillna("").str.strip().str.lower()
    return numeric.fillna(0).ne(0) | text.isin({"true", "yes", "y", "1", "hit", "target", "stop"})


def _numeric(frame: pd.DataFrame, candidates: Sequence[str], default: float = np.nan) -> pd.Series:
    column = _first_existing(frame, candidates)
    if column is None:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _normalized_reason(value: Any) -> str:
    text = str(value or "").strip().upper()
    if "TARGET" in text or text in {"TP", "TAKE_PROFIT"}:
        return "TARGET"
    if "STOP" in text or text in {"SL", "STOP_LOSS"}:
        return "STOP"
    return "TIME"


def build_cost_aware_labels(
    event_rows: pd.DataFrame,
    config: Optional[CostAwareLabelConfig] = None,
) -> pd.DataFrame:
    config = config or CostAwareLabelConfig()
    config.validate()
    if event_rows is None or event_rows.empty:
        return pd.DataFrame(columns=list(event_rows.columns) if isinstance(event_rows, pd.DataFrame) else [])
    work = event_rows.copy()
    horizon = int(config.horizon_candles)
    cost = _numeric(work, COST_CANDIDATES, 0.0).fillna(0.0).clip(lower=0.0)
    net_candidates = tuple(name.format(h=horizon) for name in NET_RETURN_CANDIDATES)
    gross_candidates = tuple(name.format(h=horizon) for name in GROSS_RETURN_CANDIDATES)
    fixed_net = _numeric(work, net_candidates, np.nan)
    fixed_gross = _numeric(work, gross_candidates, np.nan)
    fixed_gross = fixed_gross.where(fixed_gross.notna(), fixed_net + cost)

    target_distance = pd.to_numeric(work.get("target_distance_pct"), errors="coerce")
    stop_distance = pd.to_numeric(work.get("stop_distance_pct"), errors="coerce")
    target_hit = _bool_series(work, "target_1_hit") | _bool_series(work, "target_hit")
    stop_hit = _bool_series(work, "stop_hit")
    ambiguity = _bool_series(work, "intrabar_ambiguity") | (target_hit & stop_hit)
    first_reason = work.get("first_exit_reason", pd.Series("", index=work.index)).map(_normalized_reason)
    first_offset = pd.to_numeric(work.get("first_exit_candle_offset", pd.Series(np.nan, index=work.index)), errors="coerce")
    within_horizon = first_offset.isna() | first_offset.le(horizon)

    barrier = pd.Series("TIME_EXIT", index=work.index, dtype=object)
    explicit_target = first_reason.eq("TARGET") & within_horizon
    explicit_stop = first_reason.eq("STOP") & within_horizon
    inferred_target = target_hit & ~stop_hit
    inferred_stop = stop_hit & ~target_hit
    barrier.loc[explicit_target | inferred_target] = "TAKE_PROFIT"
    barrier.loc[explicit_stop | inferred_stop] = "STOP_LOSS"
    # Conservative same-candle/path ambiguity always resolves to Stop.
    barrier.loc[ambiguity & target_hit & stop_hit] = "STOP_LOSS"

    valid_target = target_distance.ge(config.minimum_geometry_target_pct)
    valid_stop = stop_distance.gt(0)
    barrier.loc[barrier.eq("TAKE_PROFIT") & ~valid_target] = "TIME_EXIT"
    barrier.loc[barrier.eq("STOP_LOSS") & ~valid_stop] = "TIME_EXIT"

    gross = fixed_gross.copy()
    net = fixed_net.copy()
    take = barrier.eq("TAKE_PROFIT")
    stopped = barrier.eq("STOP_LOSS")
    gross.loc[take] = target_distance.loc[take]
    net.loc[take] = target_distance.loc[take] - cost.loc[take]
    gross.loc[stopped] = -stop_distance.loc[stopped]
    net.loc[stopped] = -stop_distance.loc[stopped] - cost.loc[stopped]

    missing_net = net.isna()
    net.loc[missing_net] = 0.0
    gross.loc[gross.isna()] = net.loc[gross.isna()] + cost.loc[gross.isna()]

    work["triple_barrier_label"] = barrier
    work["label_horizon_candles"] = horizon
    work["label_ambiguity_policy"] = config.ambiguity_policy
    work["label_source"] = np.where(
        take | stopped,
        "FIRST_TOUCH_OR_REPLAY_FLAGS",
        "FIXED_HORIZON_TIME_EXIT",
    )
    work["realized_gross_return_pct"] = gross.astype(float)
    work["realized_net_return_pct"] = net.astype(float)
    work["realized_cost_drag_pct"] = (gross - net).clip(lower=0.0)
    work["meta_label"] = net.gt(config.minimum_positive_net_pct).astype(int)
    work["no_trade_return_pct"] = 0.0
    work["trade_vs_no_trade_delta_pct"] = net.astype(float)
    work["label_is_cost_aware"] = True
    return work


def _provenance_violation(message: str) -> ValueError:
    return ValueError(f"UPSTREAM_SPLIT_PROVENANCE_VIOLATION: {message}")


def _split_summary(frame: pd.DataFrame) -> Dict[str, Any]:
    timestamps = pd.Index(frame["__timestamp"].dropna().sort_values().unique())
    return {
        "rows": int(len(frame)),
        "unique_timestamps": int(len(timestamps)),
        "first_timestamp_utc": pd.Timestamp(timestamps[0]).isoformat() if len(timestamps) else None,
        "last_timestamp_utc": pd.Timestamp(timestamps[-1]).isoformat() if len(timestamps) else None,
    }


def _pairwise_overlap_counts(
    train: pd.DataFrame,
    optimize: pd.DataFrame,
    holdout: pd.DataFrame,
) -> Dict[str, Dict[str, int]]:
    frames = {"train": train, "optimize": optimize, "holdout": holdout}
    result: Dict[str, Dict[str, int]] = {}
    for left, right in (("train", "optimize"), ("train", "holdout"), ("optimize", "holdout")):
        result[f"{left}_{right}"] = {
            "timestamps": int(len(set(frames[left]["__timestamp"]) & set(frames[right]["__timestamp"]))),
            "decision_ids": int(len(set(frames[left]["decision_id"]) & set(frames[right]["decision_id"]))),
        }
    return result


def _validate_upstream_split_frame(
    frame: pd.DataFrame,
    config: EventMetaLabelConfig,
) -> pd.DataFrame:
    required = {"__timestamp", "decision_id", config.upstream_split_column}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise _provenance_violation(f"missing required columns: {', '.join(missing)}")
    work = frame.copy()
    if work["__timestamp"].isna().any():
        raise _provenance_violation(
            f"null timestamps detected: {int(work['__timestamp'].isna().sum())}"
        )
    if work["decision_id"].isna().any():
        raise _provenance_violation(
            f"null decision_id values detected: {int(work['decision_id'].isna().sum())}"
        )
    duplicate_count = int(work["decision_id"].duplicated(keep=False).sum())
    if duplicate_count:
        raise _provenance_violation(f"duplicate decision_id rows detected: {duplicate_count}")
    provenance = work[config.upstream_split_column]
    if provenance.isna().any():
        raise _provenance_violation(
            f"null {config.upstream_split_column} values detected: {int(provenance.isna().sum())}"
        )
    normalized = provenance.astype(str).str.strip().str.upper()
    unknown = sorted(set(normalized) - set(UPSTREAM_TO_DOWNSTREAM))
    if unknown:
        counts = normalized[normalized.isin(unknown)].value_counts().to_dict()
        raise _provenance_violation(f"unknown replay_split labels: {counts}")
    work[config.upstream_split_column] = normalized
    work["__timestamp"] = pd.to_datetime(work["__timestamp"], utc=True, errors="coerce")
    if work["__timestamp"].isna().any():
        raise _provenance_violation(
            f"invalid timestamps detected: {int(work['__timestamp'].isna().sum())}"
        )
    return work.sort_values(["__timestamp", "decision_id"], kind="stable").reset_index(drop=True)


def _purge_first_unique_timestamps(
    frame: pd.DataFrame,
    count: int,
    *,
    boundary: str,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    unique = pd.Index(frame["__timestamp"].dropna().sort_values().unique())
    if len(unique) <= count:
        raise _provenance_violation(
            f"{boundary} has {len(unique)} unique timestamps; cannot purge {count}"
        )
    removed_timestamps = unique[:count]
    removed = frame[frame["__timestamp"].isin(removed_timestamps)].copy()
    retained = frame[~frame["__timestamp"].isin(removed_timestamps)].copy()
    return retained, {
        "boundary": boundary,
        "removed_from": "VALIDATION_20" if boundary == "TRAIN_60_TO_VALIDATION_20" else "TEST_20",
        "rows_removed": int(len(removed)),
        "unique_timestamps_removed": int(len(removed_timestamps)),
        "first_removed_timestamp_utc": pd.Timestamp(removed_timestamps[0]).isoformat(),
        "last_removed_timestamp_utc": pd.Timestamp(removed_timestamps[-1]).isoformat(),
    }


def chronological_event_split(
    frame: pd.DataFrame,
    config: EventMetaLabelConfig,
) -> EventChronologicalSplit:
    """Preserve replay provenance and purge the downstream side of each boundary."""
    config.validate()
    if frame is None or frame.empty:
        raise ValueError("event label frame is empty")
    if config.artifact_selector == GLOBAL_UTC_SELECTOR:
        validate_v3_upstream_purge_metadata(frame)
    work = _validate_upstream_split_frame(frame, config)
    column = config.upstream_split_column
    upstream = {
        label: work[work[column].eq(label)].copy()
        for label in UPSTREAM_TO_DOWNSTREAM
    }
    empty = [label for label, rows in upstream.items() if rows.empty]
    if empty:
        raise _provenance_violation(f"empty upstream splits: {', '.join(empty)}")
    if not (
        upstream["TRAIN_60"]["__timestamp"].max()
        < upstream["VALIDATION_20"]["__timestamp"].min()
        < upstream["TEST_20"]["__timestamp"].min()
    ):
        raise _provenance_violation(
            "invalid upstream chronological order before purge"
        )

    train = upstream["TRAIN_60"]
    optimize, train_optimize_purge = _purge_first_unique_timestamps(
        upstream["VALIDATION_20"],
        int(config.purge_timestamps),
        boundary="TRAIN_60_TO_VALIDATION_20",
    )
    holdout, optimize_holdout_purge = _purge_first_unique_timestamps(
        upstream["TEST_20"],
        int(config.purge_timestamps),
        boundary="VALIDATION_20_TO_TEST_20",
    )
    if min(len(train), len(optimize), len(holdout)) == 0:
        raise _provenance_violation("purge produced an empty downstream role")

    provenance_matrix = {
        "test_rows_in_train": int(train[column].eq("TEST_20").sum()),
        "test_rows_in_optimize": int(optimize[column].eq("TEST_20").sum()),
        "train_rows_in_optimize": int(optimize[column].eq("TRAIN_60").sum()),
        "train_rows_in_holdout": int(holdout[column].eq("TRAIN_60").sum()),
        "validation_rows_in_train": int(train[column].eq("VALIDATION_20").sum()),
        "validation_rows_in_holdout": int(holdout[column].eq("VALIDATION_20").sum()),
    }
    violations = {name: value for name, value in provenance_matrix.items() if value}
    if violations:
        raise _provenance_violation(f"forbidden downstream provenance counts: {violations}")

    overlap = _pairwise_overlap_counts(train, optimize, holdout)
    overlap_violations = {
        pair: counts for pair, counts in overlap.items() if any(counts.values())
    }
    if overlap_violations:
        raise _provenance_violation(f"downstream overlap detected: {overlap_violations}")
    if not (
        train["__timestamp"].max()
        < optimize["__timestamp"].min()
        < holdout["__timestamp"].min()
    ):
        raise _provenance_violation("invalid chronological order after upstream mapping and purge")

    boundaries = {
        "train_end_utc": pd.Timestamp(train["__timestamp"].max()).isoformat(),
        "optimize_start_utc": pd.Timestamp(optimize["__timestamp"].min()).isoformat(),
        "optimize_end_utc": pd.Timestamp(optimize["__timestamp"].max()).isoformat(),
        "holdout_start_utc": pd.Timestamp(holdout["__timestamp"].min()).isoformat(),
        "purge_timestamps": str(config.purge_timestamps),
    }
    input_fingerprints = (
        sorted(work["replay_data_fingerprint"].dropna().astype(str).unique())
        if "replay_data_fingerprint" in work.columns
        else []
    )
    experiment_ids = (
        sorted(work["replay_experiment_id"].dropna().astype(str).unique())
        if "replay_experiment_id" in work.columns
        else []
    )
    manifest = {
        "split_protocol_version": config.split_protocol_version,
        "artifact_selector": config.artifact_selector,
        "upstream_split_protocol": resolve_artifact_route(config.artifact_selector).split_protocol,
        "upstream_split_profile": resolve_artifact_route(config.artifact_selector).split_profile,
        "upstream_provenance_column": column,
        "input_replay_fingerprints": input_fingerprints,
        "input_replay_experiment_ids": experiment_ids,
        "allowed_provenance_mapping": dict(UPSTREAM_TO_DOWNSTREAM),
        "input_upstream_splits": {
            label: _split_summary(rows) for label, rows in upstream.items()
        },
        "retained_downstream_roles": {
            "train": _split_summary(train),
            "optimize": _split_summary(optimize),
            "holdout": _split_summary(holdout),
        },
        "purge": {
            "size": int(config.purge_timestamps),
            "unit": "unique timestamps",
            "train_to_optimize": train_optimize_purge,
            "optimize_to_holdout": optimize_holdout_purge,
        },
        "purge_owner": "EVENT_PIPELINE",
        "purge_applied": True,
        "purge_timestamps": int(config.purge_timestamps),
        "purge_unit": "unique UTC timestamps",
        "boundaries": boundaries,
        "overlap_counts": overlap,
        **provenance_matrix,
        "leakage_validation": "PASSED_UPSTREAM_SPLIT_PROVENANCE",
    }
    return EventChronologicalSplit(
        train=train.reset_index(drop=True),
        optimize=optimize.reset_index(drop=True),
        holdout=holdout.reset_index(drop=True),
        boundaries=boundaries,
        manifest=manifest,
    )


def _available_features(frame: pd.DataFrame) -> Tuple[List[str], List[str]]:
    numeric = [name for name in META_NUMERIC_FEATURES if name in frame.columns]
    categorical = [name for name in META_CATEGORICAL_FEATURES if name in frame.columns]
    if not numeric:
        raise ValueError("no numeric entry-time features are available for meta-labeling")
    return numeric, categorical


def _reject_test_rows_from_tuning(frame: pd.DataFrame, stage: str) -> None:
    if UPSTREAM_SPLIT_COLUMN not in frame.columns:
        raise _provenance_violation(
            f"missing required columns before {stage}: {UPSTREAM_SPLIT_COLUMN}"
        )
    provenance = frame[UPSTREAM_SPLIT_COLUMN]
    nulls = int(provenance.isna().sum())
    if nulls:
        raise _provenance_violation(
            f"null {UPSTREAM_SPLIT_COLUMN} values before {stage}: {nulls}"
        )
    test_rows = int(provenance.astype(str).str.upper().eq("TEST_20").sum())
    if test_rows:
        raise _provenance_violation(
            f"TEST_20 rows detected in {stage}: {test_rows}"
        )


def fit_event_meta_model(train: pd.DataFrame, config: EventMetaLabelConfig) -> EventMetaModel:
    _reject_test_rows_from_tuning(train, "model fitting")
    if len(train) < config.minimum_train_events:
        raise ValueError(f"at least {config.minimum_train_events} train events are required")
    training = train[train["cost_gate_pass"].astype(bool)].copy()
    if len(training) < config.minimum_train_events:
        raise ValueError("insufficient cost-gated train events")
    target = pd.to_numeric(training["meta_label"], errors="coerce").fillna(0).astype(int)
    if target.nunique() < 2:
        raise ValueError("meta-label target has only one class")
    numeric, categorical = _available_features(training)
    numeric_pipe = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", RobustScaler())])
    categorical_pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    transformer = ColumnTransformer(
        [("num", numeric_pipe, numeric), ("cat", categorical_pipe, categorical)],
        remainder="drop",
    )
    pipeline = Pipeline(
        [
            ("features", transformer),
            (
                "model",
                LogisticRegression(
                    C=0.35,
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=config.random_seed,
                ),
            ),
        ]
    )
    pipeline.fit(training[numeric + categorical], target)
    returns = pd.to_numeric(training["realized_net_return_pct"], errors="coerce").dropna()
    wins = returns[returns > 0]
    losses = returns[returns <= 0]
    return EventMetaModel(
        pipeline=pipeline,
        numeric_features=numeric,
        categorical_features=categorical,
        average_win_pct=float(wins.mean()) if not wins.empty else 0.0,
        average_loss_pct=float(losses.mean()) if not losses.empty else 0.0,
        train_rows=int(len(training)),
        train_positive_rate=float(target.mean()),
    )


def predict_event_meta(model: EventMetaModel, frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    columns = model.numeric_features + model.categorical_features
    for column in columns:
        if column not in result.columns:
            result[column] = np.nan if column in model.numeric_features else "UNKNOWN"
    probabilities = model.pipeline.predict_proba(result[columns])[:, 1]
    result["predicted_meta_probability"] = probabilities
    result["predicted_event_ev_pct"] = (
        probabilities * model.average_win_pct + (1.0 - probabilities) * model.average_loss_pct
    )
    return result


def _metrics(returns: Sequence[float], total_rows: int) -> Dict[str, Any]:
    return strategy_metrics(returns, total_rows=total_rows)


def select_meta_threshold(
    optimize_predictions: pd.DataFrame,
    config: EventMetaLabelConfig,
) -> MetaThresholdSelection:
    _reject_test_rows_from_tuning(optimize_predictions, "threshold selection")
    records: List[Dict[str, Any]] = []
    for threshold in config.probability_thresholds:
        selected = optimize_predictions[
            optimize_predictions["cost_gate_pass"].astype(bool)
            & optimize_predictions["predicted_meta_probability"].ge(float(threshold))
            & optimize_predictions["predicted_event_ev_pct"].ge(config.minimum_predicted_ev_pct)
        ]
        metrics = _metrics(selected["realized_net_return_pct"], len(optimize_predictions))
        eligible = (
            metrics["sample_count"] >= config.optimize_min_samples
            and metrics["expectancy"] > config.optimize_min_expectancy_pct
            and metrics["profit_factor"] >= config.optimize_min_profit_factor
        )
        records.append({"threshold": float(threshold), "eligible": bool(eligible), **metrics})
    eligible_records = [row for row in records if row["eligible"]]
    if not eligible_records:
        return MetaThresholdSelection(None, False, "No Optimize threshold passed constraints", records)
    best = max(eligible_records, key=lambda row: (row["expectancy"], row["profit_factor"], row["sample_count"]))
    return MetaThresholdSelection(float(best["threshold"]), True, "Optimize-selected threshold", records)


def apply_meta_threshold(
    predictions: pd.DataFrame,
    selection: MetaThresholdSelection,
) -> pd.DataFrame:
    if not selection.eligible or selection.threshold is None:
        return predictions.iloc[0:0].copy()
    return predictions[
        predictions["cost_gate_pass"].astype(bool)
        & predictions["predicted_meta_probability"].ge(selection.threshold)
        & predictions["predicted_event_ev_pct"].ge(0.0)
    ].copy()


def event_meta_coefficients(model: EventMetaModel) -> pd.DataFrame:
    transformer = model.pipeline.named_steps["features"]
    classifier = model.pipeline.named_steps["model"]
    try:
        names = transformer.get_feature_names_out()
    except Exception:
        names = np.array(model.numeric_features + model.categorical_features, dtype=object)
    coefficients = classifier.coef_[0]
    length = min(len(names), len(coefficients))
    return pd.DataFrame(
        {
            "feature": [str(name) for name in names[:length]],
            "coefficient": coefficients[:length].astype(float),
        }
    ).sort_values("coefficient", ascending=False).reset_index(drop=True)


def event_family_benchmarks(frame: pd.DataFrame, *, scope: str) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    records: List[Dict[str, Any]] = []
    total = len(frame)
    scopes: List[Tuple[str, pd.DataFrame]] = [
        ("EVENT_ANY", frame),
        ("EVENT_COST_GATED", frame[frame["cost_gate_pass"].astype(bool)]),
    ]
    for event_name in sorted(frame["primary_event"].dropna().astype(str).unique()):
        event = frame[frame["primary_event"].astype(str).eq(event_name)]
        scopes.append((f"EVENT_{event_name}", event))
        scopes.append((f"EVENT_{event_name}_COST_GATED", event[event["cost_gate_pass"].astype(bool)]))
    for name, rows in scopes:
        records.append({"scope": scope, "strategy": name, **_metrics(rows["realized_net_return_pct"], total)})
    return pd.DataFrame(records)


def walk_forward_event_meta(frame: pd.DataFrame, config: EventMetaLabelConfig) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()
    work = _validate_upstream_split_frame(frame, config)
    forbidden = int(work[config.upstream_split_column].eq("TEST_20").sum())
    if forbidden:
        raise _provenance_violation(
            f"TEST_20 rows detected in walk-forward tuning: {forbidden}"
        )
    unique = pd.Index(work["__timestamp"].dropna().sort_values().unique())
    folds = max(1, int(config.walk_forward_folds))
    boundaries = np.linspace(0.45, 1.0, folds + 1)
    records: List[Dict[str, Any]] = []
    for fold in range(folds):
        train_end_pos = int(len(unique) * boundaries[fold])
        test_end_pos = int(len(unique) * boundaries[fold + 1])
        if train_end_pos <= config.purge_timestamps or test_end_pos <= train_end_pos + config.purge_timestamps:
            continue
        train_end = unique[train_end_pos - 1]
        test_start = unique[min(len(unique) - 1, train_end_pos + config.purge_timestamps)]
        test_end = unique[min(len(unique) - 1, test_end_pos - 1)]
        train_all = work[work["__timestamp"] <= train_end].copy()
        test = work[(work["__timestamp"] >= test_start) & (work["__timestamp"] <= test_end)].copy()
        if len(train_all) < config.minimum_walk_forward_train_events or len(test) < config.minimum_walk_forward_test_events:
            continue
        train_unique = pd.Index(train_all["__timestamp"].sort_values().unique())
        opt_start = train_unique[max(1, int(len(train_unique) * 0.80))]
        fit = train_all[train_all["__timestamp"] < opt_start].copy()
        optimize = train_all[train_all["__timestamp"] >= opt_start].copy()
        try:
            model = fit_event_meta_model(fit, config)
            opt_pred = predict_event_meta(model, optimize)
            selection = select_meta_threshold(opt_pred, config)
            test_pred = predict_event_meta(model, test)
            selected = apply_meta_threshold(test_pred, selection)
            metrics = _metrics(selected["realized_net_return_pct"], len(test))
            records.append(
                {
                    "fold": fold + 1,
                    "train_end_utc": pd.Timestamp(train_end).isoformat(),
                    "test_start_utc": pd.Timestamp(test_start).isoformat(),
                    "test_end_utc": pd.Timestamp(test_end).isoformat(),
                    "threshold": selection.threshold,
                    "threshold_eligible": selection.eligible,
                    "no_overlap": bool(train_all["__timestamp"].max() < test["__timestamp"].min()),
                    **metrics,
                    "positive": bool(metrics["expectancy"] > 0 and metrics["profit_factor"] >= 1.0),
                }
            )
        except ValueError as exc:
            records.append({"fold": fold + 1, "error": str(exc), "positive": False, "no_overlap": True})
    return pd.DataFrame(records)


def evaluate_frozen_event_candidate(
    model_path: str | Path,
    fresh_rows: pd.DataFrame,
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    payload = joblib.load(model_path)
    config: EventMetaLabelConfig = payload["config"]
    event_rows, _ = build_event_opportunity_universe(fresh_rows, config.event, time_scope="fresh")
    labels = build_cost_aware_labels(event_rows, config.label)
    predictions = predict_event_meta(payload["model"], labels)
    selected = apply_meta_threshold(predictions, payload["selection"])
    metrics = _metrics(selected["realized_net_return_pct"], len(labels))
    result = {
        "status": "FRESH_OOS_FIXED_EVALUATION",
        "fresh_event_rows": int(len(labels)),
        "selected_rows": int(len(selected)),
        **metrics,
        "model_refit": False,
        "thresholds_reselected": False,
        "promotion_applied": False,
        "paper_live_enabled": False,
    }
    return result, selected
