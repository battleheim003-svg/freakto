"""Freakto Feature Architecture v2 (research-only).

This module builds a score-independent, interpretable feature architecture for
chronological research.  It deliberately does **not** modify the runtime
DecisionEngine, score weights, Paper settings, or Live settings.

Design principles
-----------------
* LONG and SHORT are fitted independently.
* Aggregate ``score`` is metadata only and is never a model feature.
* Structure is represented as an entry gate, not an additive score.
* Momentum is capped and can be removed through a pre-declared variant.
* Volatility, execution cost, and planned trade geometry are normalized.
* Outcome/leakage fields are rejected from model features.
* Splits are chronological on unique timestamps with purge gaps.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from engine.multi_cycle_validation import normalize_replay_rows

VERSION = "2.0.0"
MODE = "FEATURE_ARCHITECTURE_V2_DEVELOPMENT_ONLY"

LEAKAGE_TOKENS = (
    "return",
    "outcome",
    "future",
    "win",
    "loss",
    "target_hit",
    "stop_hit",
    "mfe",
    "mae",
    "exit_price",
    "direction_correct",
    "label",
)

TIMESTAMP_CANDIDATES = (
    "candle_timestamp",
    "timestamp_utc",
    "timestamp",
    "feature_cutoff_timestamp",
)

ALIASES: Mapping[str, Tuple[str, ...]] = {
    "trend_score": ("trend_score",),
    "momentum_score": ("momentum_score",),
    "volume_score": ("volume_score",),
    "structure_score": ("structure_score",),
    "regime_score": ("regime_score",),
    "risk_penalty": ("risk_penalty",),
    "atr_pct": ("atr_pct", "atr_percent", "atr_14_pct", "atr_ratio_pct"),
    "rsi": ("rsi_14", "rsi"),
    "macd_hist": ("macd_histogram", "macd_hist", "macd_diff"),
    "execution_cost_pct": (
        "round_trip_cost_pct",
        "execution_cost_pct",
        "total_cost_pct",
        "estimated_round_trip_cost_pct",
        "fee_slippage_pct",
    ),
    "entry_price": ("entry_price", "entry_mid", "planned_entry_price"),
    "target_price": ("target_1", "target1", "target_1_price", "target_price"),
    "stop_price": ("stop_price", "stop", "planned_stop_price"),
    "market_return": (
        "market_return_after_6c_pct",
        "raw_market_return_after_6c_pct",
        "unsigned_market_return_after_6c_pct",
    ),
}

BASE_NUMERIC_FEATURES = (
    "trend_norm",
    "momentum_capped",
    "volume_confirm",
    "regime_norm",
    "risk_norm",
    "atr_log",
    "rsi_centered",
    "macd_per_vol",
    "cost_pct",
    "cost_to_atr",
    "net_reward_risk",
    "trend_per_vol",
    "momentum_per_vol",
    "trend_volume_interaction",
    "structure_gate",
)


@dataclass(frozen=True)
class FeatureArchitectureV2Config:
    development_cutoff_utc: str = "2026-07-09T12:00:00Z"
    train_fraction: float = 0.60
    optimize_fraction: float = 0.20
    purge_timestamps: int = 6
    ridge_alpha: float = 12.0
    logistic_c: float = 0.35
    minimum_train_samples_per_side: int = 250
    minimum_optimize_samples: int = 80
    minimum_holdout_samples: int = 100
    structure_gate_min: float = 4.0
    volume_gate_min: float = 0.0
    maximum_risk_penalty: float = 25.0
    maximum_cost_to_atr: float = 1.0
    minimum_net_reward_risk: float = 0.0
    expected_return_thresholds: Tuple[float, ...] = (-0.10, 0.0, 0.05, 0.10, 0.20, 0.35, 0.50)
    optimize_min_profit_factor: float = 1.0
    optimize_min_expectancy_pct: float = 0.0
    random_state: int = 42
    categorical_columns: Tuple[str, ...] = ("regime", "symbol")

    def validate(self) -> None:
        cutoff = pd.Timestamp(self.development_cutoff_utc)
        if cutoff.tzinfo is None:
            raise ValueError("development_cutoff_utc must include a timezone")
        if not 0.40 <= self.train_fraction < 0.85:
            raise ValueError("train_fraction must be in [0.40, 0.85)")
        if not 0.05 <= self.optimize_fraction < 0.40:
            raise ValueError("optimize_fraction must be in [0.05, 0.40)")
        if self.train_fraction + self.optimize_fraction >= 0.95:
            raise ValueError("train + optimize must leave a Holdout segment")
        if self.purge_timestamps < 0:
            raise ValueError("purge_timestamps cannot be negative")
        if self.minimum_train_samples_per_side < 10:
            raise ValueError("minimum_train_samples_per_side is too small")
        if not self.expected_return_thresholds:
            raise ValueError("expected_return_thresholds cannot be empty")


@dataclass(frozen=True)
class ChronologicalSplit:
    train: pd.DataFrame
    optimize: pd.DataFrame
    holdout: pd.DataFrame
    boundaries: Dict[str, str]


@dataclass
class SideModel:
    side: str
    variant: str
    feature_columns: List[str]
    return_pipeline: Pipeline
    win_pipeline: Optional[Pipeline]
    average_win_pct: float
    average_loss_pct: float
    train_rows: int
    gate_diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitectureBundle:
    variant: str
    models: Dict[str, SideModel]
    config: FeatureArchitectureV2Config
    available_features: List[str]
    unavailable_features: List[str]


@dataclass(frozen=True)
class ThresholdSelection:
    side: str
    threshold: Optional[float]
    eligible: bool
    reason: str
    candidate_rows: List[Dict[str, Any]]


def validate_entry_feature_names(features: Sequence[str]) -> None:
    """Reject outcome-derived or aggregate-score fields from the model."""
    for name in features:
        lowered = str(name).strip().lower()
        if not lowered:
            raise ValueError("feature names cannot be empty")
        if lowered == "score" or lowered.endswith("_score") and lowered not in {
            "trend_score",
            "momentum_score",
            "volume_score",
            "regime_score",
            "structure_score",
        }:
            raise ValueError(f"Aggregate/unsupported score cannot be a v2 model feature: {name}")
        if any(token in lowered for token in LEAKAGE_TOKENS):
            raise ValueError(f"Outcome/leakage field cannot be a v2 model feature: {name}")


def _first_existing(frame: pd.DataFrame, aliases: Sequence[str]) -> Optional[str]:
    return next((column for column in aliases if column in frame.columns), None)


def _numeric_alias(frame: pd.DataFrame, key: str, default: float = np.nan) -> pd.Series:
    column = _first_existing(frame, ALIASES[key])
    if column is None:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce")


def _safe_divide(numerator: pd.Series, denominator: pd.Series, floor: float = 1e-6) -> pd.Series:
    den = pd.to_numeric(denominator, errors="coerce").abs().clip(lower=floor)
    return pd.to_numeric(numerator, errors="coerce") / den


def _recover_mixed_timestamps(frame: pd.DataFrame) -> pd.DataFrame:
    standard = normalize_replay_rows(frame)
    if len(standard) >= max(1, int(len(frame) * 0.95)):
        return standard
    work = frame.copy()
    ts_col = _first_existing(work, TIMESTAMP_CANDIDATES)
    if ts_col is None:
        return standard
    try:
        work["__timestamp"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce", format="mixed")
    except TypeError:
        work["__timestamp"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce")
    return_col = next((c for c in ("net_signed_return_after_6c_pct", "net_return_pct", "net_signed_return_after_12c_pct") if c in work.columns), None)
    if return_col is None:
        return standard
    work["__return"] = pd.to_numeric(work[return_col], errors="coerce")
    if "side" not in work.columns:
        work["side"] = "NEUTRAL"
    if "regime" not in work.columns:
        work["regime"] = "UNKNOWN"
    work["side"] = work["side"].fillna("NEUTRAL").astype(str).str.upper()
    work["regime"] = work["regime"].fillna("UNKNOWN").astype(str).str.upper()
    if "score" not in work.columns:
        work["score"] = np.nan
    work["score"] = pd.to_numeric(work["score"], errors="coerce")
    recovered = work.dropna(subset=["__timestamp", "__return"]).sort_values("__timestamp").reset_index(drop=True)
    return recovered if len(recovered) > len(standard) else standard


def prepare_architecture_rows(
    frame: pd.DataFrame, config: FeatureArchitectureV2Config, *, time_scope: str = "development"
) -> pd.DataFrame:
    """Normalize, deduplicate, enforce the requested time scope, and retain directional rows.

    ``development`` keeps rows at or before the frozen cutoff. ``fresh`` keeps
    rows strictly after it. No scope ever mixes both populations.
    """
    config.validate()
    if frame is None or frame.empty:
        return pd.DataFrame()
    work = _recover_mixed_timestamps(frame)
    cutoff = pd.Timestamp(config.development_cutoff_utc)
    if time_scope == "development":
        work = work[work["__timestamp"] <= cutoff].copy()
    elif time_scope == "fresh":
        work = work[work["__timestamp"] > cutoff].copy()
    else:
        raise ValueError("time_scope must be development or fresh")
    work = work[work["side"].isin(["LONG", "SHORT"])].copy()
    if "decision_id" in work.columns:
        work = work.sort_values("__timestamp").drop_duplicates("decision_id", keep="last")
    else:
        keys = [c for c in ("symbol", "timeframe", "side") if c in work.columns]
        keys.append("__timestamp")
        work = work.sort_values("__timestamp").drop_duplicates(keys, keep="last")
    return work.sort_values("__timestamp").reset_index(drop=True)


def engineer_entry_features(
    frame: pd.DataFrame, config: FeatureArchitectureV2Config, *, time_scope: str = "development"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create score-independent, entry-time features.

    The output preserves metadata and ``__return`` for research evaluation, but
    the returned diagnostics explicitly list which source fields were present.
    """
    work = prepare_architecture_rows(frame, config, time_scope=time_scope)
    if work.empty:
        return work, {"available_sources": [], "unavailable_sources": list(ALIASES)}

    trend = _numeric_alias(work, "trend_score")
    momentum = _numeric_alias(work, "momentum_score")
    volume = _numeric_alias(work, "volume_score")
    structure = _numeric_alias(work, "structure_score")
    regime_score = _numeric_alias(work, "regime_score")
    risk = _numeric_alias(work, "risk_penalty")
    atr = _numeric_alias(work, "atr_pct")
    rsi = _numeric_alias(work, "rsi")
    macd = _numeric_alias(work, "macd_hist")
    cost = _numeric_alias(work, "execution_cost_pct")
    entry = _numeric_alias(work, "entry_price")
    target = _numeric_alias(work, "target_price")
    stop = _numeric_alias(work, "stop_price")

    result = work.copy()
    result["trend_norm"] = (trend / 28.0).clip(-1.5, 1.5)
    result["momentum_capped"] = ((momentum - 15.0) / 15.0).clip(-1.0, 1.0)
    result["volume_confirm"] = (volume / 20.0).clip(-1.0, 1.5)
    result["regime_norm"] = (regime_score / 10.0).clip(-1.5, 1.5)
    result["risk_norm"] = (risk / 25.0).clip(0.0, 2.0)
    result["atr_log"] = np.log1p(atr.clip(lower=0.0))
    result["rsi_centered"] = ((rsi - 50.0) / 50.0).clip(-1.0, 1.0)
    result["macd_per_vol"] = _safe_divide(macd, atr.replace(0, np.nan)).clip(-10.0, 10.0)
    result["cost_pct"] = cost.clip(lower=0.0)
    result["cost_to_atr"] = _safe_divide(cost, atr.replace(0, np.nan)).clip(0.0, 10.0)

    entry_abs = entry.abs().replace(0, np.nan)
    target_distance = (target - entry).abs() / entry_abs * 100.0
    stop_distance = (entry - stop).abs() / entry_abs * 100.0
    net_reward = (target_distance - cost).clip(lower=-100.0)
    net_risk = (stop_distance + cost).clip(lower=1e-6)
    result["net_reward_risk"] = _safe_divide(net_reward, net_risk).clip(-5.0, 10.0)

    vol_scale = 1.0 + atr.clip(lower=0.0).fillna(0.0)
    result["trend_per_vol"] = (result["trend_norm"] / vol_scale).clip(-2.0, 2.0)
    result["momentum_per_vol"] = (result["momentum_capped"] / vol_scale).clip(-2.0, 2.0)
    result["trend_volume_interaction"] = (result["trend_norm"] * result["volume_confirm"]).clip(-3.0, 3.0)
    result["structure_gate"] = structure.ge(float(config.structure_gate_min)).astype(float)

    for category in config.categorical_columns:
        if category not in result.columns:
            result[category] = "UNKNOWN"
        result[category] = result[category].fillna("UNKNOWN").astype(str).str.upper()

    available = [key for key, aliases in ALIASES.items() if _first_existing(work, aliases) is not None]
    diagnostics = {
        "available_sources": available,
        "unavailable_sources": [key for key in ALIASES if key not in available],
        "aggregate_score_used_as_feature": False,
        "structure_used_as_additive_score": False,
        "rows": int(len(result)),
    }
    return result, diagnostics


