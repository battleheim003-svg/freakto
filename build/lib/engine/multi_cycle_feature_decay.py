"""Multi-cycle feature decay and regime drift analysis for Freakto.

The analyzer uses frozen development replays only. It partitions the longest
available replay into non-overlapping chronological eras so nested 3Y/5Y/FULL
windows are never double-counted as independent evidence.

Safety contract
---------------
* The development cutoff is enforced before every calculation.
* Outcome fields are targets only and cannot be selected as features.
* No score weight, threshold, policy, Paper setting, or Live setting is changed.
* Positive diagnostics are never treated as promotion authorization.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from engine.multi_cycle_validation import (
    load_replay_files,
    metric_payload,
    normalize_replay_rows,
    population_stability_index,
    return_metrics,
)
from engine.regime_drift import (
    RegimeDriftConfig,
    regime_findings,
    regime_side_matrix,
    summarize_regime_drift,
)

VERSION = "1.0.0"
MODE = "MULTI_CYCLE_DEVELOPMENT_DIAGNOSTIC_ONLY"
DEFAULT_REPLAY_DIR = Path("logs") / "multi_cycle_archive_v2"
DEFAULT_OUTPUT_DIR = Path("logs") / "multi_cycle_feature_decay"
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
EXPECTED_DIRECTIONS = {
    "trend_score": 1.0,
    "momentum_score": 1.0,
    "volume_score": 1.0,
    "structure_score": 1.0,
    "regime_score": 1.0,
    "risk_penalty": -1.0,
    "external_context_score": 1.0,
    "adaptive_adjustment": 1.0,
    "historical_edge_score": 1.0,
}
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
)
ERA_ORDER = ("LEGACY", "TRANSITION", "RECENT")
SCORE_BINS = (-np.inf, 50.0, 60.0, 70.0, 80.0, 90.0, np.inf)
SCORE_LABELS = ("LT50", "50_59", "60_69", "70_79", "80_89", "90_PLUS")
TIMESTAMP_CANDIDATES = ("candle_timestamp", "timestamp_utc", "timestamp", "feature_cutoff_timestamp")
RETURN_CANDIDATES = (
    "net_signed_return_after_6c_pct",
    "net_return_pct",
    "net_return_after_24h_pct",
    "net_signed_return_after_12c_pct",
)


def _normalize_decay_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize replay rows and recover mixed ISO-8601 timestamp strings.

    Pandas 2.x may infer one strict timestamp format from the first CSV row;
    mixed fractional-second precision can then coerce otherwise-valid rows to
    NaT. The canonical normalizer remains the first path, while this fallback
    preserves all causally valid rows using ``format="mixed"``.
    """
    if frame is None or frame.empty:
        return pd.DataFrame()
    standard = normalize_replay_rows(frame)
    if len(standard) >= max(1, int(len(frame) * 0.95)):
        return standard
    work = frame.copy()
    ts_col = next((column for column in TIMESTAMP_CANDIDATES if column in work.columns), None)
    ret_col = next((column for column in RETURN_CANDIDATES if column in work.columns), None)
    if ts_col is None or ret_col is None:
        return standard
    try:
        work["__timestamp"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce", format="mixed")
    except TypeError:  # pandas < 2.0
        work["__timestamp"] = pd.to_datetime(work[ts_col], utc=True, errors="coerce")
    work["__return"] = pd.to_numeric(work[ret_col], errors="coerce")
    if "score" not in work.columns:
        work["score"] = np.nan
    work["score"] = pd.to_numeric(work["score"], errors="coerce")
    if "side" not in work.columns:
        work["side"] = "NEUTRAL"
    work["side"] = work["side"].fillna("NEUTRAL").astype(str).str.upper()
    if "regime" not in work.columns:
        work["regime"] = "UNKNOWN"
    work["regime"] = work["regime"].fillna("UNKNOWN").astype(str).str.upper()
    recovered = work.dropna(subset=["__timestamp", "__return"]).sort_values("__timestamp").reset_index(drop=True)
    return recovered if len(recovered) > len(standard) else standard


@dataclass(frozen=True)
class FeatureDecayConfig:
    development_cutoff_utc: str = "2026-07-09T12:00:00Z"
    recent_years: int = 3
    transition_years: int = 5
    fixed_score_threshold: float = 70.0
    minimum_era_samples: int = 100
    minimum_scope_samples: int = 60
    minimum_quantile_samples: int = 20
    quantile_bins: int = 4
    association_tolerance: float = 0.03
    spread_tolerance_pct: float = 0.05
    decay_tolerance: float = 0.05
    psi_moderate: float = 0.10
    psi_severe: float = 0.25
    components: Tuple[str, ...] = DEFAULT_COMPONENTS
    regime: RegimeDriftConfig = field(default_factory=RegimeDriftConfig)

    def validate(self) -> None:
        cutoff = pd.Timestamp(self.development_cutoff_utc)
        if cutoff.tzinfo is None:
            raise ValueError("development_cutoff_utc must include a timezone")
        if self.recent_years <= 0 or self.transition_years <= self.recent_years:
            raise ValueError("transition_years must be greater than recent_years")
        if self.minimum_era_samples <= 0 or self.minimum_scope_samples <= 0:
            raise ValueError("minimum sample constraints must be positive")
        if self.quantile_bins < 2:
            raise ValueError("quantile_bins must be at least 2")
        validate_feature_names(self.components)


@dataclass
class FeatureDecayReport:
    status: str
    mode: str
    version: str
    created_utc: str
    development_cutoff_utc: str
    selected_replay_window: Optional[str]
    available_replay_windows: List[str]
    rows_loaded: int
    rows_usable: int
    available_components: List[str]
    era_boundaries: Dict[str, str]
    era_counts: Dict[str, int]
    fixed_score_threshold: float
    key_findings: List[str]
    blockers: List[str]
    warnings: List[str]
    output_files: Dict[str, str] = field(default_factory=dict)
    promotion_applied: bool = False
    paper_live_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeatureDecayArtifacts:
    component_by_era: pd.DataFrame = field(default_factory=pd.DataFrame)
    component_decay_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    distribution_drift: pd.DataFrame = field(default_factory=pd.DataFrame)
    component_redundancy_drift: pd.DataFrame = field(default_factory=pd.DataFrame)
    regime_side_matrix: pd.DataFrame = field(default_factory=pd.DataFrame)
    regime_drift_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    score_decay: pd.DataFrame = field(default_factory=pd.DataFrame)
    window_crosscheck: pd.DataFrame = field(default_factory=pd.DataFrame)


def validate_feature_names(features: Sequence[str]) -> None:
    for feature in features:
        lowered = str(feature).strip().lower()
        if not lowered:
            raise ValueError("feature names cannot be empty")
        if any(token in lowered for token in LEAKAGE_TOKENS):
            raise ValueError(f"Outcome/leakage field cannot be used as a feature: {feature}")


def _finite(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _safe_pf(value: Any) -> float:
    if isinstance(value, str) and value.lower() == "inf":
        return float("inf")
    return _finite(value)


def _rank_spearman(x: pd.Series, y: pd.Series) -> float:
    paired = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(paired) < 3 or paired["x"].nunique() < 2 or paired["y"].nunique() < 2:
        return 0.0
    corr = paired["x"].rank(method="average").corr(paired["y"].rank(method="average"))
    return _finite(corr)


def _quantile_spread(values: pd.Series, returns: pd.Series, bins: int, min_bin_samples: int) -> Dict[str, Any]:
    paired = pd.DataFrame(
        {"feature": pd.to_numeric(values, errors="coerce"), "return": pd.to_numeric(returns, errors="coerce")}
    ).dropna()
    if len(paired) < max(2 * min_bin_samples, bins) or paired["feature"].nunique() < 2:
        return {
            "bottom_samples": 0,
            "top_samples": 0,
            "bottom_expectancy": 0.0,
            "top_expectancy": 0.0,
            "top_minus_bottom": 0.0,
        }
    ranks = paired["feature"].rank(method="first")
    try:
        paired["quantile"] = pd.qcut(ranks, q=min(bins, paired["feature"].nunique()), labels=False, duplicates="drop")
    except ValueError:
        return {
            "bottom_samples": 0,
            "top_samples": 0,
            "bottom_expectancy": 0.0,
            "top_expectancy": 0.0,
            "top_minus_bottom": 0.0,
        }
    valid = paired.dropna(subset=["quantile"])
    if valid.empty:
        return {
            "bottom_samples": 0,
            "top_samples": 0,
            "bottom_expectancy": 0.0,
            "top_expectancy": 0.0,
            "top_minus_bottom": 0.0,
        }
    bottom_q = int(valid["quantile"].min())
    top_q = int(valid["quantile"].max())
    bottom = valid[valid["quantile"].eq(bottom_q)]["return"]
    top = valid[valid["quantile"].eq(top_q)]["return"]
    if len(bottom) < min_bin_samples or len(top) < min_bin_samples:
        return {
            "bottom_samples": int(len(bottom)),
            "top_samples": int(len(top)),
            "bottom_expectancy": _finite(bottom.mean()),
            "top_expectancy": _finite(top.mean()),
            "top_minus_bottom": 0.0,
        }
    bottom_exp = _finite(bottom.mean())
    top_exp = _finite(top.mean())
    return {
        "bottom_samples": int(len(bottom)),
        "top_samples": int(len(top)),
        "bottom_expectancy": bottom_exp,
        "top_expectancy": top_exp,
        "top_minus_bottom": top_exp - bottom_exp,
    }


def _deduplicate_decisions(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    work = frame.copy()
    if "decision_id" in work.columns and work["decision_id"].notna().any():
        return work.drop_duplicates(subset=["decision_id"], keep="last").reset_index(drop=True)
    keys = [column for column in ("symbol", "timeframe", "__timestamp", "side") if column in work.columns]
    if len(keys) >= 2:
        return work.drop_duplicates(subset=keys, keep="last").reset_index(drop=True)
    return work.drop_duplicates().reset_index(drop=True)


def select_longest_replay(frames: Mapping[str, pd.DataFrame]) -> Tuple[Optional[str], pd.DataFrame, List[str]]:
    """Select FULL when present, otherwise the replay with earliest timestamp.

    Nested windows are overlapping samples, so only one longest replay is used
    for era inference. Other windows are retained solely as descriptive
    cross-checks.
    """
    warnings: List[str] = []
    normalized: Dict[str, pd.DataFrame] = {}
    for name, frame in frames.items():
        try:
            work = _deduplicate_decisions(_normalize_decay_rows(frame))
        except Exception as exc:
            warnings.append(f"{name}: invalid replay schema ignored: {type(exc).__name__}: {exc}")
            continue
        if not work.empty:
            normalized[str(name).upper()] = work
    if not normalized:
        return None, pd.DataFrame(), warnings
    if "FULL" in normalized:
        return "FULL", normalized["FULL"].copy(), warnings
    selected = min(normalized, key=lambda key: normalized[key]["__timestamp"].min())
    warnings.append(f"FULL replay was unavailable; selected longest available window {selected}.")
    return selected, normalized[selected].copy(), warnings


def assign_non_overlapping_eras(frame: pd.DataFrame, config: FeatureDecayConfig) -> Tuple[pd.DataFrame, Dict[str, str]]:
    config.validate()
    work = _deduplicate_decisions(_normalize_decay_rows(frame))
    cutoff = pd.Timestamp(config.development_cutoff_utc)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    else:
        cutoff = cutoff.tz_convert("UTC")
    work = work[work["__timestamp"].le(cutoff)].copy()
    transition_start = cutoff - pd.DateOffset(years=config.transition_years)
    recent_start = cutoff - pd.DateOffset(years=config.recent_years)
    work["__era"] = np.select(
        [
            work["__timestamp"].lt(transition_start),
            work["__timestamp"].ge(transition_start) & work["__timestamp"].lt(recent_start),
            work["__timestamp"].ge(recent_start) & work["__timestamp"].le(cutoff),
        ],
        ["LEGACY", "TRANSITION", "RECENT"],
        default="OUTSIDE",
    )
    work = work[work["__era"].isin(ERA_ORDER)].copy().reset_index(drop=True)
    boundaries = {
        "legacy_start": work["__timestamp"].min().isoformat() if len(work) else "",
        "transition_start": transition_start.isoformat(),
        "recent_start": recent_start.isoformat(),
        "development_cutoff": cutoff.isoformat(),
    }
    return work, boundaries


def available_components(frame: pd.DataFrame, requested: Sequence[str]) -> List[str]:
    validate_feature_names(requested)
    result: List[str] = []
    for component in requested:
        if component not in frame.columns:
            continue
        numeric = pd.to_numeric(frame[component], errors="coerce")
        if numeric.notna().sum() >= 3 and numeric.nunique(dropna=True) >= 2:
            result.append(component)
    return result


def _scope_frames(frame: pd.DataFrame) -> Iterable[Tuple[str, pd.DataFrame]]:
    yield "ALL", frame
    for side in ("LONG", "SHORT"):
        yield side, frame[frame["side"].eq(side)]
    if "symbol" in frame.columns:
        for symbol, group in frame.groupby("symbol", dropna=False):
            yield f"SYMBOL:{str(symbol).upper()}", group


def component_era_attribution(
    frame: pd.DataFrame,
    components: Sequence[str],
    config: FeatureDecayConfig,
) -> pd.DataFrame:
    if frame.empty or not components:
        return pd.DataFrame()
    records: List[Dict[str, Any]] = []
    for scope_name, scoped in _scope_frames(frame):
        for era in ERA_ORDER:
            era_frame = scoped[scoped["__era"].eq(era)]
            if len(era_frame) < config.minimum_scope_samples:
                continue
            for component in components:
                values = pd.to_numeric(era_frame[component], errors="coerce")
                valid = values.notna() & era_frame["__return"].notna()
                sample_count = int(valid.sum())
                if sample_count < config.minimum_scope_samples:
                    continue
                feature_values = values[valid]
                target = era_frame.loc[valid, "__return"]
                direction = float(EXPECTED_DIRECTIONS.get(component, 1.0))
                raw_corr = _rank_spearman(feature_values, target)
                spread = _quantile_spread(
                    feature_values,
                    target,
                    bins=config.quantile_bins,
                    min_bin_samples=config.minimum_quantile_samples,
                )
                records.append(
                    {
                        "scope": scope_name,
                        "era": era,
                        "component": component,
                        "component_label": COMPONENT_LABELS.get(component, component),
                        "expected_direction": direction,
                        "sample_count": sample_count,
                        "unique_values": int(feature_values.nunique()),
                        "feature_mean": _finite(feature_values.mean()),
                        "feature_std": _finite(feature_values.std(ddof=0)),
                        "spearman_to_return": raw_corr,
                        "aligned_spearman": raw_corr * direction,
                        **spread,
                        "aligned_top_minus_bottom": _finite(spread["top_minus_bottom"]) * direction,
                        "missing_share": float(1.0 - sample_count / max(1, len(era_frame))),
                    }
                )
    return pd.DataFrame(records)


def _era_row(by_era: pd.DataFrame, scope: str, component: str, era: str) -> Dict[str, Any]:
    subset = by_era[
        by_era["scope"].eq(scope)
        & by_era["component"].eq(component)
        & by_era["era"].eq(era)
    ]
    return subset.iloc[0].to_dict() if len(subset) else {}


def _classify_component(rows: Mapping[str, Dict[str, Any]], config: FeatureDecayConfig) -> str:
    recent = rows.get("RECENT", {})
    recent_n = int(recent.get("sample_count", 0) or 0)
    if recent_n < config.minimum_scope_samples:
        return "INSUFFICIENT_RECENT_DATA"
    available = [
        row for row in rows.values() if int(row.get("sample_count", 0) or 0) >= config.minimum_scope_samples
    ]
    if len(available) < 2:
        return "INSUFFICIENT_MULTI_ERA_DATA"

    aligned = [_finite(row.get("aligned_spearman")) for row in available]
    spreads = [_finite(row.get("aligned_top_minus_bottom")) for row in available]
    recent_corr = _finite(recent.get("aligned_spearman"))
    recent_spread = _finite(recent.get("aligned_top_minus_bottom"))
    legacy = rows.get("LEGACY", {})
    legacy_n = int(legacy.get("sample_count", 0) or 0)
    legacy_corr = _finite(legacy.get("aligned_spearman"))
    legacy_spread = _finite(legacy.get("aligned_top_minus_bottom"))

    recent_supportive = (
        recent_corr >= config.association_tolerance
        and recent_spread >= config.spread_tolerance_pct
    )
    recent_harmful = (
        recent_corr <= -config.association_tolerance
        and recent_spread <= -config.spread_tolerance_pct
    )
    if recent_harmful:
        return "RECENT_HARMFUL"
    if legacy_n >= config.minimum_scope_samples:
        legacy_supportive = (
            legacy_corr >= config.association_tolerance
            or legacy_spread >= config.spread_tolerance_pct
        )
        if legacy_supportive and (
            recent_corr < legacy_corr - config.decay_tolerance
            or recent_spread < legacy_spread - config.spread_tolerance_pct
        ) and not recent_supportive:
            return "DECAYED"
    if recent_supportive and all(value >= -config.association_tolerance for value in aligned):
        return "STABLE_OR_RECENT_SUPPORTIVE"
    signs = {int(np.sign(value)) for value in aligned if abs(value) >= config.association_tolerance}
    if len(signs) > 1:
        return "UNSTABLE_SIGN_FLIP"
    if max([abs(value) for value in aligned] + [0.0]) < config.association_tolerance and max(
        [abs(value) for value in spreads] + [0.0]
    ) < config.spread_tolerance_pct:
        return "NO_STANDALONE_SIGNAL"
    return "WEAK_OR_MIXED"


def summarize_component_decay(by_era: pd.DataFrame, config: FeatureDecayConfig) -> pd.DataFrame:
    if by_era is None or by_era.empty:
        return pd.DataFrame()
    records: List[Dict[str, Any]] = []
    keys = by_era[["scope", "component", "component_label", "expected_direction"]].drop_duplicates()
    for key in keys.to_dict(orient="records"):
        scope = str(key["scope"])
        component = str(key["component"])
        rows = {era: _era_row(by_era, scope, component, era) for era in ERA_ORDER}
        status = _classify_component(rows, config)
        payload: Dict[str, Any] = {
            "scope": scope,
            "component": component,
            "component_label": str(key["component_label"]),
            "expected_direction": _finite(key["expected_direction"], 1.0),
            "status": status,
            "promotion_eligible": False,
        }
        for era in ERA_ORDER:
            row = rows[era]
            prefix = era.lower()
            payload[f"{prefix}_samples"] = int(row.get("sample_count", 0) or 0)
            payload[f"{prefix}_aligned_spearman"] = _finite(row.get("aligned_spearman"))
            payload[f"{prefix}_aligned_spread"] = _finite(row.get("aligned_top_minus_bottom"))
            payload[f"{prefix}_feature_mean"] = _finite(row.get("feature_mean"))
        payload["recent_minus_legacy_spearman"] = (
            payload["recent_aligned_spearman"] - payload["legacy_aligned_spearman"]
        )
        payload["recent_minus_legacy_spread"] = (
            payload["recent_aligned_spread"] - payload["legacy_aligned_spread"]
        )
        records.append(payload)
    result = pd.DataFrame(records)
    if result.empty:
        return result
    order = {
        "RECENT_HARMFUL": 0,
        "DECAYED": 1,
        "UNSTABLE_SIGN_FLIP": 2,
        "WEAK_OR_MIXED": 3,
        "NO_STANDALONE_SIGNAL": 4,
        "STABLE_OR_RECENT_SUPPORTIVE": 5,
        "INSUFFICIENT_RECENT_DATA": 6,
        "INSUFFICIENT_MULTI_ERA_DATA": 7,
    }
    result["__order"] = result["status"].map(order).fillna(99)
    return result.sort_values(
        ["__order", "recent_minus_legacy_spearman", "recent_minus_legacy_spread"],
        ascending=[True, True, True],
    ).drop(columns="__order").reset_index(drop=True)


def component_distribution_drift(
    frame: pd.DataFrame,
    components: Sequence[str],
    config: FeatureDecayConfig,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    legacy = frame[frame["__era"].eq("LEGACY")]
    recent = frame[frame["__era"].eq("RECENT")]
    records: List[Dict[str, Any]] = []
    for scope_name, scoped in _scope_frames(frame):
        scope_legacy = scoped[scoped["__era"].eq("LEGACY")]
        scope_recent = scoped[scoped["__era"].eq("RECENT")]
        if len(scope_legacy) < config.minimum_scope_samples or len(scope_recent) < config.minimum_scope_samples:
            continue
        for component in components:
            ref = pd.to_numeric(scope_legacy[component], errors="coerce").dropna()
            cur = pd.to_numeric(scope_recent[component], errors="coerce").dropna()
            if len(ref) < config.minimum_scope_samples or len(cur) < config.minimum_scope_samples:
                continue
            psi = population_stability_index(ref, cur, bins=10)
            severity = "SEVERE" if psi >= config.psi_severe else "MODERATE" if psi >= config.psi_moderate else "LOW"
            records.append(
                {
                    "scope": scope_name,
                    "component": component,
                    "component_label": COMPONENT_LABELS.get(component, component),
                    "legacy_samples": int(len(ref)),
                    "recent_samples": int(len(cur)),
                    "legacy_mean": _finite(ref.mean()),
                    "recent_mean": _finite(cur.mean()),
                    "mean_delta": _finite(cur.mean() - ref.mean()),
                    "legacy_std": _finite(ref.std(ddof=0)),
                    "recent_std": _finite(cur.std(ddof=0)),
                    "psi": _finite(psi),
                    "severity": severity,
                }
            )
    return pd.DataFrame(records)


def component_redundancy_drift(
    frame: pd.DataFrame,
    components: Sequence[str],
    config: FeatureDecayConfig,
) -> pd.DataFrame:
    if len(components) < 2 or frame.empty:
        return pd.DataFrame()
    records: List[Dict[str, Any]] = []
    matrices: Dict[str, pd.DataFrame] = {}
    for era in ("LEGACY", "RECENT"):
        chunk = frame[frame["__era"].eq(era)]
        numeric = chunk[list(components)].apply(pd.to_numeric, errors="coerce")
        if len(numeric.dropna(how="all")) < config.minimum_scope_samples:
            matrices[era] = pd.DataFrame()
        else:
            matrices[era] = numeric.corr(method="spearman")
    for idx, left in enumerate(components):
        for right in components[idx + 1 :]:
            legacy_corr = _finite(matrices.get("LEGACY", pd.DataFrame()).get(left, {}).get(right, 0.0)) if not matrices.get("LEGACY", pd.DataFrame()).empty else 0.0
            recent_corr = _finite(matrices.get("RECENT", pd.DataFrame()).get(left, {}).get(right, 0.0)) if not matrices.get("RECENT", pd.DataFrame()).empty else 0.0
            records.append(
                {
                    "component_left": left,
                    "component_right": right,
                    "legacy_spearman": legacy_corr,
                    "recent_spearman": recent_corr,
                    "absolute_recent_correlation": abs(recent_corr),
                    "correlation_delta": recent_corr - legacy_corr,
                    "recent_redundancy_flag": bool(abs(recent_corr) >= 0.75),
                }
            )
    result = pd.DataFrame(records)
    if result.empty:
        return result
    return result.sort_values("absolute_recent_correlation", ascending=False).reset_index(drop=True)


def score_decay(frame: pd.DataFrame, config: FeatureDecayConfig) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    work = frame.copy()
    work["score"] = pd.to_numeric(work["score"], errors="coerce")
    work["score_band"] = pd.cut(work["score"], bins=SCORE_BINS, labels=SCORE_LABELS, right=False)
    records: List[Dict[str, Any]] = []
    for era in ERA_ORDER:
        era_frame = work[work["__era"].eq(era)]
        directional = era_frame[era_frame["side"].isin(["LONG", "SHORT"])]
        gate = directional[directional["score"].ge(config.fixed_score_threshold)]
        for label, chunk in (("ALL_DIRECTIONAL", directional), (f"SCORE_GE_{config.fixed_score_threshold:g}", gate)):
            metrics = return_metrics(chunk)
            records.append({"era": era, "segment": label, **metric_payload(metrics)})
        for band, chunk in directional.groupby("score_band", observed=True):
            metrics = return_metrics(chunk)
            records.append({"era": era, "segment": f"BAND_{band}", **metric_payload(metrics)})
    return pd.DataFrame(records)


def window_crosscheck(frames: Mapping[str, pd.DataFrame], threshold: float) -> pd.DataFrame:
    """Descriptive nested-window comparison; not independent evidence."""
    records: List[Dict[str, Any]] = []
    for window, raw in sorted(frames.items()):
        try:
            work = _deduplicate_decisions(_normalize_decay_rows(raw))
        except Exception:
            continue
        directional = work[work["side"].isin(["LONG", "SHORT"])]
        scopes = [("ALL", directional), ("LONG", directional[directional["side"].eq("LONG")]), ("SHORT", directional[directional["side"].eq("SHORT")])]
        for scope, scoped in scopes:
            for segment, segment_frame in (
                ("ALL_DIRECTIONAL", scoped),
                (f"SCORE_GE_{threshold:g}", scoped[pd.to_numeric(scoped["score"], errors="coerce").ge(threshold)]),
            ):
                metrics = return_metrics(segment_frame)
                records.append(
                    {
                        "window": str(window).upper(),
                        "scope": scope,
                        "segment": segment,
                        "overlapping_window_warning": True,
                        **metric_payload(metrics),
                    }
                )
    return pd.DataFrame(records)


def _feature_findings(summary: pd.DataFrame, drift: pd.DataFrame, redundancy: pd.DataFrame) -> List[str]:
    findings: List[str] = []
    if summary is None or summary.empty:
        findings.append("No component had enough multi-era observations for feature-decay classification.")
        return findings
    all_scope = summary[summary["scope"].eq("ALL")]
    harmful = all_scope[all_scope["status"].eq("RECENT_HARMFUL")]
    decayed = all_scope[all_scope["status"].eq("DECAYED")]
    supportive = all_scope[all_scope["status"].eq("STABLE_OR_RECENT_SUPPORTIVE")]
    if len(harmful):
        findings.append(
            "Components with adverse recent association after expected-direction alignment: "
            + ", ".join(harmful["component_label"].astype(str).tolist())
            + "."
        )
    if len(decayed):
        findings.append(
            "Components whose legacy association weakened materially in the recent era: "
            + ", ".join(decayed["component_label"].astype(str).tolist())
            + "."
        )
    if len(supportive):
        findings.append(
            "Components retaining supportive diagnostics (not promotion evidence): "
            + ", ".join(supportive["component_label"].astype(str).tolist())
            + "."
        )
    if drift is not None and not drift.empty:
        severe = drift[(drift["scope"].eq("ALL")) & (drift["severity"].eq("SEVERE"))]
        if len(severe):
            findings.append(
                "Severe recent distribution drift was detected for: "
                + ", ".join(severe["component_label"].astype(str).tolist())
                + "."
            )
    if redundancy is not None and not redundancy.empty:
        high = redundancy[redundancy["recent_redundancy_flag"]]
        if len(high):
            labels = ", ".join(
                f"{row.component_left}~{row.component_right}" for row in high.head(6).itertuples()
            )
            findings.append(f"High recent component redundancy was detected for: {labels}.")
    if not findings:
        findings.append("No single component showed a decisive, stable multi-cycle edge or decay signature.")
    return findings


def analyze_multi_cycle_feature_decay(
    frames: Mapping[str, pd.DataFrame],
    config: FeatureDecayConfig,
) -> Tuple[FeatureDecayReport, FeatureDecayArtifacts]:
    config.validate()
    blockers: List[str] = []
    warnings: List[str] = [
        "3Y, 5Y and FULL windows overlap; non-overlapping eras from the longest replay are the primary evidence.",
        "All positive findings are diagnostic only and require untouched Fresh OOS and Forward confirmation.",
    ]
    selected_name, selected_raw, selection_warnings = select_longest_replay(frames)
    warnings.extend(selection_warnings)
    rows_loaded = int(len(selected_raw))
    if selected_name is None or selected_raw.empty:
        report = FeatureDecayReport(
            status="READY_AWAITING_MULTI_CYCLE_REPLAYS",
            mode=MODE,
            version=VERSION,
            created_utc=datetime.now(timezone.utc).isoformat(),
            development_cutoff_utc=config.development_cutoff_utc,
            selected_replay_window=None,
            available_replay_windows=sorted(str(key).upper() for key in frames),
            rows_loaded=0,
            rows_usable=0,
            available_components=[],
            era_boundaries={},
            era_counts={},
            fixed_score_threshold=config.fixed_score_threshold,
            key_findings=["No usable multi-cycle replay was available."],
            blockers=[],
            warnings=warnings,
        )
        return report, FeatureDecayArtifacts()

    try:
        era_frame, boundaries = assign_non_overlapping_eras(selected_raw, config)
    except Exception as exc:
        blockers.append(f"Failed to create non-overlapping eras: {type(exc).__name__}: {exc}")
        era_frame = pd.DataFrame()
        boundaries = {}

    directional = era_frame[era_frame["side"].isin(["LONG", "SHORT"])].copy() if not era_frame.empty else pd.DataFrame()
    era_counts = {era: int((directional["__era"].eq(era)).sum()) for era in ERA_ORDER} if not directional.empty else {era: 0 for era in ERA_ORDER}
    for era, count in era_counts.items():
        if count < config.minimum_era_samples:
            warnings.append(f"{era} has only {count} directional rows; some diagnostics will be ineligible.")
    components = available_components(directional, config.components) if not directional.empty else []
    if not components:
        blockers.append("No non-constant decision-time score components were available in the replay.")

    artifacts = FeatureDecayArtifacts()
    if not blockers:
        artifacts.component_by_era = component_era_attribution(directional, components, config)
        artifacts.component_decay_summary = summarize_component_decay(artifacts.component_by_era, config)
        artifacts.distribution_drift = component_distribution_drift(directional, components, config)
        artifacts.component_redundancy_drift = component_redundancy_drift(directional, components, config)
        artifacts.regime_side_matrix = regime_side_matrix(directional, min_samples=1)
        artifacts.regime_drift_summary = summarize_regime_drift(artifacts.regime_side_matrix, config.regime)
        artifacts.score_decay = score_decay(directional, config)
        artifacts.window_crosscheck = window_crosscheck(frames, config.fixed_score_threshold)

    key_findings = _feature_findings(
        artifacts.component_decay_summary,
        artifacts.distribution_drift,
        artifacts.component_redundancy_drift,
    )
    key_findings.extend(regime_findings(artifacts.regime_drift_summary, config.regime))
    if not directional.empty:
        recent = directional[directional["__era"].eq("RECENT")]
        legacy = directional[directional["__era"].eq("LEGACY")]
        recent_metrics = return_metrics(recent)
        legacy_metrics = return_metrics(legacy)
        key_findings.append(
            f"Directional expectancy changed from {legacy_metrics.expectancy:.6f}% in LEGACY "
            f"to {recent_metrics.expectancy:.6f}% in RECENT."
        )
        recent_gate = recent[pd.to_numeric(recent["score"], errors="coerce").ge(config.fixed_score_threshold)]
        gate_metrics = return_metrics(recent_gate)
        key_findings.append(
            f"The frozen score>={config.fixed_score_threshold:g} benchmark had recent n={gate_metrics.sample_count}, "
            f"expectancy={gate_metrics.expectancy:.6f}% and PF={gate_metrics.profit_factor}."
        )

    if blockers:
        status = "FAIL_CLOSED"
    elif any(count < config.minimum_era_samples for count in era_counts.values()):
        status = "COMPLETE_WITH_INSUFFICIENT_ERAS"
    else:
        status = "COMPLETE_NO_PROMOTION"

    report = FeatureDecayReport(
        status=status,
        mode=MODE,
        version=VERSION,
        created_utc=datetime.now(timezone.utc).isoformat(),
        development_cutoff_utc=config.development_cutoff_utc,
        selected_replay_window=selected_name,
        available_replay_windows=sorted(str(key).upper() for key in frames),
        rows_loaded=rows_loaded,
        rows_usable=int(len(directional)),
        available_components=components,
        era_boundaries=boundaries,
        era_counts=era_counts,
        fixed_score_threshold=config.fixed_score_threshold,
        key_findings=key_findings,
        blockers=blockers,
        warnings=warnings,
    )
    return report, artifacts


def _csv_safe(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def _markdown(report: FeatureDecayReport, artifacts: FeatureDecayArtifacts) -> str:
    lines = [
        "# Freakto Multi-Cycle Feature Decay & Regime Drift",
        "",
        f"- Status: **{report.status}**",
        f"- Mode: `{report.mode}`",
        f"- Selected replay: **{report.selected_replay_window or 'NONE'}**",
        f"- Development cutoff: `{report.development_cutoff_utc}`",
        f"- Rows loaded/usable: **{report.rows_loaded} / {report.rows_usable}**",
        f"- Components: **{len(report.available_components)}**",
        f"- Fixed benchmark: `score >= {report.fixed_score_threshold:g}`",
        f"- Promotion applied: **{report.promotion_applied}**",
        f"- Paper/Live enabled: **{report.paper_live_enabled}**",
        "",
        "## Non-overlapping era counts",
        "",
    ]
    for era in ERA_ORDER:
        lines.append(f"- {era}: **{report.era_counts.get(era, 0)}**")
    lines.extend(["", "## Key findings", ""])
    lines.extend(f"- {item}" for item in report.key_findings)

    summary = artifacts.component_decay_summary
    if summary is not None and not summary.empty:
        lines.extend(["", "## Component classifications — ALL scope", ""])
        all_scope = summary[summary["scope"].eq("ALL")]
        if all_scope.empty:
            lines.append("No ALL-scope component classifications were available.")
        else:
            for row in all_scope.itertuples():
                lines.append(
                    f"- **{row.component_label}**: `{row.status}` | "
                    f"legacy rho={row.legacy_aligned_spearman:.4f}, "
                    f"recent rho={row.recent_aligned_spearman:.4f}, "
                    f"recent spread={row.recent_aligned_spread:.6f}%"
                )

    regimes = artifacts.regime_drift_summary
    if regimes is not None and not regimes.empty:
        lines.extend(["", "## Regime/side diagnostics — ALL scope", ""])
        all_regimes = regimes[regimes["symbol_scope"].eq("ALL")]
        for row in all_regimes.head(20).itertuples():
            lines.append(
                f"- **{row.regime}/{row.side}**: `{row.status}` | "
                f"legacy={row.legacy_expectancy:.6f}% | recent={row.recent_expectancy:.6f}% | "
                f"recent n={row.recent_samples}"
            )

    if report.blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- {item}" for item in report.blockers)
    if report.warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {item}" for item in report.warnings)
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This analysis is development diagnostic only. It does not tune or promote weights, thresholds, regimes, Paper trading, or Live trading.",
        ]
    )
    return "\n".join(lines)


def write_feature_decay_outputs(
    report: FeatureDecayReport,
    artifacts: FeatureDecayArtifacts,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, str]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    paths = {
        "component_by_era": root / "component_by_era.csv",
        "component_decay_summary": root / "component_decay_summary.csv",
        "distribution_drift": root / "component_distribution_drift.csv",
        "component_redundancy_drift": root / "component_redundancy_drift.csv",
        "regime_side_matrix": root / "regime_side_matrix.csv",
        "regime_drift_summary": root / "regime_drift_summary.csv",
        "score_decay": root / "score_decay.csv",
        "window_crosscheck": root / "nested_window_crosscheck.csv",
        "json": root / "multi_cycle_feature_decay_report.json",
        "markdown": root / "multi_cycle_feature_decay_report.md",
    }
    for name in (
        "component_by_era",
        "component_decay_summary",
        "distribution_drift",
        "component_redundancy_drift",
        "regime_side_matrix",
        "regime_drift_summary",
        "score_decay",
        "window_crosscheck",
    ):
        _csv_safe(getattr(artifacts, name), paths[name])
    report.output_files = {name: str(path) for name, path in paths.items()}
    paths["json"].write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    paths["markdown"].write_text(_markdown(report, artifacts), encoding="utf-8")
    return report.output_files


def load_and_analyze(
    replay_root: str | Path = DEFAULT_REPLAY_DIR,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    config: Optional[FeatureDecayConfig] = None,
) -> Tuple[FeatureDecayReport, FeatureDecayArtifacts]:
    cfg = config or FeatureDecayConfig()
    frames = load_replay_files(replay_root)
    report, artifacts = analyze_multi_cycle_feature_decay(frames, cfg)
    write_feature_decay_outputs(report, artifacts, output_dir)
    return report, artifacts


__all__ = [
    "VERSION",
    "MODE",
    "DEFAULT_COMPONENTS",
    "FeatureDecayConfig",
    "FeatureDecayReport",
    "FeatureDecayArtifacts",
    "validate_feature_names",
    "select_longest_replay",
    "assign_non_overlapping_eras",
    "available_components",
    "component_era_attribution",
    "summarize_component_decay",
    "component_distribution_drift",
    "component_redundancy_drift",
    "score_decay",
    "window_crosscheck",
    "analyze_multi_cycle_feature_decay",
    "write_feature_decay_outputs",
    "load_and_analyze",
]
