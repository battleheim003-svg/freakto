"""Leakage-safe score-component attribution for Freakto replay decisions.

This module answers a diagnostic question: which decision-time score components
are associated with future *net* return, and which ones mostly inflate the total
score without preserving out-of-sample value?

Safety contract
---------------
* Only fields available at decision time are accepted as explanatory features.
* Future return / win / target / stop / outcome fields are targets only.
* When multiple replay runs exist, the latest run is used by default to avoid
  counting the same market history several times.
* A chronological development/holdout split is used for multivariate attribution.
* No weight or Paper/Live setting is changed by this research module.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd

VERSION = "v10.6.0"

DEFAULT_REPLAY_DATASET = Path("logs/market_replay/market_replay_evaluations.csv")
DEFAULT_CALIBRATION_DATASET = Path("logs/calibration_dataset/calibration_training.csv")
DEFAULT_OUTPUT_DIR = Path("logs/score_attribution")

RETURN_CANDIDATES = (
    "net_signed_return_after_6c_pct",
    "evaluated_return",
    "net_return_after_24h_pct",
    "return_after_24h_pct",
    "net_return_pct",
    "net_return",
)
TIMESTAMP_CANDIDATES = (
    "candle_timestamp",
    "decision_timestamp",
    "feature_cutoff_timestamp",
    "timestamp",
    "created_utc",
)
DEFAULT_COMPONENTS = (
    "trend_score",
    "momentum_score",
    "volume_score",
    "structure_score",
    "regime_score",
    "risk_penalty",
    "external_context_score",
    "adaptive_adjustment",
    "historical_edge_score",
)
COMPONENT_LABELS = {
    "trend_score": "Trend",
    "momentum_score": "Momentum",
    "volume_score": "Volume",
    "structure_score": "Structure",
    "regime_score": "Regime",
    "risk_penalty": "Risk Penalty",
    "external_context_score": "External Context",
    "adaptive_adjustment": "Adaptive Adjustment",
    "historical_edge_score": "Historical Edge",
}
LEAKAGE_TOKENS = (
    "return",
    "win",
    "loss",
    "outcome",
    "target_hit",
    "target_1_hit",
    "target_2_hit",
    "target_3_hit",
    "stop_hit",
    "mfe",
    "mae",
    "future",
    "exit_price",
    "direction_correct",
)


@dataclass(frozen=True)
class AttributionConfig:
    train_ratio: float = 0.70
    purge_rows: int = 6
    minimum_total_rows: int = 300
    minimum_scope_rows: int = 80
    minimum_bin_rows: int = 20
    quantile_bins: int = 5
    ridge_alpha: float = 10.0
    random_seed: int = 42
    effect_tolerance_pct: float = 0.05

    def validate(self) -> None:
        if not 0.50 <= self.train_ratio < 0.90:
            raise ValueError("train_ratio must be in [0.50, 0.90).")
        if self.purge_rows < 0:
            raise ValueError("purge_rows cannot be negative.")
        if self.minimum_total_rows <= 0 or self.minimum_scope_rows <= 0:
            raise ValueError("minimum row constraints must be positive.")
        if self.quantile_bins < 2:
            raise ValueError("quantile_bins must be at least 2.")
        if self.ridge_alpha < 0:
            raise ValueError("ridge_alpha cannot be negative.")


@dataclass
class AttributionResult:
    created_utc: str
    version: str
    status: str
    dataset_path: str
    dataset_sha256: str
    selected_run_id: Optional[str]
    rows_loaded: int
    rows_usable: int
    components: list[str]
    return_column: str
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    dataset_summary: dict = field(default_factory=dict)
    model_metrics: dict = field(default_factory=dict)
    key_findings: list[str] = field(default_factory=list)
    output_files: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AttributionArtifacts:
    component_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    component_bins: pd.DataFrame = field(default_factory=pd.DataFrame)
    model_attribution: pd.DataFrame = field(default_factory=pd.DataFrame)
    score_bands: pd.DataFrame = field(default_factory=pd.DataFrame)
    economics: pd.DataFrame = field(default_factory=pd.DataFrame)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pick_column(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    normalized = {str(column).strip().lower(): str(column) for column in columns}
    for candidate in candidates:
        match = normalized.get(candidate.lower())
        if match is not None:
            return match
    return None


def _normalize_regime(value: object) -> str:
    text = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    if text in {"TRENDING_BULL", "BULL", "BULLISH", "UPTREND", "TREND_UP"}:
        return "BULL"
    if text in {"TRENDING_BEAR", "BEAR", "BEARISH", "DOWNTREND", "TREND_DOWN"}:
        return "BEAR"
    if text in {"SIDEWAYS", "RANGE", "RANGING", "NEUTRAL", "CHOP", "CHOPPY"}:
        return "SIDEWAYS"
    if text in {"VOLATILE", "HIGH_VOLATILITY", "HIGH_VOL", "EXPANDING_VOLATILITY"}:
        return "VOLATILE"
    if text in {"QUIET", "LOW_VOLATILITY", "LOW_VOL", "COMPRESSED_VOLATILITY"}:
        return "QUIET"
    return "UNKNOWN"


def validate_component_columns(components: Sequence[str]) -> None:
    for component in components:
        lowered = str(component).strip().lower()
        if any(token in lowered for token in LEAKAGE_TOKENS):
            raise ValueError(f"Outcome/leakage column cannot be used as a component: {component}")


def _default_dataset_path() -> Path:
    if DEFAULT_REPLAY_DATASET.exists():
        return DEFAULT_REPLAY_DATASET
    if DEFAULT_CALIBRATION_DATASET.exists():
        return DEFAULT_CALIBRATION_DATASET
    raise FileNotFoundError(
        f"Neither {DEFAULT_REPLAY_DATASET} nor {DEFAULT_CALIBRATION_DATASET} exists."
    )


def _run_sort_key(run_id: str) -> tuple[str, str]:
    text = str(run_id or "")
    digits = "".join(character for character in text if character.isdigit())
    return digits, text


def load_attribution_dataset(
    path: Path | str | None = None,
    *,
    run_id: Optional[str] = None,
    latest_run_only: bool = True,
    components: Sequence[str] = DEFAULT_COMPONENTS,
) -> tuple[pd.DataFrame, dict, list[str]]:
    """Load a canonical decision-time component dataset.

    Returns ``(frame, metadata, warnings)``. The frame contains canonical
    ``evaluated_return``, ``win``, ``_event_time``, and ``_regime_group`` columns.
    """

    validate_component_columns(components)
    source = Path(path) if path is not None else _default_dataset_path()
    if not source.exists():
        raise FileNotFoundError(source)

    header = pd.read_csv(source, encoding="utf-8-sig", nrows=0)
    return_col = _pick_column(header.columns, RETURN_CANDIDATES)
    timestamp_col = _pick_column(header.columns, TIMESTAMP_CANDIDATES)
    available_components = [component for component in components if component in header.columns]
    if return_col is None:
        raise ValueError("No supported net evaluated-return column was found.")
    if timestamp_col is None:
        raise ValueError("A decision/candle timestamp column is required for leakage-safe analysis.")
    if not available_components:
        raise ValueError(
            "No score-component columns were found. Use market_replay_evaluations.csv, "
            "not the reduced calibration_training.csv."
        )

    optional_columns = {
        "run_id",
        "decision_id",
        "evaluation_status",
        "side",
        "score",
        "symbol",
        "timeframe",
        "regime_label",
        "target_1_hit",
        "target_2_hit",
        "target_3_hit",
        "stop_hit",
        "mfe_pct",
        "mae_pct",
        "replay_safe",
        "learning_overrides_enabled",
        "historical_edge_enabled",
    }
    use_columns = set(available_components) | optional_columns | {return_col, timestamp_col}
    use_columns &= set(map(str, header.columns))
    frame = pd.read_csv(
        source,
        encoding="utf-8-sig",
        low_memory=False,
        usecols=lambda column: column in use_columns,
    )
    rows_loaded = len(frame)
    warnings: list[str] = []

    if "evaluation_status" in frame.columns:
        frame = frame[frame["evaluation_status"].astype(str).str.upper().eq("COMPLETE")]
    if "side" not in frame.columns:
        raise ValueError("The side column is required.")
    frame["side"] = frame["side"].astype(str).str.strip().str.upper()
    frame = frame[frame["side"].isin(["LONG", "SHORT"])]

    selected_run_id: Optional[str] = None
    if "run_id" in frame.columns:
        available_runs = sorted(
            [value for value in frame["run_id"].dropna().astype(str).unique() if value],
            key=_run_sort_key,
        )
        if run_id is not None:
            if run_id not in available_runs:
                raise ValueError(f"Replay run not found: {run_id}")
            selected_run_id = run_id
            frame = frame[frame["run_id"].astype(str).eq(run_id)]
        elif latest_run_only and available_runs:
            selected_run_id = available_runs[-1]
            frame = frame[frame["run_id"].astype(str).eq(selected_run_id)]
            if len(available_runs) > 1:
                warnings.append(
                    f"Selected latest replay run {selected_run_id}; ignored {len(available_runs) - 1} older runs "
                    "to avoid repeated market-history counting."
                )

    frame = frame.copy()
    frame["score"] = pd.to_numeric(frame.get("score"), errors="coerce")
    frame["evaluated_return"] = pd.to_numeric(frame[return_col], errors="coerce")
    frame["_event_time"] = pd.to_datetime(frame[timestamp_col], errors="coerce", utc=True)
    for component in available_components:
        frame[component] = pd.to_numeric(frame[component], errors="coerce")

    required = ["score", "evaluated_return", "_event_time", *available_components]
    before_drop = len(frame)
    frame = frame.dropna(subset=required)
    if before_drop != len(frame):
        warnings.append(f"Dropped {before_drop - len(frame)} rows with missing score, component, return, or timestamp.")
    frame = frame[frame["score"].between(0, 100)]

    if "decision_id" in frame.columns:
        before = len(frame)
        frame = frame.drop_duplicates("decision_id", keep="last")
        if before != len(frame):
            warnings.append(f"Removed {before - len(frame)} duplicate decision_id rows.")

    frame["win"] = frame["evaluated_return"] > 0
    if "regime_label" in frame.columns:
        frame["_regime_group"] = frame["regime_label"].map(_normalize_regime)
    else:
        frame["_regime_group"] = "UNKNOWN"
    frame = frame.sort_values(["_event_time", "symbol" if "symbol" in frame.columns else "side"], kind="stable")
    frame = frame.reset_index(drop=True)
    frame["_row_order"] = np.arange(len(frame), dtype=int)

    metadata = {
        "dataset_path": str(source),
        "rows_loaded": int(rows_loaded),
        "rows_usable": int(len(frame)),
        "return_column": str(return_col),
        "timestamp_column": str(timestamp_col),
        "selected_run_id": selected_run_id,
        "components": available_components,
        "available_runs": int(frame["run_id"].nunique()) if "run_id" in frame.columns else 0,
    }
    return frame, metadata, warnings


def chronological_development_holdout_split(
    frame: pd.DataFrame,
    config: AttributionConfig = AttributionConfig(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    config.validate()
    if len(frame) < config.minimum_total_rows:
        raise ValueError(f"At least {config.minimum_total_rows} usable rows are required; found {len(frame)}.")
    boundary = int(len(frame) * config.train_ratio)
    development_stop = max(0, boundary - config.purge_rows)
    development = frame.iloc[:development_stop].copy()
    holdout = frame.iloc[boundary:].copy()
    if min(len(development), len(holdout)) < 50:
        raise ValueError("Development and holdout must each contain at least 50 rows.")
    return development, holdout


def _safe_corr(left: pd.Series, right: pd.Series, method: str) -> float:
    pair = pd.concat([pd.to_numeric(left, errors="coerce"), pd.to_numeric(right, errors="coerce")], axis=1).dropna()
    if len(pair) < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return 0.0
    value = pair.iloc[:, 0].corr(pair.iloc[:, 1], method=method)
    return 0.0 if pd.isna(value) else float(value)


def _quantile_labels(values: pd.Series, bins: int) -> pd.Series:
    # Score components are bounded point allocations with many ties. Equal-width
    # bins preserve the meaning of low/high points better than qcut, which can
    # collapse to one bin when a component is concentrated at its maximum.
    numeric = pd.to_numeric(values, errors="coerce")
    unique_count = int(numeric.nunique(dropna=True))
    if unique_count <= 1:
        return pd.Series(["CONSTANT"] * len(numeric), index=numeric.index, dtype="object")
    q = min(max(2, bins), unique_count)
    minimum = float(numeric.min())
    maximum = float(numeric.max())
    if not math.isfinite(minimum) or not math.isfinite(maximum) or minimum == maximum:
        return pd.Series(["CONSTANT"] * len(numeric), index=numeric.index, dtype="object")
    edges = np.linspace(minimum, maximum, q + 1)
    result = pd.cut(numeric, bins=edges, include_lowest=True, duplicates="drop")
    return result.astype(str)


def _scope_frames(frame: pd.DataFrame, minimum_rows: int) -> list[tuple[str, pd.DataFrame]]:
    scopes: list[tuple[str, pd.DataFrame]] = [("ALL", frame)]
    for side in ("LONG", "SHORT"):
        subset = frame[frame["side"].eq(side)]
        if len(subset) >= minimum_rows:
            scopes.append((f"SIDE:{side}", subset))
    for regime in ("BULL", "BEAR", "SIDEWAYS", "VOLATILE", "QUIET"):
        subset = frame[frame["_regime_group"].eq(regime)]
        if len(subset) >= minimum_rows:
            scopes.append((f"REGIME:{regime}", subset))
    return scopes


def component_univariate_attribution(
    frame: pd.DataFrame,
    components: Sequence[str],
    config: AttributionConfig = AttributionConfig(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build descriptive component attribution and quantile-bin diagnostics."""

    summary_rows: list[dict] = []
    bin_rows: list[dict] = []
    tolerance = float(config.effect_tolerance_pct)

    for scope_name, scope in _scope_frames(frame, config.minimum_scope_rows):
        for component in components:
            values = pd.to_numeric(scope[component], errors="coerce")
            active = values.nunique(dropna=True) > 1 and values.abs().sum() > 0
            labels = _quantile_labels(values, config.quantile_bins)
            scoped = scope[["evaluated_return", "win"]].copy()
            scoped["component_value"] = values
            scoped["bin"] = labels
            grouped = list(scoped.dropna(subset=["component_value", "evaluated_return"]).groupby("bin", sort=False))
            grouped = sorted(grouped, key=lambda item: float(item[1]["component_value"].mean()))

            for order, (label, group) in enumerate(grouped):
                returns = group["evaluated_return"]
                bin_rows.append(
                    {
                        "scope": scope_name,
                        "component": component,
                        "component_label": COMPONENT_LABELS.get(component, component),
                        "bin_order": order,
                        "bin_label": str(label),
                        "sample_count": int(len(group)),
                        "component_mean": round(float(group["component_value"].mean()), 6),
                        "avg_return": round(float(returns.mean()), 6),
                        "median_return": round(float(returns.median()), 6),
                        "win_rate": round(float(group["win"].mean()), 6),
                    }
                )

            low = grouped[0][1] if grouped else pd.DataFrame()
            high = grouped[-1][1] if grouped else pd.DataFrame()
            low_return = float(low["evaluated_return"].mean()) if len(low) >= config.minimum_bin_rows else math.nan
            high_return = float(high["evaluated_return"].mean()) if len(high) >= config.minimum_bin_rows else math.nan
            effect = high_return - low_return if not (math.isnan(low_return) or math.isnan(high_return)) else math.nan
            spearman = _safe_corr(values, scope["evaluated_return"], "spearman")
            pearson = _safe_corr(values, scope["evaluated_return"], "pearson")
            win_corr = _safe_corr(values, scope["win"].astype(float), "spearman")

            if not active:
                diagnosis = "INACTIVE"
            elif not math.isnan(effect) and effect > tolerance and spearman > 0:
                diagnosis = "SUPPORTIVE_ASSOCIATION"
            elif not math.isnan(effect) and effect < -tolerance and spearman < 0:
                diagnosis = "HARMFUL_ASSOCIATION"
            else:
                diagnosis = "MIXED_OR_WEAK"

            summary_rows.append(
                {
                    "scope": scope_name,
                    "component": component,
                    "component_label": COMPONENT_LABELS.get(component, component),
                    "sample_count": int(values.notna().sum()),
                    "active": bool(active),
                    "mean_points": round(float(values.mean()), 6),
                    "std_points": round(float(values.std(ddof=0)), 6),
                    "min_points": round(float(values.min()), 6),
                    "max_points": round(float(values.max()), 6),
                    "spearman_return": round(spearman, 6),
                    "pearson_return": round(pearson, 6),
                    "spearman_win": round(win_corr, 6),
                    "low_bin_avg_return": None if math.isnan(low_return) else round(low_return, 6),
                    "high_bin_avg_return": None if math.isnan(high_return) else round(high_return, 6),
                    "high_minus_low_return": None if math.isnan(effect) else round(effect, 6),
                    "diagnosis": diagnosis,
                }
            )

    return pd.DataFrame(summary_rows), pd.DataFrame(bin_rows)