def entry_gate_mask(frame: pd.DataFrame, config: FeatureArchitectureV2Config, *, strict: bool = False) -> pd.Series:
    """Entry-time gate mask. Missing optional fields do not leak or fail open silently."""
    if frame.empty:
        return pd.Series(False, index=frame.index, dtype=bool)
    mask = pd.Series(True, index=frame.index, dtype=bool)
    if "structure_gate" in frame.columns:
        mask &= pd.to_numeric(frame["structure_gate"], errors="coerce").fillna(0).ge(1.0)
    if "volume_score" in frame.columns and config.volume_gate_min > 0:
        mask &= pd.to_numeric(frame["volume_score"], errors="coerce").fillna(-np.inf).ge(config.volume_gate_min)
    if "risk_penalty" in frame.columns:
        mask &= pd.to_numeric(frame["risk_penalty"], errors="coerce").fillna(np.inf).le(config.maximum_risk_penalty)
    if "cost_to_atr" in frame.columns and frame["cost_to_atr"].notna().any():
        mask &= pd.to_numeric(frame["cost_to_atr"], errors="coerce").fillna(np.inf).le(config.maximum_cost_to_atr)
    elif strict:
        mask &= False
    if "net_reward_risk" in frame.columns and frame["net_reward_risk"].notna().any() and config.minimum_net_reward_risk > 0:
        mask &= pd.to_numeric(frame["net_reward_risk"], errors="coerce").fillna(-np.inf).ge(config.minimum_net_reward_risk)
    return mask


