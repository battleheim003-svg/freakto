"""Chronological score-component ablation for Freakto replay decisions.

Ablation here means recomputing the already-recorded total score with one
component removed, then comparing selection quality. It does not fabricate new
features, retrain the decision engine, or change runtime weights.

Thresholds are selected on the optimization slice and evaluated once on the
untouched holdout slice. A fixed score>=70 holdout comparison is also reported
because it isolates how each component changes the current gate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from .score_attribution import COMPONENT_LABELS, DEFAULT_COMPONENTS
from .threshold_optimizer import selection_metrics

VERSION = "v10.6.0"
DEFAULT_OUTPUT_DIR = Path("logs/score_attribution")


@dataclass(frozen=True)
class AblationConfig:
    train_ratio: float = 0.60
    optimize_ratio: float = 0.20
    purge_rows: int = 6
    baseline_threshold: int = 70
    threshold_grid: tuple[int, ...] = tuple(range(50, 91, 5))
    minimum_total_rows: int = 300
    minimum_scope_rows: int = 100
    minimum_optimize_selected: int = 30
    minimum_holdout_selected: int = 20
    minimum_profit_factor: float = 1.0
    effect_tolerance_pct: float = 0.05

    def validate(self) -> None:
        if self.train_ratio <= 0 or self.optimize_ratio <= 0:
            raise ValueError("train_ratio and optimize_ratio must be positive.")
        if self.train_ratio + self.optimize_ratio >= 1:
            raise ValueError("train_ratio + optimize_ratio must be below 1.")
        if self.purge_rows < 0:
            raise ValueError("purge_rows cannot be negative.")
        if not self.threshold_grid:
            raise ValueError("threshold_grid cannot be empty.")
        if self.minimum_optimize_selected <= 0 or self.minimum_holdout_selected <= 0:
            raise ValueError("minimum selected rows must be positive.")


@dataclass
class AblationResult:
    created_utc: str
    version: str
    status: str
    rows_usable: int
    components: list[str]
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    output_files: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AblationArtifacts:
    summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    threshold_candidates: pd.DataFrame = field(default_factory=pd.DataFrame)


def chronological_three_way_split(
    frame: pd.DataFrame,
    config: AblationConfig = AblationConfig(),
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    config.validate()
    n = len(frame)
    if n < config.minimum_total_rows:
        raise ValueError(f"At least {config.minimum_total_rows} rows are required; found {n}.")
    train_boundary = int(n * config.train_ratio)
    optimize_boundary = int(n * (config.train_ratio + config.optimize_ratio))
    purge = int(config.purge_rows)
    train = frame.iloc[: max(0, train_boundary - purge)].copy()
    optimize = frame.iloc[train_boundary : max(train_boundary, optimize_boundary - purge)].copy()
    holdout = frame.iloc[optimize_boundary:].copy()
    if min(len(train), len(optimize), len(holdout)) < 30:
        raise ValueError("Train, optimize, and holdout must each contain at least 30 rows.")
    return train, optimize, holdout


def ablated_score(frame: pd.DataFrame, component: Optional[str]) -> pd.Series:
    score = pd.to_numeric(frame["score"], errors="coerce")
    if component is None:
        return score.clip(lower=0, upper=100)
    if component not in frame.columns:
        raise ValueError(f"Component column not found: {component}")
    points = pd.to_numeric(frame[component], errors="coerce").fillna(0.0)
    return (score - points).clip(lower=0, upper=100)


def _scope_frames(frame: pd.DataFrame, minimum_rows: int) -> list[tuple[str, pd.DataFrame]]:
    scopes: list[tuple[str, pd.DataFrame]] = [("ALL", frame)]
    for side in ("LONG", "SHORT"):
        subset = frame[frame["side"].eq(side)]
        if len(subset) >= minimum_rows:
            scopes.append((f"SIDE:{side}", subset))
    if "_regime_group" in frame.columns:
        for regime in ("BULL", "BEAR", "SIDEWAYS", "VOLATILE", "QUIET"):
            subset = frame[frame["_regime_group"].eq(regime)]
            if len(subset) >= minimum_rows:
                scopes.append((f"REGIME:{regime}", subset))
    return scopes


def _rank_correlation(score: pd.Series, returns: pd.Series) -> float:
    left = pd.to_numeric(score, errors="coerce")
    right = pd.to_numeric(returns, errors="coerce")
    pair = pd.concat([left, right], axis=1).dropna()
    if len(pair) < 3 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return 0.0
    value = pair.iloc[:, 0].corr(pair.iloc[:, 1], method="spearman")
    return 0.0 if pd.isna(value) else float(value)


def _candidate_objective(metrics: dict) -> float:
    if metrics["sample_count"] <= 0:
        return float("-inf")
    pf_term = math.log1p(min(float(metrics["profit_factor"]), 5.0))
    reliability = min(1.0, float(metrics["sample_count"]) / 150.0)
    return (
        float(metrics["expectancy"]) * 3.0
        + (float(metrics["win_rate"]) - 0.5) * 2.0
        + pf_term * 0.20
        + reliability * 0.10
        - abs(min(float(metrics["max_drawdown"]), 0.0)) * 0.01
    )


def _select_threshold(
    optimize: pd.DataFrame,
    score_column: str,
    config: AblationConfig,
    *,
    scope: str,
    variant: str,
) -> tuple[Optional[int], list[dict]]:
    rows: list[dict] = []
    best_threshold: Optional[int] = None
    best_key: Optional[tuple[float, int, float]] = None
    for threshold in config.threshold_grid:
        selected = optimize[pd.to_numeric(optimize[score_column], errors="coerce").ge(threshold)]
        metrics = selection_metrics(selected["evaluated_return"]).to_dict()
        viable = (
            metrics["sample_count"] >= config.minimum_optimize_selected
            and metrics["expectancy"] > 0
            and metrics["profit_factor"] >= config.minimum_profit_factor
        )
        objective = _candidate_objective(metrics) if viable else float("-inf")
        row = {
            "scope": scope,
            "variant": variant,
            "threshold": int(threshold),
            **metrics,
            "viable": bool(viable),
            "objective": objective,
        }
        rows.append(row)
        key = (objective, int(metrics["sample_count"]), float(metrics["expectancy"]))
        if viable and (best_key is None or key > best_key):
            best_key = key
            best_threshold = int(threshold)
    return best_threshold, rows


def _metrics_for_threshold(frame: pd.DataFrame, score_column: str, threshold: Optional[int]) -> dict:
    if threshold is None:
        return selection_metrics(pd.Series(dtype=float)).to_dict()
    selected = frame[pd.to_numeric(frame[score_column], errors="coerce").ge(threshold)]
    return selection_metrics(selected["evaluated_return"]).to_dict()


def _top_decile_expectancy(score: pd.Series, returns: pd.Series) -> tuple[int, float]:
    numeric = pd.to_numeric(score, errors="coerce")
    if numeric.notna().sum() < 10:
        return 0, 0.0
    threshold = float(numeric.quantile(0.90))
    selected = pd.to_numeric(returns[numeric.ge(threshold)], errors="coerce").dropna()
    return int(len(selected)), round(float(selected.mean()), 6) if len(selected) else 0.0


def run_component_ablation(
    frame: pd.DataFrame,
    *,
    components: Sequence[str] = DEFAULT_COMPONENTS,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    config: AblationConfig = AblationConfig(),
) -> tuple[AblationResult, AblationArtifacts]:
    config.validate()
    result = AblationResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        version=VERSION,
        status="COMPLETE",
        rows_usable=int(len(frame)),
        components=[component for component in components if component in frame.columns],
    )
    if len(frame) < config.minimum_total_rows:
        result.status = "INSUFFICIENT_DATA"
        result.blockers.append(
            f"At least {config.minimum_total_rows} usable rows are required; found {len(frame)}."
        )
        return result, AblationArtifacts()

    summary_rows: list[dict] = []
    candidate_rows: list[dict] = []
    variants: list[tuple[str, Optional[str]]] = [("FULL", None)] + [
        (f"WITHOUT_{component.upper()}", component) for component in result.components
    ]

    for scope_name, scope in _scope_frames(frame, max(config.minimum_scope_rows, config.minimum_total_rows)):
        train, optimize, holdout = chronological_three_way_split(scope, config)
        variant_rows: list[dict] = []
        for variant, component in variants:
            train = train.copy()
            optimize = optimize.copy()
            holdout = holdout.copy()
            train["_variant_score"] = ablated_score(train, component)
            optimize["_variant_score"] = ablated_score(optimize, component)
            holdout["_variant_score"] = ablated_score(holdout, component)

            selected_threshold, candidates = _select_threshold(
                optimize,
                "_variant_score",
                config,
                scope=scope_name,
                variant=variant,
            )
            candidate_rows.extend(candidates)
            fixed = _metrics_for_threshold(holdout, "_variant_score", config.baseline_threshold)
            optimized = _metrics_for_threshold(holdout, "_variant_score", selected_threshold)
            top_count, top_expectancy = _top_decile_expectancy(
                holdout["_variant_score"], holdout["evaluated_return"]
            )
            active = component is None or (
                pd.to_numeric(scope[component], errors="coerce").nunique(dropna=True) > 1
                and pd.to_numeric(scope[component], errors="coerce").abs().sum() > 0
            )
            row = {
                "scope": scope_name,
                "variant": variant,
                "removed_component": component or "",
                "component_label": COMPONENT_LABELS.get(component, component) if component else "Full Model",
                "component_active": bool(active),
                "selected_threshold": selected_threshold,
                "threshold_selected_on_optimize": selected_threshold is not None,
                "holdout_rank_correlation": round(
                    _rank_correlation(holdout["_variant_score"], holdout["evaluated_return"]), 6
                ),
                "top_decile_count": top_count,
                "top_decile_expectancy": top_expectancy,
            }
            row.update({f"fixed_{key}": value for key, value in fixed.items()})
            row.update({f"optimized_{key}": value for key, value in optimized.items()})
            variant_rows.append(row)

        full = next(item for item in variant_rows if item["variant"] == "FULL")
        for row in variant_rows:
            row["delta_fixed_expectancy_vs_full"] = round(
                float(row["fixed_expectancy"]) - float(full["fixed_expectancy"]), 6
            )
            row["delta_fixed_profit_factor_vs_full"] = round(
                float(row["fixed_profit_factor"]) - float(full["fixed_profit_factor"]), 6
            )
            row["delta_fixed_sample_count_vs_full"] = int(row["fixed_sample_count"]) - int(
                full["fixed_sample_count"]
            )
            if row["variant"] == "FULL":
                diagnosis = "BASELINE"
            elif not row["component_active"]:
                diagnosis = "INACTIVE"
            elif row["fixed_sample_count"] < config.minimum_holdout_selected:
                diagnosis = "INSUFFICIENT_HOLDOUT_SELECTION"
            elif row["delta_fixed_expectancy_vs_full"] > config.effect_tolerance_pct:
                if row["fixed_expectancy"] > 0 and row["fixed_profit_factor"] >= 1.0:
                    diagnosis = "REMOVAL_RESTORES_EDGE"
                else:
                    diagnosis = "REMOVAL_IMPROVES_BUT_NEGATIVE"
            elif row["delta_fixed_expectancy_vs_full"] < -config.effect_tolerance_pct:
                diagnosis = "REMOVAL_HURTS"
            else:
                diagnosis = "NEUTRAL_OR_MIXED"
            row["diagnosis"] = diagnosis
            summary_rows.append(row)

    summary = pd.DataFrame(summary_rows)
    candidates = pd.DataFrame(candidate_rows)
    overall = summary[summary["scope"].eq("ALL")]
    restores = overall[overall["diagnosis"].eq("REMOVAL_RESTORES_EDGE")]
    improves_negative = overall[overall["diagnosis"].eq("REMOVAL_IMPROVES_BUT_NEGATIVE")]
    hurts = overall[overall["diagnosis"].eq("REMOVAL_HURTS")]
    if not restores.empty:
        labels = ", ".join(restores["component_label"].astype(str).tolist())
        result.key_findings.append(f"Removing these components restored positive fixed-gate holdout edge: {labels}.")
    if not improves_negative.empty:
        labels = ", ".join(improves_negative["component_label"].astype(str).tolist())
        result.key_findings.append(
            f"Removing these components made fixed-gate holdout expectancy less negative, but did not restore edge: {labels}."
        )
    if not hurts.empty:
        labels = ", ".join(hurts["component_label"].astype(str).tolist())
        result.key_findings.append(f"Removing these components reduced fixed-gate holdout expectancy: {labels}.")
    full_overall = overall[overall["variant"].eq("FULL")]
    if not full_overall.empty:
        full_row = full_overall.iloc[0]
        if pd.notna(full_row["selected_threshold"]) and float(full_row["optimized_expectancy"]) <= 0:
            result.key_findings.append(
                "The full-score threshold selected on Optimize failed on untouched Holdout, confirming temporal instability."
            )
    if overall["selected_threshold"].notna().sum() == 0:
        result.key_findings.append(
            "No full/ablated variant found a positive optimization threshold; score composition alone did not restore edge."
        )
    result.key_findings.append(
        "Ablation findings are diagnostic only; runtime weights remain unchanged until a new walk-forward replay validates them."
    )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "component_ablation_summary.csv"
    candidates_path = output / "component_ablation_threshold_candidates.csv"
    report_path = output / "component_ablation_report.json"
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    candidates.to_csv(candidates_path, index=False, encoding="utf-8-sig")
    result.output_files = {
        "summary": str(summary_path),
        "threshold_candidates": str(candidates_path),
        "report": str(report_path),
    }
    report_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result, AblationArtifacts(summary=summary, threshold_candidates=candidates)
