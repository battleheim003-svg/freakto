"""Leakage-safe Champion/Challenger evaluation for Freakto.

This module compares the existing technical score gate (Champion benchmark)
with expectancy-aware shadow challengers.  Models are fitted on Train,
thresholds are selected on Optimize, and the selected policy is evaluated once
on untouched Holdout.  A nested pre-holdout walk-forward diagnostic is also
required before a challenger can be considered promotable.

No function in this module writes runtime configuration or enables Paper/Live
trading.  Even a passing challenger remains a research recommendation only.
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

from .expectancy_challenger import (
    ChallengerConfig,
    ChallengerVariant,
    DEFAULT_VARIANTS,
    ExpectancyChallenger,
    VERSION as CHALLENGER_VERSION,
)
from .score_attribution import load_attribution_dataset
from .threshold_optimizer import selection_metrics

VERSION = "v10.7.0"
DEFAULT_DATASET = Path("logs/market_replay/market_replay_evaluations.csv")
DEFAULT_OUTPUT_DIR = Path("logs/champion_challenger")


@dataclass(frozen=True)
class ChampionChallengerConfig:
    train_ratio: float = 0.60
    optimize_ratio: float = 0.20
    purge_rows: int = 6
    minimum_total_rows: int = 1200
    minimum_optimize_selected: int = 50
    minimum_holdout_selected: int = 60
    minimum_side_holdout: int = 20
    champion_score_threshold: int = 70
    minimum_profit_factor: float = 1.05
    minimum_expectancy_pct: float = 0.0
    minimum_walk_forward_pass_rate: float = 2.0 / 3.0
    maximum_drawdown_deterioration_ratio: float = 0.10
    minimum_positive_holdout_quarters: int = 2
    maximum_single_quarter_profit_share: float = 0.70
    confidence_z: float = 1.96
    walk_forward_folds: int = 3
    walk_forward_optimize_ratio: float = 0.10
    walk_forward_test_ratio: float = 0.10
    threshold_grid: tuple[float, ...] = (
        0.00,
        0.05,
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.40,
        0.50,
        0.60,
        0.75,
        1.00,
    )

    def validate(self) -> None:
        if not 0 < self.train_ratio < 1 or not 0 < self.optimize_ratio < 1:
            raise ValueError("train_ratio and optimize_ratio must be in (0, 1).")
        if self.train_ratio + self.optimize_ratio >= 1:
            raise ValueError("train_ratio + optimize_ratio must be below 1.")
        if self.purge_rows < 0:
            raise ValueError("purge_rows cannot be negative.")
        if self.minimum_total_rows <= 0:
            raise ValueError("minimum_total_rows must be positive.")
        if self.minimum_optimize_selected <= 0 or self.minimum_holdout_selected <= 0:
            raise ValueError("selection minimums must be positive.")
        if self.walk_forward_folds < 1:
            raise ValueError("walk_forward_folds must be positive.")
        if not self.threshold_grid:
            raise ValueError("threshold_grid cannot be empty.")
        if any(value < 0 for value in self.threshold_grid):
            raise ValueError("Expected-value thresholds cannot be negative.")


@dataclass(frozen=True)
class SplitSummary:
    name: str
    rows: int
    start_timestamp: Optional[str]
    end_timestamp: Optional[str]


@dataclass
class ChampionChallengerResult:
    created_utc: str
    version: str
    challenger_version: str
    status: str
    dataset_path: str
    dataset_sha256: str
    selected_run_id: Optional[str]
    rows_loaded: int
    rows_usable: int
    mode: str = "RESEARCH_SHADOW_ONLY"
    shadow_only: bool = True
    paper_live_enabled: bool = False
    promotion_applied: bool = False
    recommended_variant: Optional[str] = None
    recommended_threshold_pct: Optional[float] = None
    splits: list[SplitSummary] = field(default_factory=list)
    champion_holdout: dict = field(default_factory=dict)
    variant_results: list[dict] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    output_files: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = asdict(self)
        data["splits"] = [asdict(item) for item in self.splits]
        return data


@dataclass
class ChampionChallengerArtifacts:
    summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    threshold_candidates: pd.DataFrame = field(default_factory=pd.DataFrame)
    walk_forward: pd.DataFrame = field(default_factory=pd.DataFrame)
    holdout_predictions: pd.DataFrame = field(default_factory=pd.DataFrame)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp_summary(name: str, frame: pd.DataFrame) -> SplitSummary:
    timestamps = frame.get("_event_time", pd.Series(dtype="datetime64[ns, UTC]")).dropna()
    return SplitSummary(
        name=name,
        rows=int(len(frame)),
        start_timestamp=str(timestamps.iloc[0]) if not timestamps.empty else None,
        end_timestamp=str(timestamps.iloc[-1]) if not timestamps.empty else None,
    )


def chronological_three_way_split(
    frame: pd.DataFrame,
    config: ChampionChallengerConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[SplitSummary]]:
    config.validate()
    if len(frame) < config.minimum_total_rows:
        raise ValueError(
            f"At least {config.minimum_total_rows} usable rows are required; found {len(frame)}."
        )
    ordered = frame.sort_values(["_event_time", "_row_order"], kind="stable").reset_index(drop=True)
    if ordered["_event_time"].isna().any():
        raise ValueError("Chronological Champion/Challenger evaluation requires valid timestamps.")
    unique_times = pd.Index(ordered["_event_time"].drop_duplicates().sort_values())
    if len(unique_times) < 30:
        raise ValueError("At least 30 unique decision timestamps are required.")
    train_boundary = int(len(unique_times) * config.train_ratio)
    optimize_boundary = int(len(unique_times) * (config.train_ratio + config.optimize_ratio))
    purge = int(config.purge_rows)
    train_times = unique_times[: max(0, train_boundary - purge)]
    optimize_times = unique_times[
        train_boundary : max(train_boundary, optimize_boundary - purge)
    ]
    holdout_times = unique_times[optimize_boundary:]
    train = ordered[ordered["_event_time"].isin(train_times)].copy()
    optimize = ordered[ordered["_event_time"].isin(optimize_times)].copy()
    holdout = ordered[ordered["_event_time"].isin(holdout_times)].copy()
    if min(len(train), len(optimize), len(holdout)) < 100:
        raise ValueError("Each chronological split must contain at least 100 rows after purging.")
    summaries = [
        _timestamp_summary("train", train),
        _timestamp_summary("optimize", optimize),
        _timestamp_summary("holdout", holdout),
    ]
    return train, optimize, holdout, summaries


def _numeric(frame: pd.DataFrame, column: str, default: float = 0.0) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").fillna(default).astype(float)


def champion_mask(frame: pd.DataFrame, config: ChampionChallengerConfig) -> pd.Series:
    """Technical Champion benchmark without the unavailable empirical edge gate.

    The current runtime edge gate is intentionally not bypassed in production.
    This mask is a research benchmark representing the existing component and
    score logic before empirical-edge fail-closed blocking.
    """

    side = frame["side"].astype(str).str.upper()
    regime = frame.get("_regime_group", frame.get("regime_label", "UNKNOWN"))
    regime = pd.Series(regime, index=frame.index).astype(str).str.upper()
    return (
        side.isin(["LONG", "SHORT"])
        & _numeric(frame, "score").ge(config.champion_score_threshold)
        & _numeric(frame, "trend_score").ge(20)
        & _numeric(frame, "momentum_score").ge(18)
        & _numeric(frame, "volume_score").ge(5)
        & _numeric(frame, "structure_score").ge(6)
        & _numeric(frame, "risk_penalty").gt(-10)
        & ~regime.isin(["SIDEWAYS", "UNKNOWN"])
    )


def _metrics_from_mask(frame: pd.DataFrame, mask: pd.Series) -> dict:
    metrics = selection_metrics(frame.loc[mask, "evaluated_return"]).to_dict()
    selected = pd.to_numeric(frame.loc[mask, "evaluated_return"], errors="coerce").dropna()
    if len(selected) >= 2:
        standard_error = float(selected.std(ddof=1) / math.sqrt(len(selected)))
        lower = float(selected.mean() - 1.96 * standard_error)
        upper = float(selected.mean() + 1.96 * standard_error)
    else:
        standard_error = 0.0
        lower = 0.0
        upper = 0.0
    metrics.update(
        {
            "expectancy_standard_error": round(standard_error, 6),
            "expectancy_ci95_lower": round(lower, 6),
            "expectancy_ci95_upper": round(upper, 6),
        }
    )
    return metrics


def _side_metrics(frame: pd.DataFrame, mask: pd.Series) -> dict:
    output: dict[str, dict] = {}
    for side in ("LONG", "SHORT"):
        output[side] = _metrics_from_mask(frame, mask & frame["side"].astype(str).str.upper().eq(side))
    return output


def _prediction_diagnostics(frame: pd.DataFrame, predictions: pd.DataFrame) -> dict:
    available = predictions["model_available"].astype(bool)
    probability = pd.to_numeric(
        predictions.loc[available, "predicted_probability_win"], errors="coerce"
    )
    expected_value = pd.to_numeric(
        predictions.loc[available, "predicted_expected_value_pct"], errors="coerce"
    )
    actual_return = pd.to_numeric(frame.loc[available, "evaluated_return"], errors="coerce")
    actual_win = actual_return.gt(0).astype(float)
    clean_probability = pd.concat([probability, actual_win], axis=1).dropna()
    if clean_probability.empty:
        brier = 0.0
    else:
        brier = float(
            ((clean_probability.iloc[:, 0] - clean_probability.iloc[:, 1]) ** 2).mean()
        )
    pair = pd.concat([expected_value, actual_return], axis=1).dropna()
    if len(pair) >= 3 and pair.iloc[:, 0].nunique() > 1 and pair.iloc[:, 1].nunique() > 1:
        correlation = float(pair.iloc[:, 0].corr(pair.iloc[:, 1], method="spearman"))
        if pd.isna(correlation):
            correlation = 0.0
    else:
        correlation = 0.0
    quantiles = expected_value.dropna().quantile([0.10, 0.50, 0.90]).to_dict()
    return {
        "sample_count": int(len(pair)),
        "probability_brier_score": round(brier, 6),
        "expected_value_return_spearman": round(correlation, 6),
        "predicted_ev_p10": round(float(quantiles.get(0.10, 0.0)), 6),
        "predicted_ev_p50": round(float(quantiles.get(0.50, 0.0)), 6),
        "predicted_ev_p90": round(float(quantiles.get(0.90, 0.0)), 6),
    }


def _temporal_stability(frame: pd.DataFrame, mask: pd.Series) -> dict:
    selected = frame.loc[mask, ["_event_time", "evaluated_return"]].copy()
    selected["evaluated_return"] = pd.to_numeric(selected["evaluated_return"], errors="coerce")
    selected = selected.dropna(subset=["_event_time", "evaluated_return"])
    if selected.empty:
        return {
            "quarter_count": 0,
            "positive_quarters": 0,
            "maximum_single_quarter_profit_share": 1.0,
            "quarter_metrics": [],
        }
    # Equal chronological buckets are more robust than calendar quarters for a
    # replay whose covered calendar span may be irregular.
    bucket_count = min(4, max(1, len(selected)))
    selected["holdout_quarter"] = pd.qcut(
        np.arange(len(selected)), q=bucket_count, labels=False, duplicates="drop"
    )
    rows: list[dict] = []
    for bucket, group in selected.groupby("holdout_quarter", sort=True):
        metrics = selection_metrics(group["evaluated_return"]).to_dict()
        rows.append({"quarter": int(bucket) + 1, **metrics})
    positive = sum(float(row["expectancy"]) > 0 for row in rows)
    positive_profit = [max(0.0, float(row["total_return"])) for row in rows]
    total_positive = sum(positive_profit)
    max_share = max(positive_profit) / total_positive if total_positive > 0 else 1.0
    return {
        "quarter_count": len(rows),
        "positive_quarters": int(positive),
        "maximum_single_quarter_profit_share": round(float(max_share), 6),
        "quarter_metrics": rows,
    }


def apply_challenger_threshold(predictions: pd.DataFrame, threshold: float) -> pd.Series:
    expected = pd.to_numeric(predictions["predicted_expected_value_pct"], errors="coerce")
    return (
        predictions["shadow_only"].astype(bool)
        & ~predictions["paper_live_enabled"].astype(bool)
        & predictions["model_available"].astype(bool)
        & predictions["base_gate_passed"].astype(bool)
        & expected.ge(float(threshold))
        & expected.notna()
    )


def _candidate_objective(metrics: dict, target_sample_count: int = 150) -> float:
    if int(metrics["sample_count"]) <= 0:
        return float("-inf")
    reliability = min(1.0, int(metrics["sample_count"]) / max(1, target_sample_count))
    pf = min(max(float(metrics["profit_factor"]), 0.0), 5.0)
    drawdown_penalty = abs(min(float(metrics["max_drawdown"]), 0.0)) * 0.01
    return (
        float(metrics["expectancy"]) * 3.0
        + (float(metrics["win_rate"]) - 0.5) * 1.5
        + math.log1p(pf) * 0.20
        + reliability * 0.15
        - drawdown_penalty
    )


def select_expected_value_threshold(
    optimize: pd.DataFrame,
    predictions: pd.DataFrame,
    config: ChampionChallengerConfig,
    *,
    variant_name: str,
    fold: str = "MAIN",
) -> tuple[Optional[float], pd.DataFrame]:
    rows: list[dict] = []
    best_threshold: Optional[float] = None
    best_key: Optional[tuple[float, int, float]] = None
    for threshold in config.threshold_grid:
        mask = apply_challenger_threshold(predictions, threshold)
        metrics = _metrics_from_mask(optimize, mask)
        viable = (
            int(metrics["sample_count"]) >= config.minimum_optimize_selected
            and float(metrics["expectancy"]) > config.minimum_expectancy_pct
            and float(metrics["profit_factor"]) >= config.minimum_profit_factor
        )
        objective = _candidate_objective(metrics) if viable else float("-inf")
        row = {
            "fold": fold,
            "variant": variant_name,
            "threshold_pct": float(threshold),
            **metrics,
            "viable": bool(viable),
            "objective": objective,
        }
        rows.append(row)
        key = (objective, int(metrics["sample_count"]), float(metrics["expectancy"]))
        if viable and (best_key is None or key > best_key):
            best_key = key
            best_threshold = float(threshold)
    candidates = pd.DataFrame(rows)
    if not candidates.empty:
        candidates = candidates.sort_values(
            ["viable", "objective", "sample_count", "expectancy"],
            ascending=[False, False, False, False],
            kind="stable",
        ).reset_index(drop=True)
    return best_threshold, candidates


def _walk_forward_windows(
    development: pd.DataFrame,
    config: ChampionChallengerConfig,
) -> list[tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    ordered = development.sort_values(["_event_time", "_row_order"], kind="stable").reset_index(drop=True)
    if ordered["_event_time"].isna().any():
        return []
    unique_times = pd.Index(ordered["_event_time"].drop_duplicates().sort_values())
    period_count = len(unique_times)
    opt_size = max(12, int(period_count * config.walk_forward_optimize_ratio))
    test_size = max(12, int(period_count * config.walk_forward_test_ratio))
    purge = int(config.purge_rows)
    windows: list[tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame]] = []
    for fold_index in range(config.walk_forward_folds):
        train_fraction = 0.45 + fold_index * 0.10
        train_boundary = int(period_count * train_fraction)
        optimize_boundary = min(period_count, train_boundary + opt_size)
        test_boundary = min(period_count, optimize_boundary + test_size)
        train_times = unique_times[: max(0, train_boundary - purge)]
        optimize_times = unique_times[
            train_boundary : max(train_boundary, optimize_boundary - purge)
        ]
        test_times = unique_times[optimize_boundary:test_boundary]
        train = ordered[ordered["_event_time"].isin(train_times)].copy()
        optimize = ordered[ordered["_event_time"].isin(optimize_times)].copy()
        test = ordered[ordered["_event_time"].isin(test_times)].copy()
        if min(len(train), len(optimize), len(test)) < 100:
            continue
        windows.append((f"WF_{fold_index + 1}", train, optimize, test))
    return windows


def run_walk_forward(
    development: pd.DataFrame,
    variant: ChallengerVariant,
    config: ChampionChallengerConfig,
    challenger_config: ChallengerConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict] = []
    candidate_parts: list[pd.DataFrame] = []
    for fold_name, train, optimize, test in _walk_forward_windows(development, config):
        model = ExpectancyChallenger(variant, challenger_config)
        fit = model.fit(train)
        if fit.status != "READY":
            rows.append(
                {
                    "fold": fold_name,
                    "variant": variant.name,
                    "status": "MODEL_FAIL_CLOSED",
                    "selected_threshold_pct": None,
                    **selection_metrics(pd.Series(dtype=float)).to_dict(),
                    "pass": False,
                    "blocker": "; ".join(fit.blockers),
                }
            )
            continue
        optimize_predictions = model.predict(optimize)
        threshold, candidates = select_expected_value_threshold(
            optimize,
            optimize_predictions,
            config,
            variant_name=variant.name,
            fold=fold_name,
        )
        candidate_parts.append(candidates)
        test_predictions = model.predict(test)
        if threshold is None:
            mask = pd.Series(False, index=test.index)
            status = "NO_OPTIMIZE_POLICY"
        else:
            mask = apply_challenger_threshold(test_predictions, threshold)
            status = "EVALUATED"
        metrics = _metrics_from_mask(test, mask)
        passed = (
            threshold is not None
            and int(metrics["sample_count"]) >= max(20, config.minimum_holdout_selected // 2)
            and float(metrics["expectancy"]) > config.minimum_expectancy_pct
            and float(metrics["profit_factor"]) >= config.minimum_profit_factor
        )
        rows.append(
            {
                "fold": fold_name,
                "variant": variant.name,
                "status": status,
                "selected_threshold_pct": threshold,
                **metrics,
                "pass": bool(passed),
                "blocker": "" if passed else "Walk-forward test did not preserve positive edge.",
            }
        )
    return pd.DataFrame(rows), pd.concat(candidate_parts, ignore_index=True) if candidate_parts else pd.DataFrame()


def _promotion_checks(
    *,
    holdout_metrics: dict,
    side_metrics: dict,
    temporal: dict,
    champion_metrics: dict,
    walk_forward_rows: pd.DataFrame,
    threshold: Optional[float],
    variant: ChallengerVariant,
    config: ChampionChallengerConfig,
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if threshold is None:
        blockers.append("No positive Optimize threshold survived.")
    if int(holdout_metrics["sample_count"]) < config.minimum_holdout_selected:
        blockers.append("Holdout sample count is insufficient.")
    if float(holdout_metrics["expectancy"]) <= config.minimum_expectancy_pct:
        blockers.append("Holdout expectancy is not positive.")
    if float(holdout_metrics["profit_factor"]) < config.minimum_profit_factor:
        blockers.append("Holdout profit factor is below the promotion floor.")
    if float(holdout_metrics["expectancy_ci95_lower"]) <= 0:
        blockers.append("Holdout expectancy 95% confidence interval crosses zero.")

    champion_drawdown = float(champion_metrics.get("max_drawdown", 0.0))
    challenger_drawdown = float(holdout_metrics.get("max_drawdown", 0.0))
    allowed_worse = abs(champion_drawdown) * config.maximum_drawdown_deterioration_ratio
    if champion_drawdown < 0 and challenger_drawdown < champion_drawdown - allowed_worse:
        blockers.append("Holdout drawdown is materially worse than Champion.")

    if walk_forward_rows.empty:
        blockers.append("Walk-forward evidence is unavailable.")
    else:
        pass_rate = float(walk_forward_rows["pass"].astype(bool).mean())
        if pass_rate < config.minimum_walk_forward_pass_rate:
            blockers.append("Walk-forward pass rate is below the stability requirement.")

    if int(temporal.get("positive_quarters", 0)) < min(
        config.minimum_positive_holdout_quarters,
        int(temporal.get("quarter_count", 0)),
    ):
        blockers.append("Holdout edge is not positive across enough chronological quarters.")
    if float(temporal.get("maximum_single_quarter_profit_share", 1.0)) > config.maximum_single_quarter_profit_share:
        blockers.append("Holdout profit is overly concentrated in one chronological quarter.")

    allowed = {side.upper() for side in variant.allowed_sides}
    if allowed == {"LONG", "SHORT"}:
        represented = [
            side
            for side, metrics in side_metrics.items()
            if int(metrics.get("sample_count", 0)) >= config.minimum_side_holdout
        ]
        if len(represented) < 2:
            blockers.append("Two-sided challenger lacks minimum LONG/SHORT Holdout representation.")
    return len(blockers) == 0, blockers


def run_champion_challenger(
    dataset_path: Path | str = DEFAULT_DATASET,
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    run_id: Optional[str] = None,
    variants: Sequence[ChallengerVariant] = DEFAULT_VARIANTS,
    config: ChampionChallengerConfig = ChampionChallengerConfig(),
    challenger_config: ChallengerConfig = ChallengerConfig(),
) -> tuple[ChampionChallengerResult, ChampionChallengerArtifacts]:
    config.validate()
    challenger_config.validate()
    source = Path(dataset_path)
    frame, metadata, warnings = load_attribution_dataset(source, run_id=run_id)
    result = ChampionChallengerResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        version=VERSION,
        challenger_version=CHALLENGER_VERSION,
        status="RUNNING",
        dataset_path=str(source),
        dataset_sha256=_sha256(source),
        selected_run_id=metadata.get("selected_run_id"),
        rows_loaded=int(metadata.get("rows_loaded", len(frame))),
        rows_usable=int(len(frame)),
    )
    result.key_findings.extend(warnings)
    if len(frame) < config.minimum_total_rows:
        result.status = "INSUFFICIENT_DATA"
        result.blockers.append(
            f"At least {config.minimum_total_rows} usable rows are required; found {len(frame)}."
        )
        return result, ChampionChallengerArtifacts()

    train, optimize, holdout, splits = chronological_three_way_split(frame, config)
    result.splits = splits
    champion_holdout_mask = champion_mask(holdout, config)
    champion_metrics = _metrics_from_mask(holdout, champion_holdout_mask)
    champion_side = _side_metrics(holdout, champion_holdout_mask)
    champion_temporal = _temporal_stability(holdout, champion_holdout_mask)
    result.champion_holdout = {
        "name": "TECHNICAL_CHAMPION_RESEARCH_BENCHMARK",
        **champion_metrics,
        "by_side": champion_side,
        "temporal_stability": champion_temporal,
        "runtime_empirical_edge_gate_bypassed": False,
        "note": (
            "Research benchmark only. Runtime empirical edge remains fail-closed and is not changed."
        ),
    }

    summary_rows: list[dict] = []
    candidate_parts: list[pd.DataFrame] = []
    walk_forward_parts: list[pd.DataFrame] = []
    prediction_parts: list[pd.DataFrame] = []
    promotable: list[dict] = []
    development = pd.concat([train, optimize], ignore_index=True)

    for variant in variants:
        variant.validate()
        model = ExpectancyChallenger(variant, challenger_config)
        fit_summary = model.fit(train)
        if fit_summary.status != "READY":
            variant_result = {
                "variant": variant.name,
                "description": variant.description,
                "status": "MODEL_FAIL_CLOSED",
                "selected_threshold_pct": None,
                "fit_summary": fit_summary.to_dict(),
                "holdout": selection_metrics(pd.Series(dtype=float)).to_dict(),
                "by_side": {},
                "temporal_stability": {},
                "walk_forward_pass_rate": 0.0,
                "promotable": False,
                "promotion_blockers": fit_summary.blockers,
            }
            result.variant_results.append(variant_result)
            summary_rows.append(
                {
                    "variant": variant.name,
                    "status": "MODEL_FAIL_CLOSED",
                    "promotable": False,
                    "selected_threshold_pct": None,
                    **selection_metrics(pd.Series(dtype=float)).to_dict(),
                    "walk_forward_pass_rate": 0.0,
                    "promotion_blockers": "; ".join(fit_summary.blockers),
                }
            )
            continue

        optimize_predictions = model.predict(optimize)
        selected_threshold, candidates = select_expected_value_threshold(
            optimize,
            optimize_predictions,
            config,
            variant_name=variant.name,
        )
        candidate_parts.append(candidates)
        holdout_predictions = model.predict(holdout)
        fixed_zero_mask = apply_challenger_threshold(holdout_predictions, 0.0)
        fixed_zero_metrics = _metrics_from_mask(holdout, fixed_zero_mask)
        prediction_diagnostics = _prediction_diagnostics(holdout, holdout_predictions)
        if selected_threshold is None:
            holdout_mask = pd.Series(False, index=holdout.index)
        else:
            holdout_mask = apply_challenger_threshold(holdout_predictions, selected_threshold)
        holdout_metrics = _metrics_from_mask(holdout, holdout_mask)
        side_metrics = _side_metrics(holdout, holdout_mask)
        temporal = _temporal_stability(holdout, holdout_mask)

        walk_forward, wf_candidates = run_walk_forward(
            development,
            variant,
            config,
            challenger_config,
        )
        if not walk_forward.empty:
            walk_forward_parts.append(walk_forward)
        if not wf_candidates.empty:
            candidate_parts.append(wf_candidates)
        wf_pass_rate = float(walk_forward["pass"].astype(bool).mean()) if not walk_forward.empty else 0.0

        is_promotable, promotion_blockers = _promotion_checks(
            holdout_metrics=holdout_metrics,
            side_metrics=side_metrics,
            temporal=temporal,
            champion_metrics=champion_metrics,
            walk_forward_rows=walk_forward,
            threshold=selected_threshold,
            variant=variant,
            config=config,
        )
        status = "PASS" if is_promotable else "FAIL"
        variant_result = {
            "variant": variant.name,
            "description": variant.description,
            "status": status,
            "selected_threshold_pct": selected_threshold,
            "fit_summary": fit_summary.to_dict(),
            "holdout": holdout_metrics,
            "fixed_zero_ev_holdout": fixed_zero_metrics,
            "prediction_diagnostics": prediction_diagnostics,
            "by_side": side_metrics,
            "temporal_stability": temporal,
            "walk_forward_pass_rate": round(wf_pass_rate, 6),
            "promotable": bool(is_promotable),
            "promotion_blockers": promotion_blockers,
            "shadow_only": True,
            "paper_live_enabled": False,
        }
        result.variant_results.append(variant_result)
        summary_rows.append(
            {
                "variant": variant.name,
                "status": status,
                "promotable": bool(is_promotable),
                "selected_threshold_pct": selected_threshold,
                **holdout_metrics,
                "fixed_zero_ev_sample_count": fixed_zero_metrics["sample_count"],
                "fixed_zero_ev_expectancy": fixed_zero_metrics["expectancy"],
                "fixed_zero_ev_profit_factor": fixed_zero_metrics["profit_factor"],
                "probability_brier_score": prediction_diagnostics["probability_brier_score"],
                "expected_value_return_spearman": prediction_diagnostics["expected_value_return_spearman"],
                "long_sample_count": side_metrics["LONG"]["sample_count"],
                "long_expectancy": side_metrics["LONG"]["expectancy"],
                "short_sample_count": side_metrics["SHORT"]["sample_count"],
                "short_expectancy": side_metrics["SHORT"]["expectancy"],
                "positive_holdout_quarters": temporal["positive_quarters"],
                "maximum_single_quarter_profit_share": temporal[
                    "maximum_single_quarter_profit_share"
                ],
                "walk_forward_pass_rate": round(wf_pass_rate, 6),
                "promotion_blockers": "; ".join(promotion_blockers),
            }
        )
        if is_promotable:
            promotable.append(variant_result)

        prediction_export = holdout[
            [
                column
                for column in (
                    "run_id",
                    "decision_id",
                    "_event_time",
                    "symbol",
                    "timeframe",
                    "side",
                    "score",
                    "evaluated_return",
                )
                if column in holdout.columns
            ]
        ].copy()
        prediction_export = prediction_export.join(
            holdout_predictions.drop(columns=["side"], errors="ignore")
        )
        threshold_value = np.nan if selected_threshold is None else float(selected_threshold)
        prediction_export["selected_threshold_pct"] = pd.Series(
            threshold_value, index=prediction_export.index, dtype=float
        )
        prediction_export["shadow_selected"] = holdout_mask.astype(bool)
        prediction_parts.append(prediction_export)

    if promotable:
        promotable.sort(
            key=lambda item: (
                float(item["holdout"]["expectancy"]),
                float(item["holdout"]["profit_factor"]),
                int(item["holdout"]["sample_count"]),
            ),
            reverse=True,
        )
        best = promotable[0]
        result.status = "PASS_RESEARCH_ONLY"
        result.recommended_variant = best["variant"]
        result.recommended_threshold_pct = best["selected_threshold_pct"]
        result.key_findings.append(
            f"{best['variant']} passed research promotion criteria, but remains shadow-only."
        )
    else:
        result.status = "FAIL"
        result.blockers.append(
            "No challenger preserved positive, sufficiently sampled, temporally stable edge on untouched Holdout."
        )
        result.key_findings.append(
            "No challenger is eligible to replace the Champion; runtime weights and Paper/Live settings remain unchanged."
        )

    summary = pd.DataFrame(summary_rows)
    candidates = pd.concat(candidate_parts, ignore_index=True) if candidate_parts else pd.DataFrame()
    walk_forward = (
        pd.concat(walk_forward_parts, ignore_index=True) if walk_forward_parts else pd.DataFrame()
    )
    holdout_predictions = (
        pd.concat(prediction_parts, ignore_index=True) if prediction_parts else pd.DataFrame()
    )

    if not summary.empty:
        better = summary[
            summary["expectancy"].gt(float(champion_metrics["expectancy"]))
            & summary["sample_count"].ge(config.minimum_holdout_selected)
        ]
        if not better.empty:
            result.key_findings.append(
                "Some challengers were less negative or better than the Champion, but improvement alone is not promotion evidence."
            )
        positive = summary[
            summary["expectancy"].gt(0) & summary["profit_factor"].ge(1.0)
        ]
        if positive.empty:
            result.key_findings.append(
                "No Optimize-selected challenger produced positive Holdout expectancy with profit factor >= 1."
            )
        fixed_positive = summary[
            summary["fixed_zero_ev_sample_count"].ge(config.minimum_holdout_selected)
            & summary["fixed_zero_ev_expectancy"].gt(0)
            & summary["fixed_zero_ev_profit_factor"].ge(1.0)
        ]
        if fixed_positive.empty:
            result.key_findings.append(
                "Even the fixed EV>=0 diagnostic remained non-positive across all adequately sampled challengers."
            )
        long_only = summary[summary["variant"].isin(["EXPECTANCY_LONG_ONLY", "EXPECTANCY_SHORT_DISABLED"])]
        if not long_only.empty and (long_only["expectancy"] > 0).any():
            result.key_findings.append(
                "Disabling SHORT improved the challenger in Holdout, but all stability criteria still apply."
            )

    result.key_findings.append(
        "Expected value includes side-specific win probability, predicted win/loss magnitude, execution buffer, and explicit risk-cost haircut."
    )
    result.key_findings.append(
        "Structure is used as a gate in designated variants; Volume remains a confirmation gate; Momentum is capped or removed."
    )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "champion_challenger_summary.csv"
    candidates_path = output / "challenger_threshold_candidates.csv"
    walk_forward_path = output / "challenger_walk_forward.csv"
    predictions_path = output / "challenger_holdout_shadow_predictions.csv"
    report_path = output / "champion_challenger_report.json"
    markdown_path = output / "champion_challenger_report.md"

    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    candidates.to_csv(candidates_path, index=False, encoding="utf-8-sig")
    walk_forward.to_csv(walk_forward_path, index=False, encoding="utf-8-sig")
    holdout_predictions.to_csv(predictions_path, index=False, encoding="utf-8-sig")
    result.output_files = {
        "summary_csv": str(summary_path),
        "threshold_candidates_csv": str(candidates_path),
        "walk_forward_csv": str(walk_forward_path),
        "holdout_shadow_predictions_csv": str(predictions_path),
        "report_json": str(report_path),
        "report_markdown": str(markdown_path),
    }
    report_path.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_path.write_text(_markdown_report(result, summary), encoding="utf-8")
    return result, ChampionChallengerArtifacts(summary, candidates, walk_forward, holdout_predictions)


def _markdown_report(result: ChampionChallengerResult, summary: pd.DataFrame) -> str:
    lines = [
        "# Freakto Expectancy-Aware Champion–Challenger Report",
        "",
        f"- Status: **{result.status}**",
        f"- Mode: **{result.mode}**",
        f"- Selected replay run: `{result.selected_run_id}`",
        f"- Rows usable: **{result.rows_usable:,}**",
        f"- Recommended variant: `{result.recommended_variant}`",
        f"- Recommended threshold: `{result.recommended_threshold_pct}`",
        f"- Promotion applied: **{result.promotion_applied}**",
        f"- Paper/Live enabled: **{result.paper_live_enabled}**",
        "",
        "## Champion Holdout",
        "",
        f"- Samples: {result.champion_holdout.get('sample_count', 0)}",
        f"- Expectancy: {result.champion_holdout.get('expectancy', 0)}%",
        f"- Profit factor: {result.champion_holdout.get('profit_factor', 0)}",
        f"- Max drawdown: {result.champion_holdout.get('max_drawdown', 0)}%",
        "",
        "## Challenger Summary",
        "",
    ]
    if summary.empty:
        lines.append("No challenger result was available.")
    else:
        columns = [
            "variant",
            "status",
            "sample_count",
            "expectancy",
            "profit_factor",
            "fixed_zero_ev_sample_count",
            "fixed_zero_ev_expectancy",
            "fixed_zero_ev_profit_factor",
            "max_drawdown",
            "walk_forward_pass_rate",
            "promotable",
        ]
        header = "| " + " | ".join(columns) + " |"
        separator = "| " + " | ".join(["---"] * len(columns)) + " |"
        lines.extend([header, separator])
        for _, row in summary[columns].iterrows():
            values = [str(row[column]) for column in columns]
            lines.append("| " + " | ".join(values) + " |")
    lines.extend(["", "## Key Findings", ""])
    lines.extend([f"- {item}" for item in result.key_findings])
    if result.blockers:
        lines.extend(["", "## Blockers", ""])
        lines.extend([f"- {item}" for item in result.blockers])
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "This report is research-only. It does not replace the runtime Champion, alter score weights, enable Paper/Live trading, or place orders.",
            "",
        ]
    )
    return "\n".join(lines)