def chronological_development_split(frame: pd.DataFrame, config: FeatureArchitectureV2Config) -> ChronologicalSplit:
    """Split on unique timestamps and remove purge timestamps between segments."""
    work = prepare_architecture_rows(frame, config)
    if work.empty:
        return ChronologicalSplit(work.copy(), work.copy(), work.copy(), {})
    timestamps = pd.Index(work["__timestamp"].drop_duplicates().sort_values())
    n = len(timestamps)
    if n < max(20, config.purge_timestamps * 3 + 6):
        raise ValueError("not enough unique timestamps for chronological split with purge")
    train_end_idx = max(1, int(n * config.train_fraction))
    optimize_end_idx = max(train_end_idx + 1, int(n * (config.train_fraction + config.optimize_fraction)))
    purge = int(config.purge_timestamps)

    train_times = timestamps[: max(0, train_end_idx - purge)]
    optimize_times = timestamps[min(n, train_end_idx + purge) : max(train_end_idx + purge, optimize_end_idx - purge)]
    holdout_times = timestamps[min(n, optimize_end_idx + purge) :]
    if len(train_times) == 0 or len(optimize_times) == 0 or len(holdout_times) == 0:
        raise ValueError("purged chronological split produced an empty segment")

    train = work[work["__timestamp"].isin(train_times)].copy()
    optimize = work[work["__timestamp"].isin(optimize_times)].copy()
    holdout = work[work["__timestamp"].isin(holdout_times)].copy()
    boundaries = {
        "train_start": train["__timestamp"].min().isoformat(),
        "train_end": train["__timestamp"].max().isoformat(),
        "optimize_start": optimize["__timestamp"].min().isoformat(),
        "optimize_end": optimize["__timestamp"].max().isoformat(),
        "holdout_start": holdout["__timestamp"].min().isoformat(),
        "holdout_end": holdout["__timestamp"].max().isoformat(),
        "purge_timestamps": str(purge),
    }
    if not (train["__timestamp"].max() < optimize["__timestamp"].min() < holdout["__timestamp"].min()):
        raise AssertionError("chronological split overlap detected")
    return ChronologicalSplit(train, optimize, holdout, boundaries)