def _ridge_fit_predict(
    development: pd.DataFrame,
    holdout: pd.DataFrame,
    components: Sequence[str],
    alpha: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], np.ndarray, np.ndarray]:
    active = [component for component in components if development[component].nunique(dropna=True) > 1]
    if not active:
        raise ValueError("No non-constant component is available for multivariate attribution.")

    x_train = development[active].astype(float).to_numpy()
    x_holdout = holdout[active].astype(float).to_numpy()
    y_train = development["evaluated_return"].astype(float).to_numpy()
    y_holdout = holdout["evaluated_return"].astype(float).to_numpy()

    mean = x_train.mean(axis=0)
    scale = x_train.std(axis=0)
    scale = np.where(scale <= 1e-12, 1.0, scale)
    z_train = (x_train - mean) / scale
    z_holdout = (x_holdout - mean) / scale
    y_mean = float(y_train.mean())
    centered_y = y_train - y_mean
    gram = z_train.T @ z_train + float(alpha) * np.eye(len(active))
    beta = np.linalg.solve(gram, z_train.T @ centered_y)
    predictions = y_mean + z_holdout @ beta
    return beta, predictions, y_holdout, active, z_holdout, scale


def ridge_out_of_sample_attribution(
    frame: pd.DataFrame,
    components: Sequence[str],
    config: AttributionConfig = AttributionConfig(),
) -> tuple[pd.DataFrame, dict]:
    """Fit ridge attribution on development and measure permutation value on holdout."""

    development, holdout = chronological_development_holdout_split(frame, config)
    beta, predictions, y_holdout, active, z_holdout, _ = _ridge_fit_predict(
        development, holdout, components, config.ridge_alpha
    )
    residual = y_holdout - predictions
    baseline_mse = float(np.mean(residual**2))
    baseline_mae = float(np.mean(np.abs(residual)))
    denominator = float(np.sum((y_holdout - y_holdout.mean()) ** 2))
    r2 = 0.0 if denominator <= 1e-12 else 1.0 - float(np.sum(residual**2)) / denominator
    prediction_series = pd.Series(predictions)
    target_series = pd.Series(y_holdout)
    rank_corr = _safe_corr(prediction_series, target_series, "spearman")

    rng = np.random.default_rng(config.random_seed)
    rows: list[dict] = []
    for idx, component in enumerate(active):
        shuffled = z_holdout.copy()
        shuffled[:, idx] = rng.permutation(shuffled[:, idx])
        permuted_predictions = float(development["evaluated_return"].mean()) + shuffled @ beta
        permuted_mse = float(np.mean((y_holdout - permuted_predictions) ** 2))
        importance = permuted_mse - baseline_mse
        rows.append(
            {
                "component": component,
                "component_label": COMPONENT_LABELS.get(component, component),
                "standardized_coefficient": round(float(beta[idx]), 8),
                "permutation_mse_increase": round(float(importance), 8),
                "coefficient_direction": "POSITIVE" if beta[idx] > 0 else "NEGATIVE" if beta[idx] < 0 else "ZERO",
                "holdout_value": "USEFUL" if importance > 0 else "NO_HOLDOUT_VALUE",
                "development_rows": int(len(development)),
                "holdout_rows": int(len(holdout)),
            }
        )

    inactive = [component for component in components if component not in active]
    for component in inactive:
        rows.append(
            {
                "component": component,
                "component_label": COMPONENT_LABELS.get(component, component),
                "standardized_coefficient": 0.0,
                "permutation_mse_increase": 0.0,
                "coefficient_direction": "ZERO",
                "holdout_value": "INACTIVE",
                "development_rows": int(len(development)),
                "holdout_rows": int(len(holdout)),
            }
        )

    metrics = {
        "development_rows": int(len(development)),
        "holdout_rows": int(len(holdout)),
        "purge_rows": int(config.purge_rows),
        "ridge_alpha": float(config.ridge_alpha),
        "holdout_mse": round(baseline_mse, 8),
        "holdout_mae": round(baseline_mae, 8),
        "holdout_r2": round(r2, 8),
        "holdout_spearman_prediction_return": round(rank_corr, 8),
    }
    result = pd.DataFrame(rows).sort_values(
        ["permutation_mse_increase", "standardized_coefficient"], ascending=[False, False], kind="stable"
    )
    return result.reset_index(drop=True), metrics


