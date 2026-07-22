"""Leakage-resistant side/regime segmented calibration research.

The global calibration validator can fail even when a narrow, pre-defined market
context contains useful edge.  This module evaluates that hypothesis without
loosening the safety contract:

* one common chronological Train -> Optimize -> Holdout boundary is used;
* segment definitions use only decision-time labels (side and regime);
* calibration is fitted on Train only;
* thresholds are selected on Optimize only;
* Holdout is evaluated once and never used to choose a policy;
* expanding walk-forward checks run only inside the development period;
* sparse, unknown, unstable, or statistically weak segments fail closed.

The module is research-only and does not alter Paper or Live settings.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
from typing import Iterable, Optional

import pandas as pd

from .calibration_validation import (
    DEFAULT_DATASET,
    ValidationConfig,
    apply_calibration_table,
    build_calibration_table,
    calibration_metrics,
    chronological_three_way_split,
    load_validation_dataset,
)
from .segmented_threshold_optimizer import (
    SegmentedThresholdSearchConfig,
    evaluate_segment_policy,
    optimize_segment_thresholds,
)
from .threshold_optimizer import EdgeGatePolicyCandidate, apply_policy, selection_metrics

VERSION = "v10.5.0"
DEFAULT_OUTPUT_DIR = Path("logs/segmented_calibration_validation")
DEFAULT_RUNTIME_MAPPING = Path("logs/calibration/segmented_score_calibration.csv")
DEFAULT_RUNTIME_POLICY = Path("logs/calibration/segmented_edge_gate_policy.json")

REGIME_ORDER = ("BULL", "BEAR", "SIDEWAYS", "VOLATILE", "QUIET", "UNKNOWN")
LEVEL_PRECEDENCE = {"SIDE_REGIME": 0, "SIDE": 1, "REGIME": 2}


@dataclass(frozen=True)
class SegmentDefinition:
    segment_id: str
    level: str
    side: Optional[str] = None
    regime: Optional[str] = None
    promotion_eligible: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SegmentedCalibrationConfig:
    train_ratio: float = 0.60
    optimize_ratio: float = 0.20
    purge_rows: int = 6
    bucket_width: int = 10
    prior_strength: float = 20.0
    minimum_total_rows: int = 300
    baseline_score_threshold: int = 70

    minimum_train_rows: int = 120
    minimum_optimize_rows: int = 40
    minimum_holdout_rows: int = 40
    minimum_selected_holdout: int = 20
    strong_selected_holdout: int = 30

    minimum_holdout_expectancy: float = 0.0
    minimum_holdout_profit_factor: float = 1.05
    strong_holdout_profit_factor: float = 1.10
    max_brier_score: float = 0.30
    max_ece: float = 0.20
    confidence_z: float = 1.96
    minimum_break_even_wins: int = 20
    minimum_break_even_losses: int = 20
    break_even_floor: float = 0.25
    break_even_ceiling: float = 0.75

    walk_forward_folds: int = 3
    minimum_walk_forward_folds: int = 2
    minimum_walk_forward_pass_rate: float = 2.0 / 3.0
    minimum_walk_forward_train_rows: int = 80
    minimum_walk_forward_optimize_rows: int = 20
    minimum_walk_forward_test_rows: int = 20

    include_side_segments: bool = True
    include_regime_segments: bool = True
    include_side_regime_segments: bool = True
    include_unknown_regime_diagnostics: bool = True

    search: SegmentedThresholdSearchConfig = field(default_factory=SegmentedThresholdSearchConfig)

    def base_validation_config(self) -> ValidationConfig:
        return ValidationConfig(
            train_ratio=self.train_ratio,
            optimize_ratio=self.optimize_ratio,
            purge_rows=self.purge_rows,
            bucket_width=self.bucket_width,
            prior_strength=self.prior_strength,
            minimum_total_rows=self.minimum_total_rows,
            baseline_score_threshold=self.baseline_score_threshold,
            minimum_selected=self.search.minimum_selected,
        )

    def validate(self) -> None:
        self.search.validate()
        if self.minimum_train_rows <= 0:
            raise ValueError("minimum_train_rows must be positive.")
        if self.minimum_optimize_rows <= 0 or self.minimum_holdout_rows <= 0:
            raise ValueError("minimum split rows must be positive.")
        if self.minimum_selected_holdout <= 0:
            raise ValueError("minimum_selected_holdout must be positive.")
        if self.walk_forward_folds <= 0:
            raise ValueError("walk_forward_folds must be positive.")
        if self.minimum_walk_forward_folds <= 0:
            raise ValueError("minimum_walk_forward_folds must be positive.")
        if not 0.0 <= self.minimum_walk_forward_pass_rate <= 1.0:
            raise ValueError("minimum_walk_forward_pass_rate must be between 0 and 1.")
        if self.max_brier_score <= 0 or self.max_ece <= 0:
            raise ValueError("calibration error limits must be positive.")
        if not 0.0 < self.break_even_floor < self.break_even_ceiling < 1.0:
            raise ValueError("break-even bounds must satisfy 0 < floor < ceiling < 1.")


@dataclass
class SegmentValidationResult:
    segment: SegmentDefinition
    status: str
    split_rows: dict = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    selected_policy: Optional[dict] = None
    baseline_holdout: dict = field(default_factory=dict)
    optimized_holdout: dict = field(default_factory=dict)
    expectancy_confidence_interval: dict = field(default_factory=dict)
    calibration_metrics: dict = field(default_factory=dict)
    economics: dict = field(default_factory=dict)
    walk_forward: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["segment"] = self.segment.to_dict()
        return payload


@dataclass
class SegmentedCalibrationValidationResult:
    created_utc: str
    version: str
    status: str
    dataset_path: str
    dataset_sha256: str
    rows_loaded: int
    rows_usable: int
    splits: list[dict] = field(default_factory=list)
    segment_results: list[SegmentValidationResult] = field(default_factory=list)
    recommended_policies: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    output_files: dict = field(default_factory=dict)
    promoted: bool = False

    def to_dict(self) -> dict:
        return {
            "created_utc": self.created_utc,
            "version": self.version,
            "status": self.status,
            "dataset_path": self.dataset_path,
            "dataset_sha256": self.dataset_sha256,
            "rows_loaded": self.rows_loaded,
            "rows_usable": self.rows_usable,
            "splits": self.splits,
            "segment_results": [item.to_dict() for item in self.segment_results],
            "recommended_policies": self.recommended_policies,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "output_files": self.output_files,
            "promoted": self.promoted,
        }


@dataclass
class _SegmentArtifacts:
    training_mapping: pd.DataFrame = field(default_factory=pd.DataFrame)
    final_mapping: pd.DataFrame = field(default_factory=pd.DataFrame)
    candidates: pd.DataFrame = field(default_factory=pd.DataFrame)
    holdout_scored: pd.DataFrame = field(default_factory=pd.DataFrame)
    walk_forward_rows: pd.DataFrame = field(default_factory=pd.DataFrame)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_regime_label(value: object) -> str:
    """Map heterogeneous decision-time regime labels to stable research groups."""

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


def prepare_segment_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "side" not in result.columns:
        result["side"] = "UNKNOWN"
    result["_segment_side"] = result["side"].astype(str).str.strip().str.upper()
    if "regime_label" in result.columns:
        result["_segment_regime"] = result["regime_label"].map(normalize_regime_label)
    elif "regime" in result.columns:
        result["_segment_regime"] = result["regime"].map(normalize_regime_label)
    else:
        result["_segment_regime"] = "UNKNOWN"
    return result


def build_segment_definitions(
    training_frame: pd.DataFrame,
    config: SegmentedCalibrationConfig = SegmentedCalibrationConfig(),
) -> list[SegmentDefinition]:
    """Create only pre-defined label segments; outcome columns are never inspected."""

    frame = prepare_segment_columns(training_frame)
    definitions: list[SegmentDefinition] = []
    present_sides = [side for side in ("LONG", "SHORT") if frame["_segment_side"].eq(side).any()]
    present_regimes = [regime for regime in REGIME_ORDER if frame["_segment_regime"].eq(regime).any()]

    if config.include_side_segments:
        for side in present_sides:
            definitions.append(SegmentDefinition(f"SIDE:{side}", "SIDE", side=side))

    if config.include_regime_segments:
        for regime in present_regimes:
            if regime == "UNKNOWN" and not config.include_unknown_regime_diagnostics:
                continue
            definitions.append(
                SegmentDefinition(
                    f"REGIME:{regime}",
                    "REGIME",
                    regime=regime,
                    promotion_eligible=regime != "UNKNOWN",
                )
            )

    if config.include_side_regime_segments:
        for side in present_sides:
            for regime in present_regimes:
                if regime == "UNKNOWN" and not config.include_unknown_regime_diagnostics:
                    continue
                mask = frame["_segment_side"].eq(side) & frame["_segment_regime"].eq(regime)
                if not mask.any():
                    continue
                definitions.append(
                    SegmentDefinition(
                        f"SIDE_REGIME:{side}|{regime}",
                        "SIDE_REGIME",
                        side=side,
                        regime=regime,
                        promotion_eligible=regime != "UNKNOWN",
                    )
                )

    return sorted(
        definitions,
        key=lambda item: (
            LEVEL_PRECEDENCE.get(item.level, 99),
            item.side or "",
            REGIME_ORDER.index(item.regime) if item.regime in REGIME_ORDER else 99,
            item.segment_id,
        ),
    )


def segment_mask(frame: pd.DataFrame, segment: SegmentDefinition) -> pd.Series:
    prepared = prepare_segment_columns(frame)
    mask = pd.Series(True, index=prepared.index, dtype=bool)
    if segment.side is not None:
        mask &= prepared["_segment_side"].eq(segment.side)
    if segment.regime is not None:
        mask &= prepared["_segment_regime"].eq(segment.regime)
    return mask


def filter_segment(frame: pd.DataFrame, segment: SegmentDefinition) -> pd.DataFrame:
    prepared = prepare_segment_columns(frame)
    return prepared.loc[segment_mask(prepared, segment)].copy()


def expectancy_confidence_interval(
    returns: Iterable[float],
    *,
    z_value: float = 1.96,
) -> dict:
    clean = pd.to_numeric(pd.Series(list(returns), dtype="float64"), errors="coerce").dropna()
    if clean.empty:
        return {"sample_count": 0, "mean": 0.0, "standard_error": None, "lower": None, "upper": None}
    mean = float(clean.mean())
    if len(clean) < 2:
        return {
            "sample_count": int(len(clean)),
            "mean": round(mean, 6),
            "standard_error": None,
            "lower": None,
            "upper": None,
        }
    standard_error = float(clean.std(ddof=1) / math.sqrt(len(clean)))
    margin = float(z_value) * standard_error
    return {
        "sample_count": int(len(clean)),
        "mean": round(mean, 6),
        "standard_error": round(standard_error, 6),
        "lower": round(mean - margin, 6),
        "upper": round(mean + margin, 6),
    }


def estimate_empirical_break_even(
    returns: Iterable[float],
    *,
    minimum_wins: int = 20,
    minimum_losses: int = 20,
    floor: float = 0.25,
    ceiling: float = 0.75,
    fallback: float = 0.50,
) -> dict:
    """Estimate probability break-even from Train payoff asymmetry only."""

    clean = pd.to_numeric(pd.Series(list(returns), dtype="float64"), errors="coerce").dropna()
    wins = clean[clean > 0]
    losses = -clean[clean < 0]
    if len(wins) < minimum_wins or len(losses) < minimum_losses:
        return {
            "status": "FALLBACK",
            "probability": round(float(fallback), 6),
            "win_count": int(len(wins)),
            "loss_count": int(len(losses)),
            "avg_win": round(float(wins.mean()), 6) if len(wins) else None,
            "avg_loss": round(float(losses.mean()), 6) if len(losses) else None,
            "reason": "Insufficient Train wins/losses for payoff-aware break-even estimation.",
        }
    avg_win = float(wins.mean())
    avg_loss = float(losses.mean())
    denominator = avg_win + avg_loss
    if denominator <= 0:
        probability = float(fallback)
        status = "FALLBACK"
        reason = "Invalid Train payoff denominator."
    else:
        probability = avg_loss / denominator
        probability = max(float(floor), min(float(ceiling), probability))
        status = "READY"
        reason = "Estimated from Train average win/loss asymmetry."
    return {
        "status": status,
        "probability": round(probability, 6),
        "win_count": int(len(wins)),
        "loss_count": int(len(losses)),
        "avg_win": round(avg_win, 6),
        "avg_loss": round(avg_loss, 6),
        "reason": reason,
    }


def _empty_metrics() -> dict:
    return selection_metrics(pd.Series(dtype="float64")).to_dict()


def _walk_forward_boundaries(
    row_count: int,
    *,
    folds: int,
) -> list[tuple[int, int, int, int]]:
    """Return expanding train and non-overlapping optimize/test blocks."""

    total_units = 2 + 2 * int(folds)
    if row_count < total_units:
        return []
    unit = row_count // total_units
    if unit <= 0:
        return []
    boundaries: list[tuple[int, int, int, int]] = []
    for fold_index in range(int(folds)):
        train_end = (2 + 2 * fold_index) * unit
        optimize_end = train_end + unit
        test_end = row_count if fold_index == folds - 1 else optimize_end + unit
        boundaries.append((train_end, optimize_end, optimize_end, test_end))
    return boundaries


def _timestamp_value(frame: pd.DataFrame, position: str) -> Optional[str]:
    if frame.empty or "_event_time" not in frame.columns:
        return None
    values = frame["_event_time"].dropna()
    if values.empty:
        return None
    value = values.iloc[0] if position == "start" else values.iloc[-1]
    return str(value)


def walk_forward_segment_validation(
    development_frame: pd.DataFrame,
    *,
    segment: SegmentDefinition,
    config: SegmentedCalibrationConfig,
) -> tuple[dict, pd.DataFrame]:
    """Expanding walk-forward inside Train+Optimize only; final Holdout is untouched."""

    data = development_frame.sort_values(["_event_time", "_row_order"], kind="stable").reset_index(drop=True)
    boundaries = _walk_forward_boundaries(len(data), folds=config.walk_forward_folds)
    rows: list[dict] = []
    selected_returns: list[float] = []
    passed_folds = 0
    policy_folds = 0
    completed_folds = 0

    for fold_index, (train_end, optimize_end, test_start, test_end) in enumerate(boundaries, start=1):
        purge = max(0, int(config.purge_rows))
        train = data.iloc[: max(0, train_end - purge)].copy()
        optimize = data.iloc[train_end : max(train_end, optimize_end - purge)].copy()
        test = data.iloc[test_start:test_end].copy()

        if (
            len(train) < config.minimum_walk_forward_train_rows
            or len(optimize) < config.minimum_walk_forward_optimize_rows
            or len(test) < config.minimum_walk_forward_test_rows
        ):
            rows.append(
                {
                    "segment_id": segment.segment_id,
                    "fold": fold_index,
                    "status": "INSUFFICIENT_DATA",
                    "train_rows": len(train),
                    "optimize_rows": len(optimize),
                    "test_rows": len(test),
                    "train_end": _timestamp_value(train, "end"),
                    "optimize_start": _timestamp_value(optimize, "start"),
                    "optimize_end": _timestamp_value(optimize, "end"),
                    "test_start": _timestamp_value(test, "start"),
                    "test_end": _timestamp_value(test, "end"),
                }
            )
            continue

        completed_folds += 1
        table = build_calibration_table(
            train,
            bucket_width=config.bucket_width,
            prior_strength=config.prior_strength,
        )
        optimize_mapped = apply_calibration_table(optimize, table)
        test_mapped = apply_calibration_table(test, table)
        fold_economics = estimate_empirical_break_even(
            train["evaluated_return"].tolist(),
            minimum_wins=max(5, min(config.minimum_break_even_wins, len(train) // 10)),
            minimum_losses=max(5, min(config.minimum_break_even_losses, len(train) // 10)),
            floor=config.break_even_floor,
            ceiling=config.break_even_ceiling,
            fallback=config.search.break_even_probability,
        )
        fold_search = replace(
            config.search,
            break_even_probability=float(fold_economics["probability"]),
            minimum_selected=min(
                config.search.minimum_selected,
                max(5, config.minimum_walk_forward_optimize_rows),
            ),
            target_sample_count=min(config.search.target_sample_count, max(20, len(optimize))),
        )
        policy, _ = optimize_segment_thresholds(
            optimize_mapped,
            segment_id=f"{segment.segment_id}#WF{fold_index}",
            config=fold_search,
        )
        evaluation = evaluate_segment_policy(
            test_mapped,
            policy,
            segment_id=segment.segment_id,
            minimum_selected=max(5, min(config.minimum_selected_holdout, len(test))),
            minimum_expectancy=config.minimum_holdout_expectancy,
            minimum_profit_factor=1.0,
        )
        if policy is not None:
            policy_folds += 1
            mask = apply_policy(test_mapped, policy)
            selected_returns.extend(
                pd.to_numeric(test_mapped.loc[mask, "evaluated_return"], errors="coerce").dropna().tolist()
            )
        fold_pass = bool(policy is not None and evaluation.viable)
        if fold_pass:
            passed_folds += 1

        rows.append(
            {
                "segment_id": segment.segment_id,
                "fold": fold_index,
                "status": "PASS" if fold_pass else ("NO_POLICY" if policy is None else "FAIL"),
                "train_rows": len(train),
                "optimize_rows": len(optimize),
                "test_rows": len(test),
                "train_end": _timestamp_value(train, "end"),
                "optimize_start": _timestamp_value(optimize, "start"),
                "optimize_end": _timestamp_value(optimize, "end"),
                "test_start": _timestamp_value(test, "start"),
                "test_end": _timestamp_value(test, "end"),
                "break_even_probability": fold_economics["probability"],
                "break_even_status": fold_economics["status"],
                "policy": json.dumps(policy.to_dict(), sort_keys=True) if policy is not None else None,
                **evaluation.to_dict(),
            }
        )

    aggregate = selection_metrics(pd.Series(selected_returns, dtype="float64")).to_dict()
    pass_rate = float(passed_folds / completed_folds) if completed_folds else 0.0
    stable = (
        completed_folds >= config.minimum_walk_forward_folds
        and pass_rate >= config.minimum_walk_forward_pass_rate
        and aggregate["sample_count"] >= config.minimum_selected_holdout
        and aggregate["expectancy"] > config.minimum_holdout_expectancy
        and aggregate["profit_factor"] >= 1.0
    )
    summary = {
        "requested_folds": config.walk_forward_folds,
        "completed_folds": completed_folds,
        "policy_folds": policy_folds,
        "passed_folds": passed_folds,
        "pass_rate": round(pass_rate, 6),
        "aggregate_metrics": aggregate,
        "stable": stable,
        "development_only": True,
    }
    return summary, pd.DataFrame(rows)


def _validate_one_segment(
    train: pd.DataFrame,
    optimize: pd.DataFrame,
    holdout: pd.DataFrame,
    full_frame: pd.DataFrame,
    *,
    segment: SegmentDefinition,
    config: SegmentedCalibrationConfig,
) -> tuple[SegmentValidationResult, _SegmentArtifacts]:
    train_segment = filter_segment(train, segment)
    optimize_segment = filter_segment(optimize, segment)
    holdout_segment = filter_segment(holdout, segment)
    full_segment = filter_segment(full_frame, segment)
    split_rows = {
        "train": len(train_segment),
        "optimize": len(optimize_segment),
        "holdout": len(holdout_segment),
        "total": len(full_segment),
    }
    result = SegmentValidationResult(segment=segment, status="RUNNING", split_rows=split_rows)
    artifacts = _SegmentArtifacts()

    if not segment.promotion_eligible:
        result.status = "INELIGIBLE"
        result.blockers.append("UNKNOWN regime segments are diagnostic-only and cannot be promoted.")
        return result, artifacts

    minimums = {
        "train": config.minimum_train_rows,
        "optimize": config.minimum_optimize_rows,
        "holdout": config.minimum_holdout_rows,
    }
    insufficient = [
        f"{name}={split_rows[name]}<{required}"
        for name, required in minimums.items()
        if split_rows[name] < required
    ]
    if insufficient:
        result.status = "INSUFFICIENT_DATA"
        result.blockers.append("Insufficient chronological segment support: " + ", ".join(insufficient))
        return result, artifacts

    training_mapping = build_calibration_table(
        train_segment,
        bucket_width=config.bucket_width,
        prior_strength=config.prior_strength,
    )
    optimize_mapped = apply_calibration_table(optimize_segment, training_mapping)
    holdout_mapped = apply_calibration_table(holdout_segment, training_mapping)
    economics = estimate_empirical_break_even(
        train_segment["evaluated_return"].tolist(),
        minimum_wins=config.minimum_break_even_wins,
        minimum_losses=config.minimum_break_even_losses,
        floor=config.break_even_floor,
        ceiling=config.break_even_ceiling,
        fallback=config.search.break_even_probability,
    )
    result.economics = economics
    segment_search = replace(
        config.search,
        break_even_probability=float(economics["probability"]),
    )
    policy, candidates = optimize_segment_thresholds(
        optimize_mapped,
        segment_id=segment.segment_id,
        config=segment_search,
    )

    result.selected_policy = policy.to_dict() if policy is not None else None
    baseline_mask = pd.to_numeric(holdout_mapped["score"], errors="coerce").ge(
        config.baseline_score_threshold
    )
    result.baseline_holdout = selection_metrics(
        holdout_mapped.loc[baseline_mask, "evaluated_return"]
    ).to_dict()

    if policy is None:
        optimized_mask = pd.Series(False, index=holdout_mapped.index, dtype=bool)
        result.optimized_holdout = _empty_metrics()
    else:
        optimized_mask = apply_policy(holdout_mapped, policy)
        result.optimized_holdout = selection_metrics(
            holdout_mapped.loc[optimized_mask, "evaluated_return"]
        ).to_dict()
    result.expectancy_confidence_interval = expectancy_confidence_interval(
        holdout_mapped.loc[optimized_mask, "evaluated_return"].tolist(),
        z_value=config.confidence_z,
    )
    calibration_summary, _ = calibration_metrics(holdout_mapped)
    result.calibration_metrics = calibration_summary

    development = pd.concat([train_segment, optimize_segment], axis=0).sort_values(
        ["_event_time", "_row_order"], kind="stable"
    )
    walk_summary, walk_rows = walk_forward_segment_validation(
        development,
        segment=segment,
        config=config,
    )
    result.walk_forward = walk_summary

    if policy is None:
        result.status = "FAIL"
        result.blockers.append("No positive threshold policy survived this segment's Optimize split.")
    else:
        metrics = result.optimized_holdout
        if metrics["sample_count"] < config.minimum_selected_holdout:
            result.blockers.append("Untouched Holdout selected too few decisions.")
        if metrics["expectancy"] <= config.minimum_holdout_expectancy:
            result.blockers.append("Untouched Holdout expectancy is not positive.")
        if metrics["profit_factor"] < config.minimum_holdout_profit_factor:
            result.blockers.append("Untouched Holdout profit factor is below the minimum.")
        brier = calibration_summary.get("brier_score")
        ece = calibration_summary.get("ece")
        if brier is None or brier > config.max_brier_score:
            result.blockers.append("Segment Holdout Brier score is too weak.")
        if ece is None or ece > config.max_ece:
            result.blockers.append("Segment Holdout ECE is too weak.")
        if not walk_summary.get("stable", False):
            result.blockers.append("Development-period walk-forward stability did not pass.")

        if result.blockers:
            result.status = "FAIL"
        else:
            lower = result.expectancy_confidence_interval.get("lower")
            strong = (
                metrics["sample_count"] >= config.strong_selected_holdout
                and metrics["profit_factor"] >= config.strong_holdout_profit_factor
                and lower is not None
                and lower > 0
            )
            if strong:
                result.status = "PASS"
            else:
                result.status = "PASS_WITH_WARNINGS"
                result.warnings.append(
                    "Positive segment edge passed operational checks, but its 95% expectancy lower bound "
                    "or strong-sample threshold is not positive enough for automatic promotion."
                )

    training_mapping = training_mapping.copy()
    training_mapping.insert(0, "segment_id", segment.segment_id)
    training_mapping.insert(1, "segment_level", segment.level)
    training_mapping.insert(2, "segment_side", segment.side)
    training_mapping.insert(3, "segment_regime", segment.regime)

    final_mapping = build_calibration_table(
        full_segment,
        bucket_width=config.bucket_width,
        prior_strength=config.prior_strength,
    )
    final_mapping.insert(0, "segment_id", segment.segment_id)
    final_mapping.insert(1, "segment_level", segment.level)
    final_mapping.insert(2, "segment_side", segment.side)
    final_mapping.insert(3, "segment_regime", segment.regime)

    holdout_scored = holdout_mapped.copy()
    holdout_scored.insert(0, "segment_id", segment.segment_id)
    holdout_scored.insert(1, "segment_level", segment.level)
    holdout_scored["policy_selected"] = optimized_mask.astype(bool)

    artifacts.training_mapping = training_mapping
    artifacts.final_mapping = final_mapping
    artifacts.candidates = candidates
    artifacts.holdout_scored = holdout_scored
    artifacts.walk_forward_rows = walk_rows
    return result, artifacts


def _policy_payload(
    result: SegmentedCalibrationValidationResult,
    *,
    status: str,
) -> dict:
    return {
        "schema_version": 1,
        "engine_version": VERSION,
        "status": status,
        "approved": status == "PROMOTED",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": result.dataset_sha256,
        "precedence": ["SIDE_REGIME", "SIDE", "REGIME"],
        "fail_closed": True,
        "policies": result.recommended_policies,
    }


def _summary_frame(results: list[SegmentValidationResult]) -> pd.DataFrame:
    rows: list[dict] = []
    for item in results:
        policy = item.selected_policy or {}
        holdout = item.optimized_holdout or _empty_metrics()
        baseline = item.baseline_holdout or _empty_metrics()
        calibration = item.calibration_metrics or {}
        walk = item.walk_forward or {}
        ci = item.expectancy_confidence_interval or {}
        economics = item.economics or {}
        rows.append(
            {
                **item.segment.to_dict(),
                "status": item.status,
                "train_rows": item.split_rows.get("train", 0),
                "optimize_rows": item.split_rows.get("optimize", 0),
                "holdout_rows": item.split_rows.get("holdout", 0),
                "policy_raw_score_threshold": policy.get("raw_score_threshold"),
                "policy_min_probability": policy.get("min_probability"),
                "policy_min_samples": policy.get("min_samples"),
                "policy_min_expected_edge": policy.get("min_expected_edge"),
                "train_break_even_probability": economics.get("probability"),
                "train_break_even_status": economics.get("status"),
                "train_avg_win": economics.get("avg_win"),
                "train_avg_loss": economics.get("avg_loss"),
                "baseline_samples": baseline.get("sample_count", 0),
                "baseline_expectancy": baseline.get("expectancy", 0.0),
                "holdout_samples": holdout.get("sample_count", 0),
                "holdout_win_rate": holdout.get("win_rate", 0.0),
                "holdout_expectancy": holdout.get("expectancy", 0.0),
                "holdout_profit_factor": holdout.get("profit_factor", 0.0),
                "holdout_max_drawdown": holdout.get("max_drawdown", 0.0),
                "expectancy_ci_lower": ci.get("lower"),
                "expectancy_ci_upper": ci.get("upper"),
                "brier_score": calibration.get("brier_score"),
                "ece": calibration.get("ece"),
                "walk_forward_completed_folds": walk.get("completed_folds", 0),
                "walk_forward_pass_rate": walk.get("pass_rate", 0.0),
                "walk_forward_stable": walk.get("stable", False),
                "blockers": " | ".join(item.blockers),
                "warnings": " | ".join(item.warnings),
            }
        )
    return pd.DataFrame(rows)


def run_segmented_calibration_validation(
    dataset_path: Path | str = DEFAULT_DATASET,
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    config: SegmentedCalibrationConfig = SegmentedCalibrationConfig(),
    promote: bool = False,
    runtime_mapping_path: Path | str = DEFAULT_RUNTIME_MAPPING,
    runtime_policy_path: Path | str = DEFAULT_RUNTIME_POLICY,
) -> SegmentedCalibrationValidationResult:
    config.validate()
    source = Path(dataset_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    loaded = pd.read_csv(source, encoding="utf-8-sig", low_memory=False)
    frame, warnings = load_validation_dataset(source)
    frame = prepare_segment_columns(frame)
    train, optimize, holdout, split_summaries = chronological_three_way_split(
        frame,
        config.base_validation_config(),
    )

    result = SegmentedCalibrationValidationResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        version=VERSION,
        status="RUNNING",
        dataset_path=str(source),
        dataset_sha256=_sha256(source),
        rows_loaded=len(loaded),
        rows_usable=len(frame),
        splits=[asdict(item) for item in split_summaries],
        warnings=warnings,
    )

    definitions = build_segment_definitions(train, config)
    if not definitions:
        result.status = "FAIL"
        result.blockers.append("No side/regime segment definitions were available in Train.")

    training_mappings: list[pd.DataFrame] = []
    final_mappings: list[pd.DataFrame] = []
    candidates: list[pd.DataFrame] = []
    holdout_scored: list[pd.DataFrame] = []
    walk_rows: list[pd.DataFrame] = []

    for segment in definitions:
        segment_result, artifacts = _validate_one_segment(
            train,
            optimize,
            holdout,
            frame,
            segment=segment,
            config=config,
        )
        result.segment_results.append(segment_result)
        if not artifacts.training_mapping.empty:
            training_mappings.append(artifacts.training_mapping)
        if not artifacts.final_mapping.empty:
            final_mappings.append(artifacts.final_mapping)
        if not artifacts.candidates.empty:
            candidates.append(artifacts.candidates)
        if not artifacts.holdout_scored.empty:
            holdout_scored.append(artifacts.holdout_scored)
        if not artifacts.walk_forward_rows.empty:
            walk_rows.append(artifacts.walk_forward_rows)

    robust = [item for item in result.segment_results if item.status == "PASS"]
    warning_candidates = [item for item in result.segment_results if item.status == "PASS_WITH_WARNINGS"]
    result.recommended_policies = [
        {
            "segment": item.segment.to_dict(),
            "validation_status": item.status,
            "policy": item.selected_policy,
            "holdout_metrics": item.optimized_holdout,
            "expectancy_confidence_interval": item.expectancy_confidence_interval,
            "calibration_metrics": item.calibration_metrics,
            "walk_forward": item.walk_forward,
        }
        for item in robust
    ]

    if robust:
        result.status = "PASS"
    else:
        result.status = "FAIL"
        if warning_candidates:
            result.blockers.append(
                "Some segments passed operational checks but none cleared the strong statistical promotion gate."
            )
        else:
            result.blockers.append(
                "No side/regime segment preserved positive, calibrated, walk-forward-stable edge on untouched Holdout."
            )

    summary_path = destination / "segment_summary.csv"
    training_mapping_path = destination / "segmented_score_calibration_train.csv"
    candidate_mapping_path = destination / "segmented_score_calibration_candidate.csv"
    candidates_path = destination / "segment_threshold_candidates.csv"
    holdout_path = destination / "segment_holdout_scored.csv"
    walk_path = destination / "segment_walk_forward_folds.csv"
    recommended_policy_path = destination / "recommended_segmented_edge_gate_policy.json"
    report_path = destination / "segmented_calibration_validation_report.json"

    _summary_frame(result.segment_results).to_csv(summary_path, index=False, encoding="utf-8-sig")
    pd.concat(training_mappings, ignore_index=True).to_csv(
        training_mapping_path, index=False, encoding="utf-8-sig"
    ) if training_mappings else pd.DataFrame().to_csv(training_mapping_path, index=False)
    pd.concat(final_mappings, ignore_index=True).to_csv(
        candidate_mapping_path, index=False, encoding="utf-8-sig"
    ) if final_mappings else pd.DataFrame().to_csv(candidate_mapping_path, index=False)
    pd.concat(candidates, ignore_index=True).to_csv(
        candidates_path, index=False, encoding="utf-8-sig"
    ) if candidates else pd.DataFrame().to_csv(candidates_path, index=False)
    pd.concat(holdout_scored, ignore_index=True).to_csv(
        holdout_path, index=False, encoding="utf-8-sig"
    ) if holdout_scored else pd.DataFrame().to_csv(holdout_path, index=False)
    pd.concat(walk_rows, ignore_index=True).to_csv(
        walk_path, index=False, encoding="utf-8-sig"
    ) if walk_rows else pd.DataFrame().to_csv(walk_path, index=False)

    policy_status = "RECOMMENDED" if robust else "NO_RECOMMENDATION"
    recommended_policy_path.write_text(
        json.dumps(_policy_payload(result, status=policy_status), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result.output_files = {
        "segment_summary": str(summary_path),
        "training_mapping": str(training_mapping_path),
        "candidate_mapping": str(candidate_mapping_path),
        "threshold_candidates": str(candidates_path),
        "holdout_scored": str(holdout_path),
        "walk_forward_folds": str(walk_path),
        "recommended_policy": str(recommended_policy_path),
        "report_json": str(report_path),
    }

    if promote:
        if result.status != "PASS" or not result.recommended_policies:
            result.warnings.append("Promotion requested but blocked because no segment has PASS status.")
        else:
            active_mapping = Path(runtime_mapping_path)
            active_policy = Path(runtime_policy_path)
            active_mapping.parent.mkdir(parents=True, exist_ok=True)
            active_policy.parent.mkdir(parents=True, exist_ok=True)
            robust_ids = {item.segment.segment_id for item in robust}
            final_frame = pd.concat(final_mappings, ignore_index=True)
            final_frame = final_frame[final_frame["segment_id"].isin(robust_ids)]
            final_frame.to_csv(active_mapping, index=False, encoding="utf-8-sig")
            active_policy.write_text(
                json.dumps(_policy_payload(result, status="PROMOTED"), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result.promoted = True
            result.output_files["active_mapping"] = str(active_mapping)
            result.output_files["active_policy"] = str(active_policy)

    report_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result