def _variant_numeric_features(variant: str) -> List[str]:
    features = list(BASE_NUMERIC_FEATURES)
    upper = variant.upper()
    if "NO_MOMENTUM" in upper:
        features = [f for f in features if "momentum" not in f]
    if "LEAN" in upper:
        keep = {"trend_per_vol", "volume_confirm", "risk_norm", "atr_log", "cost_to_atr", "net_reward_risk", "structure_gate"}
        features = [f for f in features if f in keep]
    return features


def build_model_matrix(frame: pd.DataFrame, variant: str, config: FeatureArchitectureV2Config, *, columns: Optional[Sequence[str]] = None) -> pd.DataFrame:
    validate_entry_feature_names(_variant_numeric_features(variant))
    numeric = [feature for feature in _variant_numeric_features(variant) if feature in frame.columns]
    matrix = frame[numeric].apply(pd.to_numeric, errors="coerce") if numeric else pd.DataFrame(index=frame.index)
    categories = [c for c in config.categorical_columns if c in frame.columns]
    if categories:
        dummies = pd.get_dummies(frame[categories].fillna("UNKNOWN").astype(str), prefix=categories, dtype=float)
        matrix = pd.concat([matrix, dummies], axis=1)
    if columns is not None:
        matrix = matrix.reindex(columns=list(columns), fill_value=0.0)
    return matrix.astype(float)