def _performance_dict(returns: pd.Series) -> dict:
    clean = pd.to_numeric(returns, errors="coerce").dropna()
    if clean.empty:
        return {
            "sample_count": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "median_return": 0.0,
            "profit_factor": 0.0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
        }
    wins = clean[clean > 0]
    losses = clean[clean < 0]
    gross_loss = abs(float(losses.sum()))
    gross_profit = float(wins.sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else gross_profit
    equity = clean.cumsum()
    drawdown = equity - equity.cummax()
    return {
        "sample_count": int(len(clean)),
        "win_rate": round(float((clean > 0).mean()), 6),
        "avg_return": round(float(clean.mean()), 6),
        "median_return": round(float(clean.median()), 6),
        "profit_factor": round(float(profit_factor), 6),
        "total_return": round(float(clean.sum()), 6),
        "max_drawdown": round(float(drawdown.min()), 6),
    }


def score_band_performance(frame: pd.DataFrame, config: AttributionConfig = AttributionConfig()) -> pd.DataFrame:
    bins = [-0.001, 49, 54, 59, 64, 69, 74, 79, 84, 89, 100]
    labels = ["00-49", "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85-89", "90-100"]
    rows: list[dict] = []
    for scope_name, scope in _scope_frames(frame, config.minimum_scope_rows):
        bucket = pd.cut(scope["score"], bins=bins, labels=labels, include_lowest=True)
        for label, group in scope.assign(_score_band=bucket).groupby("_score_band", observed=True, sort=True):
            rows.append({"scope": scope_name, "score_band": str(label), **_performance_dict(group["evaluated_return"])})
    return pd.DataFrame(rows)


def economics_summary(frame: pd.DataFrame, config: AttributionConfig = AttributionConfig()) -> pd.DataFrame:
    rows: list[dict] = []
    for scope_name, scope in _scope_frames(frame, config.minimum_scope_rows):
        returns = pd.to_numeric(scope["evaluated_return"], errors="coerce").dropna()
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        avg_win = float(wins.mean()) if not wins.empty else 0.0
        avg_loss = float(losses.mean()) if not losses.empty else 0.0
        loss_magnitude = abs(avg_loss)
        break_even = loss_magnitude / (avg_win + loss_magnitude) if avg_win + loss_magnitude > 0 else 1.0
        actual_win_rate = float((returns > 0).mean()) if len(returns) else 0.0
        row = {
            "scope": scope_name,
            **_performance_dict(returns),
            "avg_win": round(avg_win, 6),
            "avg_loss": round(avg_loss, 6),
            "payoff_ratio": round(avg_win / loss_magnitude, 6) if loss_magnitude > 0 else 0.0,
            "break_even_win_rate": round(break_even, 6),
            "actual_minus_break_even_win_rate": round(actual_win_rate - break_even, 6),
        }
        for column in ("target_1_hit", "target_2_hit", "target_3_hit", "stop_hit"):
            if column in scope.columns:
                normalized = scope[column].astype(str).str.strip().str.lower().map(
                    {"true": 1.0, "1": 1.0, "yes": 1.0, "false": 0.0, "0": 0.0, "no": 0.0}
                )
                row[f"{column}_rate"] = round(float(normalized.mean()), 6) if normalized.notna().any() else None
        if "mfe_pct" in scope.columns:
            row["avg_mfe_pct"] = round(float(pd.to_numeric(scope["mfe_pct"], errors="coerce").mean()), 6)
        if "mae_pct" in scope.columns:
            row["avg_mae_pct"] = round(float(pd.to_numeric(scope["mae_pct"], errors="coerce").mean()), 6)
        rows.append(row)
    return pd.DataFrame(rows)


def _key_findings(
    component_summary: pd.DataFrame,
    model_attribution: pd.DataFrame,
    economics: pd.DataFrame,
) -> list[str]:
    findings: list[str] = []
    overall = component_summary[component_summary["scope"].eq("ALL")]
    harmful = overall[overall["diagnosis"].eq("HARMFUL_ASSOCIATION")]
    supportive = overall[overall["diagnosis"].eq("SUPPORTIVE_ASSOCIATION")]
    if not harmful.empty:
        names = ", ".join(harmful["component_label"].astype(str).tolist())
        findings.append(f"Higher values were associated with worse future net return for: {names}.")
    if not supportive.empty:
        names = ", ".join(supportive["component_label"].astype(str).tolist())
        findings.append(f"Higher values were associated with better future net return for: {names}.")
    no_value = model_attribution[model_attribution["holdout_value"].eq("NO_HOLDOUT_VALUE")]
    if not no_value.empty:
        names = ", ".join(no_value["component_label"].astype(str).tolist())
        findings.append(f"No positive holdout permutation value was observed for: {names}.")
    overall_econ = economics[economics["scope"].eq("ALL")]
    if not overall_econ.empty:
        row = overall_econ.iloc[0]
        if float(row["actual_minus_break_even_win_rate"]) < 0:
            findings.append(
                "Actual win rate was below the payoff-implied break-even win rate; loss magnitude, not only hit rate, is a root cause."
            )
    if not findings:
        findings.append("No single component showed a decisive standalone root cause; interactions and execution economics remain primary suspects.")
    return findings


def run_score_attribution(
    dataset_path: Path | str | None = None,
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    run_id: Optional[str] = None,
    latest_run_only: bool = True,
    config: AttributionConfig = AttributionConfig(),
) -> tuple[AttributionResult, AttributionArtifacts, pd.DataFrame]:
    config.validate()
    frame, metadata, warnings = load_attribution_dataset(
        dataset_path,
        run_id=run_id,
        latest_run_only=latest_run_only,
    )
    source = Path(metadata["dataset_path"])
    result = AttributionResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        version=VERSION,
        status="COMPLETE",
        dataset_path=str(source),
        dataset_sha256=_sha256(source),
        selected_run_id=metadata["selected_run_id"],
        rows_loaded=metadata["rows_loaded"],
        rows_usable=metadata["rows_usable"],
        components=list(metadata["components"]),
        return_column=metadata["return_column"],
        warnings=warnings,
    )

    if len(frame) < config.minimum_total_rows:
        result.status = "INSUFFICIENT_DATA"
        result.blockers.append(
            f"At least {config.minimum_total_rows} usable rows are required; found {len(frame)}."
        )
        return result, AttributionArtifacts(), frame

    component_summary, component_bins = component_univariate_attribution(
        frame, result.components, config
    )
    model_attribution, model_metrics = ridge_out_of_sample_attribution(
        frame, result.components, config
    )
    score_bands = score_band_performance(frame, config)
    economics = economics_summary(frame, config)
    artifacts = AttributionArtifacts(
        component_summary=component_summary,
        component_bins=component_bins,
        model_attribution=model_attribution,
        score_bands=score_bands,
        economics=economics,
    )
    result.model_metrics = model_metrics
    score_spearman = _safe_corr(frame["score"], frame["evaluated_return"], "spearman")
    result.dataset_summary = {
        "start_timestamp": str(frame["_event_time"].min()),
        "end_timestamp": str(frame["_event_time"].max()),
        "symbols": int(frame["symbol"].nunique()) if "symbol" in frame.columns else None,
        "timeframes": int(frame["timeframe"].nunique()) if "timeframe" in frame.columns else None,
        "long_rows": int(frame["side"].eq("LONG").sum()),
        "short_rows": int(frame["side"].eq("SHORT").sum()),
        "score_spearman_return": round(score_spearman, 8),
    }
    result.key_findings = _key_findings(component_summary, model_attribution, economics)
    if model_metrics.get("holdout_r2", 0.0) <= 0 or model_metrics.get("holdout_spearman_prediction_return", 0.0) <= 0:
        result.key_findings.insert(
            0,
            "The multivariate component model failed to generalize on chronological Holdout; direct weight promotion is not justified.",
        )
    overall_bands = score_bands[score_bands["scope"].eq("ALL")].copy()
    adequately_sampled_positive = overall_bands[
        (overall_bands["sample_count"] >= config.minimum_scope_rows)
        & (overall_bands["avg_return"] > 0)
        & (overall_bands["profit_factor"] >= 1.0)
    ]
    if adequately_sampled_positive.empty:
        result.key_findings.append(
            "No adequately sampled score band had positive expectancy and profit factor >= 1; higher total score was not a reliable edge proxy."
        )
    sparse_positive = overall_bands[
        (overall_bands["sample_count"] < config.minimum_scope_rows)
        & (overall_bands["avg_return"] > 0)
    ]
    if not sparse_positive.empty:
        labels = ", ".join(
            f"{row.score_band} (n={int(row.sample_count)})" for row in sparse_positive.itertuples()
        )
        result.key_findings.append(f"Positive score bands were sparse and non-promotable: {labels}.")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "component_summary": output / "component_attribution.csv",
        "component_bins": output / "component_bins.csv",
        "model_attribution": output / "model_attribution.csv",
        "score_bands": output / "score_band_performance.csv",
        "economics": output / "decision_economics.csv",
        "report": output / "score_attribution_report.json",
    }
    for name, table in (
        ("component_summary", component_summary),
        ("component_bins", component_bins),
        ("model_attribution", model_attribution),
        ("score_bands", score_bands),
        ("economics", economics),
    ):
        table.to_csv(paths[name], index=False, encoding="utf-8-sig")
    result.output_files = {key: str(value) for key, value in paths.items()}
    paths["report"].write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result, artifacts, frame
