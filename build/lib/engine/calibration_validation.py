"""Chronological calibration validation and edge-gate policy research.

This module implements a leakage-resistant three-way workflow:

1. Fit the score-to-probability mapping on the oldest training slice.
2. Select edge-gate thresholds on a later optimization slice.
3. Evaluate the selected policy once on the newest untouched holdout slice.

No target/outcome column is used as a model feature.  The only predictive input
is the decision score that existed at decision time.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
from typing import Iterable, Optional

import pandas as pd

from .threshold_optimizer import (
    EdgeGatePolicyCandidate,
    apply_policy,
    optimize_edge_thresholds,
    selection_metrics,
)

DEFAULT_DATASET = Path("logs/calibration_dataset/calibration_training.csv")
DEFAULT_OUTPUT_DIR = Path("logs/calibration_validation")
DEFAULT_RUNTIME_CALIBRATION = Path("logs/calibration/score_calibration.csv")
DEFAULT_RUNTIME_POLICY = Path("logs/calibration/edge_gate_policy.json")


@dataclass(frozen=True)
class ValidationConfig:
    train_ratio: float = 0.60
    optimize_ratio: float = 0.20
    purge_rows: int = 6
    bucket_width: int = 10
    prior_strength: float = 20.0
    minimum_total_rows: int = 180
    baseline_score_threshold: int = 70
    minimum_selected: int = 30


@dataclass(frozen=True)
class SplitSummary:
    name: str
    rows: int
    start_timestamp: Optional[str]
    end_timestamp: Optional[str]


@dataclass
class CalibrationValidationResult:
    created_utc: str
    status: str
    dataset_path: str
    dataset_sha256: str
    rows_loaded: int
    rows_usable: int
    warnings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    splits: list[SplitSummary] = field(default_factory=list)
    recommended_policy: Optional[dict] = None
    baseline_holdout: dict = field(default_factory=dict)
    baseline_by_side: dict = field(default_factory=dict)
    optimized_holdout: dict = field(default_factory=dict)
    holdout_by_side: dict = field(default_factory=dict)
    calibration_metrics: dict = field(default_factory=dict)
    output_files: dict = field(default_factory=dict)
    promoted: bool = False

    def to_dict(self) -> dict:
        data = asdict(self)
        data["splits"] = [asdict(item) for item in self.splits]
        return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pick_column(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    normalized = {str(column).strip().lower(): column for column in columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    return None


def load_validation_dataset(path: Path | str) -> tuple[pd.DataFrame, list[str]]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)

    frame = pd.read_csv(source, encoding="utf-8-sig", low_memory=False)
    warnings: list[str] = []

    score_col = _pick_column(frame.columns, ("score", "raw_score"))
    return_col = _pick_column(
        frame.columns,
        (
            "evaluated_return",
            "net_signed_return_after_6c_pct",
            "net_return_after_24h_pct",
            "return_after_24h_pct",
            "signed_return_after_6c_pct",
        ),
    )
    timestamp_col = _pick_column(
        frame.columns,
        ("candle_timestamp", "decision_timestamp", "timestamp", "created_at", "created_utc"),
    )

    if score_col is None:
        raise ValueError("No decision score column found.")
    if return_col is None:
        raise ValueError("No evaluated return column found.")

    if "evaluation_status" in frame.columns:
        frame = frame[frame["evaluation_status"].astype(str).str.upper().eq("COMPLETE")]

    if "side" in frame.columns:
        frame["side"] = frame["side"].astype(str).str.upper()
        frame = frame[frame["side"].isin(["LONG", "SHORT"])]

    frame = frame.copy()
    frame["score"] = pd.to_numeric(frame[score_col], errors="coerce")
    frame["evaluated_return"] = pd.to_numeric(frame[return_col], errors="coerce")
    frame = frame.dropna(subset=["score", "evaluated_return"])
    frame = frame[frame["score"].between(0, 100)]
    frame["win"] = frame["evaluated_return"] > 0

    if "decision_id" in frame.columns:
        before = len(frame)
        frame = frame.drop_duplicates("decision_id", keep="last")
        removed = before - len(frame)
        if removed:
            warnings.append(f"Removed {removed} duplicate decision_id rows.")

    if timestamp_col is not None:
        parsed = pd.to_datetime(frame[timestamp_col], errors="coerce", utc=True)
        invalid = int(parsed.isna().sum())
        if invalid:
            warnings.append(f"Dropped {invalid} rows with invalid timestamps.")
        frame = frame.loc[parsed.notna()].copy()
        frame["_event_time"] = parsed.loc[parsed.notna()]
        frame = frame.sort_values(["_event_time"], kind="stable")
    else:
        warnings.append("Timestamp column missing; original row order is used. Leakage protection is weaker.")
        frame["_event_time"] = pd.NaT

    frame = frame.reset_index(drop=True)
    frame["_row_order"] = range(len(frame))
    return frame, warnings


def chronological_three_way_split(
    frame: pd.DataFrame,
    config: ValidationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[SplitSummary]]:
    n = len(frame)
    if n < config.minimum_total_rows:
        raise ValueError(f"At least {config.minimum_total_rows} usable rows are required; found {n}.")
    if config.train_ratio <= 0 or config.optimize_ratio <= 0:
        raise ValueError("train_ratio and optimize_ratio must be positive.")
    if config.train_ratio + config.optimize_ratio >= 1:
        raise ValueError("train_ratio + optimize_ratio must be below 1.")

    train_boundary = int(n * config.train_ratio)
    optimize_boundary = int(n * (config.train_ratio + config.optimize_ratio))
    purge = max(0, int(config.purge_rows))

    train_stop = max(0, train_boundary - purge)
    optimize_stop = max(train_boundary, optimize_boundary - purge)
    train = frame.iloc[:train_stop].copy()
    optimize = frame.iloc[train_boundary:optimize_stop].copy()
    holdout = frame.iloc[optimize_boundary:].copy()

    if min(len(train), len(optimize), len(holdout)) < 30:
        raise ValueError("Each chronological split must contain at least 30 rows after purging.")

    def summary(name: str, part: pd.DataFrame) -> SplitSummary:
        timestamps = part["_event_time"].dropna() if "_event_time" in part else pd.Series(dtype="datetime64[ns, UTC]")
        return SplitSummary(
            name=name,
            rows=len(part),
            start_timestamp=str(timestamps.iloc[0]) if not timestamps.empty else None,
            end_timestamp=str(timestamps.iloc[-1]) if not timestamps.empty else None,
        )

    return train, optimize, holdout, [summary("train", train), summary("optimize", optimize), summary("holdout", holdout)]


def build_calibration_table(
    train: pd.DataFrame,
    *,
    bucket_width: int = 10,
    prior_strength: float = 20.0,
) -> pd.DataFrame:
    width = max(1, int(bucket_width))
    data = train[["score", "evaluated_return", "win"]].copy()
    data["bucket_low"] = (data["score"] // width * width).clip(0, 100).astype(int)
    data["bucket_high"] = (data["bucket_low"] + width - 1).clip(upper=100)
    global_rate = float(data["win"].mean()) if len(data) else 0.5

    grouped = (
        data.groupby(["bucket_low", "bucket_high"], sort=True)
        .agg(
            sample_count=("win", "size"),
            wins=("win", "sum"),
            observed_success_rate=("win", "mean"),
            avg_return=("evaluated_return", "mean"),
            median_return=("evaluated_return", "median"),
        )
        .reset_index()
    )
    grouped["raw_score"] = (grouped["bucket_low"] + grouped["bucket_high"]) / 2.0
    grouped["calibrated_probability"] = (
        grouped["wins"] + float(prior_strength) * global_rate
    ) / (grouped["sample_count"] + float(prior_strength))
    grouped["global_prior"] = global_rate
    return grouped[
        [
            "raw_score",
            "bucket_low",
            "bucket_high",
            "sample_count",
            "wins",
            "observed_success_rate",
            "calibrated_probability",
            "avg_return",
            "median_return",
            "global_prior",
        ]
    ].sort_values("raw_score").reset_index(drop=True)


def apply_calibration_table(frame: pd.DataFrame, table: pd.DataFrame) -> pd.DataFrame:
    if table.empty:
        raise ValueError("Calibration table is empty.")
    points = table.sort_values("raw_score").reset_index(drop=True)
    scores = pd.to_numeric(frame["score"], errors="coerce")

    def map_one(score: float) -> tuple[float, int]:
        if pd.isna(score):
            return math.nan, 0
        if score <= points.iloc[0]["raw_score"]:
            row = points.iloc[0]
            return float(row["calibrated_probability"]), int(row["sample_count"])
        if score >= points.iloc[-1]["raw_score"]:
            row = points.iloc[-1]
            return float(row["calibrated_probability"]), int(row["sample_count"])
        for idx in range(1, len(points)):
            right = points.iloc[idx]
            if score <= right["raw_score"]:
                left = points.iloc[idx - 1]
                span = float(right["raw_score"] - left["raw_score"])
                weight = 0.0 if span == 0 else float((score - left["raw_score"]) / span)
                probability = float(left["calibrated_probability"]) + weight * (
                    float(right["calibrated_probability"]) - float(left["calibrated_probability"])
                )
                support = min(int(left["sample_count"]), int(right["sample_count"]))
                return max(0.0, min(1.0, probability)), support
        return math.nan, 0

    mapped = [map_one(value) for value in scores]
    result = frame.copy()
    result["calibrated_probability"] = [item[0] for item in mapped]
    result["calibration_sample_count"] = [item[1] for item in mapped]
    return result


def calibration_metrics(frame: pd.DataFrame, *, bins: int = 10) -> tuple[dict, pd.DataFrame]:
    clean = frame.dropna(subset=["calibrated_probability", "win"]).copy()
    if clean.empty:
        return {"sample_count": 0, "brier_score": None, "log_loss": None, "ece": None, "mce": None}, pd.DataFrame()

    probability = pd.to_numeric(clean["calibrated_probability"], errors="coerce").clip(1e-6, 1 - 1e-6)
    actual = clean["win"].astype(float)
    brier = float(((probability - actual) ** 2).mean())
    log_loss = float((-(actual * probability.map(math.log) + (1 - actual) * (1 - probability).map(math.log))).mean())

    clean["probability_bin"] = pd.cut(probability, bins=bins, include_lowest=True, duplicates="drop")
    diagnostics = (
        clean.groupby("probability_bin", observed=True)
        .agg(
            sample_count=("win", "size"),
            mean_predicted_probability=("calibrated_probability", "mean"),
            observed_win_rate=("win", "mean"),
            avg_return=("evaluated_return", "mean"),
        )
        .reset_index()
    )
    diagnostics["absolute_calibration_error"] = (
        diagnostics["mean_predicted_probability"] - diagnostics["observed_win_rate"]
    ).abs()
    diagnostics["probability_bin"] = diagnostics["probability_bin"].astype(str)
    ece = float(
        (diagnostics["absolute_calibration_error"] * diagnostics["sample_count"]).sum()
        / diagnostics["sample_count"].sum()
    )
    mce = float(diagnostics["absolute_calibration_error"].max())
    return {
        "sample_count": int(len(clean)),
        "brier_score": round(brier, 6),
        "log_loss": round(log_loss, 6),
        "ece": round(ece, 6),
        "mce": round(mce, 6),
    }, diagnostics


def _metrics_dict(frame: pd.DataFrame, mask: pd.Series) -> dict:
    return selection_metrics(frame.loc[mask, "evaluated_return"]).to_dict()


def _side_metrics(frame: pd.DataFrame, mask: pd.Series) -> dict:
    if "side" not in frame.columns:
        return {}
    output: dict[str, dict] = {}
    for side in ("LONG", "SHORT"):
        side_mask = mask & frame["side"].eq(side)
        output[side] = _metrics_dict(frame, side_mask)
    return output



def _raw_threshold_diagnostics(parts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows: list[dict] = []
    for split_name, frame in parts.items():
        segments = {"ALL": frame}
        if "side" in frame.columns:
            segments["LONG"] = frame[frame["side"].eq("LONG")]
            segments["SHORT"] = frame[frame["side"].eq("SHORT")]
        for segment_name, segment in segments.items():
            for threshold in range(50, 91, 5):
                mask = pd.to_numeric(segment["score"], errors="coerce").ge(threshold)
                metrics = selection_metrics(segment.loc[mask, "evaluated_return"]).to_dict()
                rows.append({"split": split_name, "segment": segment_name, "raw_score_threshold": threshold, **metrics})
    return pd.DataFrame(rows)

def _policy_json(policy: EdgeGatePolicyCandidate, *, status: str, result_status: str, dataset_sha256: str) -> dict:
    return {
        "schema_version": 1,
        "status": status,
        "validation_status": result_status,
        "approved": status == "PROMOTED",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": dataset_sha256,
        **policy.to_dict(),
    }


def run_calibration_validation(
    dataset_path: Path | str = DEFAULT_DATASET,
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    config: ValidationConfig = ValidationConfig(),
    promote: bool = False,
    runtime_calibration_path: Path | str = DEFAULT_RUNTIME_CALIBRATION,
    runtime_policy_path: Path | str = DEFAULT_RUNTIME_POLICY,
) -> CalibrationValidationResult:
    source = Path(dataset_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    loaded = pd.read_csv(source, encoding="utf-8-sig", low_memory=False)
    frame, warnings = load_validation_dataset(source)
    result = CalibrationValidationResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        status="RUNNING",
        dataset_path=str(source),
        dataset_sha256=_sha256(source),
        rows_loaded=len(loaded),
        rows_usable=len(frame),
        warnings=warnings,
    )

    train, optimize, holdout, splits = chronological_three_way_split(frame, config)
    result.splits = splits

    table = build_calibration_table(
        train,
        bucket_width=config.bucket_width,
        prior_strength=config.prior_strength,
    )
    optimize_mapped = apply_calibration_table(optimize, table)
    holdout_mapped = apply_calibration_table(holdout, table)

    policy, candidates = optimize_edge_thresholds(
        optimize_mapped,
        minimum_selected=config.minimum_selected,
    )
    if policy is None:
        result.status = "FAIL"
        result.blockers.append("No positive out-of-sample threshold candidate survived the optimization constraints.")
        result.recommended_policy = None
    else:
        result.recommended_policy = policy.to_dict()

    baseline_mask = pd.to_numeric(holdout_mapped["score"], errors="coerce").ge(config.baseline_score_threshold)
    optimized_mask = apply_policy(holdout_mapped, policy) if policy is not None else pd.Series(False, index=holdout_mapped.index)
    result.baseline_holdout = _metrics_dict(holdout_mapped, baseline_mask)
    result.baseline_by_side = _side_metrics(holdout_mapped, baseline_mask)
    result.optimized_holdout = _metrics_dict(holdout_mapped, optimized_mask)
    result.holdout_by_side = _side_metrics(holdout_mapped, optimized_mask)
    calibration_summary, calibration_bins = calibration_metrics(holdout_mapped)
    result.calibration_metrics = calibration_summary

    optimized = result.optimized_holdout
    if result.status != "FAIL":
        if optimized["sample_count"] < config.minimum_selected:
            result.status = "FAIL"
            result.blockers.append("Optimized policy selected too few untouched holdout decisions.")
        elif optimized["expectancy"] <= 0 or optimized["profit_factor"] < 1.0:
            result.status = "FAIL"
            result.blockers.append("Optimized policy did not preserve positive expectancy on the untouched holdout.")
        elif calibration_summary.get("brier_score") is not None and calibration_summary["brier_score"] > 0.30:
            result.status = "FAIL"
            result.blockers.append("Holdout Brier score is too weak for policy promotion.")
        elif optimized["sample_count"] < 60 or optimized["profit_factor"] < 1.10:
            result.status = "PASS_WITH_WARNINGS"
            result.warnings.append("Holdout edge is positive but not yet robust enough for automatic promotion.")
        else:
            result.status = "PASS"

    table_path = destination / "score_calibration_train.csv"
    candidates_path = destination / "threshold_candidates.csv"
    bins_path = destination / "calibration_bucket_diagnostics.csv"
    holdout_path = destination / "holdout_scored.csv"
    summary_csv_path = destination / "calibration_validation_report.csv"
    report_json_path = destination / "calibration_validation_report.json"
    recommended_policy_path = destination / "recommended_edge_gate_policy.json"
    candidate_mapping_path = destination / "score_calibration_candidate.csv"
    segment_diagnostics_path = destination / "raw_threshold_diagnostics.csv"

    table.to_csv(table_path, index=False, encoding="utf-8-sig")
    candidates.to_csv(candidates_path, index=False, encoding="utf-8-sig")
    calibration_bins.to_csv(bins_path, index=False, encoding="utf-8-sig")
    holdout_mapped.to_csv(holdout_path, index=False, encoding="utf-8-sig")
    raw_diagnostics = _raw_threshold_diagnostics({"optimize": optimize_mapped, "holdout": holdout_mapped})
    raw_diagnostics.to_csv(segment_diagnostics_path, index=False, encoding="utf-8-sig")

    final_mapping = build_calibration_table(
        frame,
        bucket_width=config.bucket_width,
        prior_strength=config.prior_strength,
    )
    final_mapping.to_csv(candidate_mapping_path, index=False, encoding="utf-8-sig")
    if policy is not None:
        recommended_policy_payload = _policy_json(
            policy,
            status="RECOMMENDED",
            result_status=result.status,
            dataset_sha256=result.dataset_sha256,
        )
    else:
        recommended_policy_payload = {
            "schema_version": 1,
            "status": "NO_RECOMMENDATION",
            "validation_status": result.status,
            "approved": False,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "dataset_sha256": result.dataset_sha256,
            "reason": result.blockers[0] if result.blockers else "No robust policy was found.",
        }
    recommended_policy_path.write_text(json.dumps(recommended_policy_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_rows = []
    for label, metrics in (("baseline_holdout", result.baseline_holdout), ("optimized_holdout", result.optimized_holdout)):
        summary_rows.append({"segment": label, **metrics})
    for side, metrics in result.baseline_by_side.items():
        summary_rows.append({"segment": f"baseline_{side.lower()}", **metrics})
    for side, metrics in result.holdout_by_side.items():
        summary_rows.append({"segment": f"optimized_{side.lower()}", **metrics})
    pd.DataFrame(summary_rows).to_csv(summary_csv_path, index=False, encoding="utf-8-sig")

    result.output_files = {
        "training_mapping": str(table_path),
        "threshold_candidates": str(candidates_path),
        "calibration_diagnostics": str(bins_path),
        "holdout_scored": str(holdout_path),
        "summary_csv": str(summary_csv_path),
        "recommended_policy": str(recommended_policy_path),
        "candidate_mapping": str(candidate_mapping_path),
        "raw_threshold_diagnostics": str(segment_diagnostics_path),
        "report_json": str(report_json_path),
    }

    if promote:
        if result.status != "PASS" or policy is None:
            result.warnings.append("Promotion requested but blocked because validation status is not PASS.")
        else:
            active_mapping = Path(runtime_calibration_path)
            active_policy = Path(runtime_policy_path)
            active_mapping.parent.mkdir(parents=True, exist_ok=True)
            active_policy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidate_mapping_path, active_mapping)
            promoted_payload = _policy_json(
                policy,
                status="PROMOTED",
                result_status=result.status,
                dataset_sha256=result.dataset_sha256,
            )
            active_policy.write_text(json.dumps(promoted_payload, ensure_ascii=False, indent=2), encoding="utf-8")
            result.promoted = True
            result.output_files["active_mapping"] = str(active_mapping)
            result.output_files["active_policy"] = str(active_policy)

    report_json_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result