def _return_pipeline(alpha: float) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
        ("scaler", RobustScaler()),
        ("model", Ridge(alpha=float(alpha))),
    ])


def _win_pipeline(c_value: float, random_state: int) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
        ("scaler", RobustScaler()),
        ("model", LogisticRegression(C=float(c_value), max_iter=2000, class_weight="balanced", random_state=random_state)),
    ])


def fit_side_model(frame: pd.DataFrame, side: str, variant: str, config: FeatureArchitectureV2Config) -> SideModel:
    side = side.upper()
    subset = frame[frame["side"].eq(side)].copy()
    if len(subset) < config.minimum_train_samples_per_side:
        raise ValueError(f"insufficient {side} train samples: {len(subset)}")
    matrix = build_model_matrix(subset, variant, config)
    if matrix.shape[1] == 0:
        raise ValueError("no usable entry-time features for architecture model")
    target = pd.to_numeric(subset["__return"], errors="coerce")
    valid = target.notna()
    matrix = matrix.loc[valid]
    target = target.loc[valid]
    if len(target) < config.minimum_train_samples_per_side:
        raise ValueError(f"insufficient valid {side} target rows")

    return_model = _return_pipeline(config.ridge_alpha)
    return_model.fit(matrix, target)
    win_target = target.gt(0).astype(int)
    win_model: Optional[Pipeline] = None
    if win_target.nunique() >= 2:
        win_model = _win_pipeline(config.logistic_c, config.random_state)
        win_model.fit(matrix, win_target)

    wins = target[target > 0]
    losses = target[target <= 0]
    avg_win = float(wins.mean()) if not wins.empty else 0.0
    avg_loss = float(losses.mean()) if not losses.empty else 0.0
    return SideModel(
        side=side,
        variant=variant,
        feature_columns=list(matrix.columns),
        return_pipeline=return_model,
        win_pipeline=win_model,
        average_win_pct=avg_win,
        average_loss_pct=avg_loss,
        train_rows=int(len(target)),
        gate_diagnostics={"train_gate_pass_rate": float(entry_gate_mask(subset, config).mean())},
    )


def fit_architecture_bundle(train_frame: pd.DataFrame, variant: str, config: FeatureArchitectureV2Config) -> ArchitectureBundle:
    engineered, diagnostics = engineer_entry_features(train_frame, config)
    models: Dict[str, SideModel] = {}
    for side in ("LONG", "SHORT"):
        try:
            models[side] = fit_side_model(engineered, side, variant, config)
        except ValueError:
            continue
    available = sorted(set(feature for model in models.values() for feature in model.feature_columns))
    return ArchitectureBundle(
        variant=variant,
        models=models,
        config=config,
        available_features=available,
        unavailable_features=list(diagnostics.get("unavailable_sources", [])),
    )


def predict_architecture(
    bundle: ArchitectureBundle,
    frame: pd.DataFrame,
    *,
    strict_gates: bool = False,
    time_scope: str = "development",
) -> pd.DataFrame:
    engineered, _ = engineer_entry_features(frame, bundle.config, time_scope=time_scope)
    if engineered.empty:
        return engineered
    result = engineered.copy()
    result["predicted_return_pct"] = np.nan
    result["predicted_win_probability"] = np.nan
    result["predicted_probability_ev_pct"] = np.nan
    result["predicted_expected_net_pct"] = np.nan
    result["gate_pass"] = entry_gate_mask(result, bundle.config, strict=strict_gates)

    for side, model in bundle.models.items():
        mask = result["side"].eq(side)
        if not mask.any():
            continue
        matrix = build_model_matrix(result.loc[mask], model.variant, bundle.config, columns=model.feature_columns)
        return_pred = np.asarray(model.return_pipeline.predict(matrix), dtype=float)
        if model.win_pipeline is not None:
            win_prob = np.asarray(model.win_pipeline.predict_proba(matrix)[:, 1], dtype=float)
        else:
            win_prob = np.full(len(matrix), 0.5, dtype=float)
        probability_ev = win_prob * model.average_win_pct + (1.0 - win_prob) * model.average_loss_pct
        expected = 0.5 * return_pred + 0.5 * probability_ev
        result.loc[mask, "predicted_return_pct"] = return_pred
        result.loc[mask, "predicted_win_probability"] = win_prob
        result.loc[mask, "predicted_probability_ev_pct"] = probability_ev
        result.loc[mask, "predicted_expected_net_pct"] = expected
    return result


def _basic_metrics(returns: pd.Series) -> Dict[str, Any]:
    values = pd.to_numeric(returns, errors="coerce").dropna().astype(float)
    if values.empty:
        return {"sample_count": 0, "win_rate": 0.0, "expectancy": 0.0, "profit_factor": 0.0, "total_return": 0.0, "max_drawdown": 0.0}
    wins = values[values > 0]
    losses = values[values <= 0]
    gross_profit = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    pf = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    equity = values.cumsum().to_numpy(dtype=float)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    max_dd = float((np.r_[0.0, equity] - peaks).min())
    return {
        "sample_count": int(len(values)),
        "win_rate": float((values > 0).mean()),
        "expectancy": float(values.mean()),
        "profit_factor": float(pf),
        "total_return": float(values.sum()),
        "max_drawdown": max_dd,
    }


def select_side_threshold(predictions: pd.DataFrame, side: str, config: FeatureArchitectureV2Config) -> ThresholdSelection:
    subset = predictions[predictions["side"].eq(side.upper()) & predictions["gate_pass"]].copy()
    rows: List[Dict[str, Any]] = []
    for threshold in config.expected_return_thresholds:
        selected = subset[subset["predicted_expected_net_pct"].ge(float(threshold))]
        metrics = _basic_metrics(selected["__return"])
        eligible = (
            metrics["sample_count"] >= config.minimum_optimize_samples
            and metrics["expectancy"] > config.optimize_min_expectancy_pct
            and metrics["profit_factor"] >= config.optimize_min_profit_factor
        )
        rows.append({"side": side.upper(), "threshold": float(threshold), "eligible": bool(eligible), **metrics})
    eligible_rows = [row for row in rows if row["eligible"]]
    if eligible_rows:
        best = max(eligible_rows, key=lambda row: (row["expectancy"], row["profit_factor"], row["sample_count"]))
        return ThresholdSelection(side.upper(), float(best["threshold"]), True, "positive optimize candidate", rows)
    return ThresholdSelection(side.upper(), None, False, "no positive optimize threshold survived constraints", rows)


def apply_thresholds(predictions: pd.DataFrame, selections: Mapping[str, ThresholdSelection], *, long_only: bool = False) -> pd.DataFrame:
    if predictions.empty:
        return predictions.copy()
    masks: List[pd.Series] = []
    for side in ("LONG", "SHORT"):
        if long_only and side == "SHORT":
            continue
        selection = selections.get(side)
        if selection is None or selection.threshold is None:
            continue
        masks.append(
            predictions["side"].eq(side)
            & predictions["gate_pass"]
            & predictions["predicted_expected_net_pct"].ge(float(selection.threshold))
        )
    if not masks:
        return predictions.iloc[0:0].copy()
    combined = masks[0].copy()
    for mask in masks[1:]:
        combined |= mask
    return predictions[combined].copy()


def model_coefficients(bundle: ArchitectureBundle) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    for side, model in bundle.models.items():
        ridge = model.return_pipeline.named_steps["model"]
        coefficients = np.asarray(ridge.coef_, dtype=float).ravel()
        # SimpleImputer(add_indicator=True) may expand columns. Preserve source names
        # for the original columns and name missing indicators explicitly.
        names = list(model.feature_columns)
        if len(coefficients) > len(names):
            names += [f"missing_indicator_{i}" for i in range(len(coefficients) - len(names))]
        for name, value in zip(names, coefficients):
            records.append({"variant": bundle.variant, "side": side, "model": "RETURN_RIDGE", "feature": name, "coefficient": float(value)})
        if model.win_pipeline is not None:
            logistic = model.win_pipeline.named_steps["model"]
            win_coefficients = np.asarray(logistic.coef_, dtype=float).ravel()
            win_names = list(model.feature_columns)
            if len(win_coefficients) > len(win_names):
                win_names += [f"missing_indicator_{i}" for i in range(len(win_coefficients) - len(win_names))]
            for name, value in zip(win_names, win_coefficients):
                records.append({"variant": bundle.variant, "side": side, "model": "WIN_LOGISTIC", "feature": name, "coefficient": float(value)})
    return pd.DataFrame.from_records(records)


def stable_row_id(row: pd.Series, fallback_index: int) -> str:
    raw = str(row.get("decision_id") or f"{row.get('__timestamp')}|{row.get('symbol')}|{fallback_index}")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
