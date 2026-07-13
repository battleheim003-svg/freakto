"""Baseline benchmark suite for Freakto Feature Architecture v2.

All comparisons use the same chronological Holdout segment.  The suite is
research-only and can freeze a development candidate manifest, but it never
promotes a runtime model or enables Paper/Live trading.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import joblib

from engine.feature_architecture_v2 import (
    ArchitectureBundle,
    FeatureArchitectureV2Config,
    ThresholdSelection,
    apply_thresholds,
    chronological_development_split,
    engineer_entry_features,
    fit_architecture_bundle,
    model_coefficients,
    predict_architecture,
    prepare_architecture_rows,
    select_side_threshold,
)
from engine.multi_cycle_validation import load_replay_files

VERSION = "2.0.0"
MODE = "BASELINE_BENCHMARK_DEVELOPMENT_ONLY"
DEFAULT_REPLAY_ROOT = Path("logs") / "multi_cycle_archive_v2"
DEFAULT_OUTPUT_DIR = Path("logs") / "feature_architecture_v2"
MARKET_RETURN_CANDIDATES = (
    "market_return_after_6c_pct",
    "raw_market_return_after_6c_pct",
    "unsigned_market_return_after_6c_pct",
)
COST_CANDIDATES = (
    "round_trip_cost_pct",
    "execution_cost_pct",
    "total_cost_pct",
    "estimated_round_trip_cost_pct",
    "fee_slippage_pct",
)


@dataclass(frozen=True)
class BenchmarkConfig:
    architecture: FeatureArchitectureV2Config = field(default_factory=FeatureArchitectureV2Config)
    variants: Tuple[str, ...] = ("ARCH_V2_BASE", "ARCH_V2_NO_MOMENTUM", "ARCH_V2_LEAN", "ARCH_V2_LONG_ONLY")
    champion_score_threshold: float = 70.0
    trend_threshold: float = 18.0
    mean_reversion_rsi_low: float = 35.0
    mean_reversion_rsi_high: float = 65.0
    walk_forward_folds: int = 3
    minimum_walk_forward_train_rows: int = 600
    minimum_walk_forward_test_rows: int = 100
    bootstrap_samples: int = 300
    bootstrap_block_size: int = 24
    random_seed: int = 42
    promotion_min_expectancy_pct: float = 0.0
    promotion_min_profit_factor: float = 1.05
    promotion_min_samples: int = 200
    promotion_min_positive_walk_forward_fraction: float = 2.0 / 3.0
    baseline_margin_pct: float = 0.05


@dataclass
class BenchmarkReport:
    status: str
    mode: str
    version: str
    created_utc: str
    selected_replay_window: Optional[str]
    available_replay_windows: List[str]
    development_cutoff_utc: str
    rows_loaded: int
    rows_usable: int
    split_boundaries: Dict[str, str]
    variants_evaluated: List[str]
    baselines_evaluated: List[str]
    development_candidate: Optional[str]
    fresh_oos_required: bool
    key_findings: List[str]
    blockers: List[str]
    warnings: List[str]
    output_files: Dict[str, str] = field(default_factory=dict)
    promotion_applied: bool = False
    paper_live_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BenchmarkArtifacts:
    holdout_benchmarks: pd.DataFrame = field(default_factory=pd.DataFrame)
    threshold_candidates: pd.DataFrame = field(default_factory=pd.DataFrame)
    side_diagnostics: pd.DataFrame = field(default_factory=pd.DataFrame)
    feature_coefficients: pd.DataFrame = field(default_factory=pd.DataFrame)
    walk_forward: pd.DataFrame = field(default_factory=pd.DataFrame)
    prediction_sample: pd.DataFrame = field(default_factory=pd.DataFrame)
    candidate_manifest: Dict[str, Any] = field(default_factory=dict)
    frozen_candidate_payload: Any = field(default=None, repr=False)


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


def strategy_metrics(returns: Sequence[float], *, total_rows: int = 0) -> Dict[str, Any]:
    values = pd.Series(returns, dtype=float).replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        return {
            "sample_count": 0,
            "coverage": 0.0,
            "win_rate": 0.0,
            "expectancy": 0.0,
            "median_return": 0.0,
            "profit_factor": 0.0,
            "total_return": 0.0,
            "max_drawdown": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
        }
    wins = values[values > 0]
    losses = values[values <= 0]
    gross_profit = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    pf = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    equity = values.cumsum().to_numpy(dtype=float)
    peaks = np.maximum.accumulate(np.r_[0.0, equity])
    max_drawdown = float((np.r_[0.0, equity] - peaks).min())
    return {
        "sample_count": int(len(values)),
        "coverage": float(len(values) / max(1, int(total_rows))),
        "win_rate": float((values > 0).mean()),
        "expectancy": float(values.mean()),
        "median_return": float(values.median()),
        "profit_factor": float(pf),
        "total_return": float(values.sum()),
        "max_drawdown": max_drawdown,
        "average_win": float(wins.mean()) if not wins.empty else 0.0,
        "average_loss": float(losses.mean()) if not losses.empty else 0.0,
    }


def block_bootstrap_expectancy_ci(
    returns: Sequence[float], *, samples: int = 300, block_size: int = 24, seed: int = 42
) -> Tuple[float, float]:
    values = pd.Series(returns, dtype=float).replace([np.inf, -np.inf], np.nan).dropna().to_numpy()
    if len(values) < 10 or samples <= 0:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    block = max(1, min(int(block_size), len(values)))
    starts = np.arange(0, max(1, len(values) - block + 1))
    estimates: List[float] = []
    required_blocks = int(np.ceil(len(values) / block))
    for _ in range(int(samples)):
        chosen = rng.choice(starts, size=required_blocks, replace=True)
        sample = np.concatenate([values[start : start + block] for start in chosen])[: len(values)]
        estimates.append(float(sample.mean()))
    return float(np.quantile(estimates, 0.025)), float(np.quantile(estimates, 0.975))


def _numeric_column(frame: pd.DataFrame, candidates: Sequence[str]) -> Optional[pd.Series]:
    column = next((c for c in candidates if c in frame.columns), None)
    return None if column is None else pd.to_numeric(frame[column], errors="coerce")


def _baseline_rows(holdout: pd.DataFrame, config: BenchmarkConfig) -> Dict[str, pd.Series]:
    rows: Dict[str, pd.Series] = {}
    rows["ALL_DIRECTIONAL"] = holdout["__return"]
    rows["LONG_ONLY"] = holdout.loc[holdout["side"].eq("LONG"), "__return"]
    rows["SHORT_ONLY"] = holdout.loc[holdout["side"].eq("SHORT"), "__return"]
    score = pd.to_numeric(holdout["score"], errors="coerce") if "score" in holdout.columns else pd.Series(np.nan, index=holdout.index)
    rows["CHAMPION_SCORE_GE_70"] = holdout.loc[score.ge(config.champion_score_threshold), "__return"]

    if "trend_score" in holdout.columns:
        trend = pd.to_numeric(holdout["trend_score"], errors="coerce")
        rows["TREND_ONLY"] = holdout.loc[trend.ge(config.trend_threshold), "__return"]
    rsi_column = next((c for c in ("rsi_14", "rsi") if c in holdout.columns), None)
    if rsi_column:
        rsi = pd.to_numeric(holdout[rsi_column], errors="coerce")
        mask = (holdout["side"].eq("LONG") & rsi.le(config.mean_reversion_rsi_low)) | (
            holdout["side"].eq("SHORT") & rsi.ge(config.mean_reversion_rsi_high)
        )
        rows["MEAN_REVERSION_RSI"] = holdout.loc[mask, "__return"]

    market = _numeric_column(holdout, MARKET_RETURN_CANDIDATES)
    if market is not None:
        cost = _numeric_column(holdout, COST_CANDIDATES)
        cost = pd.Series(0.0, index=holdout.index) if cost is None else cost.fillna(0.0).clip(lower=0.0)
        rows["BUY_AND_HOLD"] = (market - cost).dropna()
        ids = holdout.get("decision_id", holdout.index.astype(str)).astype(str)
        signs = ids.map(lambda value: 1.0 if int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16) % 2 == 0 else -1.0)
        rows["RANDOM_DIRECTIONAL"] = (market * signs - cost).dropna()
    return rows


def _benchmark_record(name: str, family: str, returns: Sequence[float], total_rows: int, config: BenchmarkConfig, **extra: Any) -> Dict[str, Any]:
    metrics = strategy_metrics(returns, total_rows=total_rows)
    low, high = block_bootstrap_expectancy_ci(
        returns,
        samples=config.bootstrap_samples,
        block_size=config.bootstrap_block_size,
        seed=config.random_seed,
    )
    return {
        "strategy": name,
        "family": family,
        **metrics,
        "expectancy_ci_low": low,
        "expectancy_ci_high": high,
        **extra,
    }


def _architecture_variant(
    train: pd.DataFrame,
    optimize: pd.DataFrame,
    holdout: pd.DataFrame,
    variant: str,
    config: BenchmarkConfig,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    bundle = fit_architecture_bundle(train, variant, config.architecture)
    optimize_predictions = predict_architecture(bundle, optimize)
    holdout_predictions = predict_architecture(bundle, holdout)
    selections: Dict[str, ThresholdSelection] = {
        side: select_side_threshold(optimize_predictions, side, config.architecture) for side in ("LONG", "SHORT")
    }
    long_only = "LONG_ONLY" in variant.upper()
    selected = apply_thresholds(holdout_predictions, selections, long_only=long_only)
    record = _benchmark_record(
        variant,
        "ARCHITECTURE_V2",
        selected["__return"],
        len(holdout),
        config,
        long_threshold=selections["LONG"].threshold,
        short_threshold=None if long_only else selections["SHORT"].threshold,
        optimize_long_eligible=selections["LONG"].eligible,
        optimize_short_eligible=False if long_only else selections["SHORT"].eligible,
    )
    threshold_rows = [row | {"variant": variant} for selection in selections.values() for row in selection.candidate_rows]
    diagnostics = []
    for side, model in bundle.models.items():
        diagnostics.append(
            {
                "variant": variant,
                "side": side,
                "train_rows": model.train_rows,
                "average_win_pct": model.average_win_pct,
                "average_loss_pct": model.average_loss_pct,
                "feature_count": len(model.feature_columns),
                **model.gate_diagnostics,
            }
        )
    coefficients = model_coefficients(bundle)
    prediction_columns = [
        c
        for c in (
            "decision_id",
            "__timestamp",
            "symbol",
            "side",
            "regime",
            "__return",
            "predicted_return_pct",
            "predicted_win_probability",
            "predicted_probability_ev_pct",
            "predicted_expected_net_pct",
            "gate_pass",
        )
        if c in holdout_predictions.columns
    ]
    predictions = holdout_predictions[prediction_columns].copy()
    predictions["variant"] = variant
    payload = {
        "version": VERSION,
        "variant": variant,
        "bundle": bundle,
        "selections": selections,
        "long_only": long_only,
        "development_cutoff_utc": config.architecture.development_cutoff_utc,
    }
    return record, threshold_rows, pd.DataFrame(diagnostics), coefficients, predictions, payload


def walk_forward_architecture(frame: pd.DataFrame, variant: str, config: BenchmarkConfig) -> pd.DataFrame:
    work = prepare_architecture_rows(frame, config.architecture)
    if work.empty:
        return pd.DataFrame()
    timestamps = pd.Index(work["__timestamp"].drop_duplicates().sort_values())
    folds = max(1, int(config.walk_forward_folds))
    # Reserve successive chronological test blocks after an initial 50% train.
    initial = int(len(timestamps) * 0.50)
    remaining = max(1, len(timestamps) - initial)
    test_size = max(1, remaining // folds)
    records: List[Dict[str, Any]] = []
    for fold in range(folds):
        test_start_idx = initial + fold * test_size
        test_end_idx = len(timestamps) if fold == folds - 1 else min(len(timestamps), test_start_idx + test_size)
        purge = config.architecture.purge_timestamps
        train_times = timestamps[: max(0, test_start_idx - purge)]
        test_times = timestamps[min(len(timestamps), test_start_idx + purge) : test_end_idx]
        train = work[work["__timestamp"].isin(train_times)]
        test = work[work["__timestamp"].isin(test_times)]
        if len(train) < config.minimum_walk_forward_train_rows or len(test) < config.minimum_walk_forward_test_rows:
            continue
        engineered_train, _ = engineer_entry_features(train, config.architecture)
        # Internal Optimize is the final 20% of the fold's training history.
        internal_times = pd.Index(engineered_train["__timestamp"].drop_duplicates().sort_values())
        split_at = max(1, int(len(internal_times) * 0.80))
        fit_times = internal_times[: max(1, split_at - purge)]
        opt_times = internal_times[min(len(internal_times), split_at + purge) :]
        fit_frame = engineered_train[engineered_train["__timestamp"].isin(fit_times)]
        opt_frame = engineered_train[engineered_train["__timestamp"].isin(opt_times)]
        if len(fit_frame) < config.minimum_walk_forward_train_rows // 2 or len(opt_frame) < config.architecture.minimum_optimize_samples:
            continue
        try:
            bundle = fit_architecture_bundle(fit_frame, variant, config.architecture)
            opt_pred = predict_architecture(bundle, opt_frame)
            selections = {side: select_side_threshold(opt_pred, side, config.architecture) for side in ("LONG", "SHORT")}
            test_pred = predict_architecture(bundle, test)
            selected = apply_thresholds(test_pred, selections, long_only="LONG_ONLY" in variant.upper())
            metrics = strategy_metrics(selected["__return"], total_rows=len(test))
            records.append(
                {
                    "variant": variant,
                    "fold": fold + 1,
                    "train_start": train["__timestamp"].min().isoformat(),
                    "train_end": train["__timestamp"].max().isoformat(),
                    "test_start": test["__timestamp"].min().isoformat(),
                    "test_end": test["__timestamp"].max().isoformat(),
                    "no_overlap": bool(train["__timestamp"].max() < test["__timestamp"].min()),
                    **metrics,
                    "positive": bool(metrics["expectancy"] > 0 and metrics["profit_factor"] >= 1.0),
                }
            )
        except ValueError as exc:
            records.append({"variant": variant, "fold": fold + 1, "error": str(exc), "positive": False})
    return pd.DataFrame(records)


def select_longest_replay(frames: Mapping[str, pd.DataFrame]) -> Tuple[Optional[str], pd.DataFrame]:
    available = {name: frame for name, frame in frames.items() if frame is not None and not frame.empty}
    if not available:
        return None, pd.DataFrame()
    preferred = next((name for name in ("FULL", "full", "5Y", "5y", "3Y", "3y") if name in available), None)
    if preferred is not None:
        return preferred.upper(), available[preferred]
    name, frame = max(available.items(), key=lambda item: len(item[1]))
    return str(name).upper(), frame


def analyze_feature_architecture_v2(
    replay_frames: Mapping[str, pd.DataFrame], config: Optional[BenchmarkConfig] = None
) -> Tuple[BenchmarkReport, BenchmarkArtifacts]:
    config = config or BenchmarkConfig()
    config.architecture.validate()
    selected_name, selected = select_longest_replay(replay_frames)
    available_names = sorted(str(name).upper() for name, frame in replay_frames.items() if frame is not None and not frame.empty)
    created = datetime.now(timezone.utc).isoformat()
    if selected.empty:
        report = BenchmarkReport(
            status="READY_AWAITING_MULTI_CYCLE_REPLAY",
            mode=MODE,
            version=VERSION,
            created_utc=created,
            selected_replay_window=None,
            available_replay_windows=available_names,
            development_cutoff_utc=config.architecture.development_cutoff_utc,
            rows_loaded=0,
            rows_usable=0,
            split_boundaries={},
            variants_evaluated=[],
            baselines_evaluated=[],
            development_candidate=None,
            fresh_oos_required=True,
            key_findings=[],
            blockers=["No multi-cycle replay rows were available."],
            warnings=[],
        )
        return report, BenchmarkArtifacts()

    prepared = prepare_architecture_rows(selected, config.architecture)
    try:
        split = chronological_development_split(prepared, config.architecture)
    except ValueError as exc:
        report = BenchmarkReport(
            status="INSUFFICIENT_CHRONOLOGICAL_DATA",
            mode=MODE,
            version=VERSION,
            created_utc=created,
            selected_replay_window=selected_name,
            available_replay_windows=available_names,
            development_cutoff_utc=config.architecture.development_cutoff_utc,
            rows_loaded=int(len(selected)),
            rows_usable=int(len(prepared)),
            split_boundaries={},
            variants_evaluated=[],
            baselines_evaluated=[],
            development_candidate=None,
            fresh_oos_required=True,
            key_findings=[],
            blockers=[str(exc)],
            warnings=[],
        )
        return report, BenchmarkArtifacts()

    benchmark_records: List[Dict[str, Any]] = []
    threshold_records: List[Dict[str, Any]] = []
    diagnostics_frames: List[pd.DataFrame] = []
    coefficient_frames: List[pd.DataFrame] = []
    prediction_frames: List[pd.DataFrame] = []
    walk_frames: List[pd.DataFrame] = []
    variant_payloads: Dict[str, Dict[str, Any]] = {}

    baseline_returns = _baseline_rows(split.holdout, config)
    for name, returns in baseline_returns.items():
        benchmark_records.append(_benchmark_record(name, "SIMPLE_BASELINE", returns, len(split.holdout), config))

    evaluated_variants: List[str] = []
    warnings: List[str] = []
    for variant in config.variants:
        try:
            record, thresholds, diagnostics, coefficients, predictions, payload = _architecture_variant(
                split.train, split.optimize, split.holdout, variant, config
            )
            benchmark_records.append(record)
            threshold_records.extend(thresholds)
            diagnostics_frames.append(diagnostics)
            coefficient_frames.append(coefficients)
            prediction_frames.append(predictions)
            walk = walk_forward_architecture(prepared, variant, config)
            if not walk.empty:
                walk_frames.append(walk)
            variant_payloads[variant] = payload
            evaluated_variants.append(variant)
        except ValueError as exc:
            warnings.append(f"{variant} unavailable: {exc}")

    benchmarks = pd.DataFrame(benchmark_records)
    walk_forward = pd.concat(walk_frames, ignore_index=True) if walk_frames else pd.DataFrame()
    if not benchmarks.empty:
        architecture_rows = benchmarks[benchmarks["family"].eq("ARCHITECTURE_V2")].copy()
        simple_rows = benchmarks[benchmarks["family"].eq("SIMPLE_BASELINE")].copy()
    else:
        architecture_rows = pd.DataFrame()
        simple_rows = pd.DataFrame()

    best_simple_expectancy = float(simple_rows["expectancy"].max()) if not simple_rows.empty else 0.0
    candidate: Optional[str] = None
    key_findings: List[str] = []
    blockers: List[str] = []
    if not architecture_rows.empty:
        for _, row in architecture_rows.sort_values(["expectancy", "profit_factor"], ascending=False).iterrows():
            variant = str(row["strategy"])
            wf = walk_forward[walk_forward.get("variant", pd.Series(dtype=str)).eq(variant)] if not walk_forward.empty else pd.DataFrame()
            positive_fraction = float(wf["positive"].mean()) if not wf.empty and "positive" in wf.columns else 0.0
            eligible = (
                int(row["sample_count"]) >= config.promotion_min_samples
                and float(row["expectancy"]) > config.promotion_min_expectancy_pct
                and _safe_pf(row["profit_factor"]) >= config.promotion_min_profit_factor
                and float(row["expectancy_ci_low"]) > 0
                and positive_fraction >= config.promotion_min_positive_walk_forward_fraction
                and float(row["expectancy"]) >= best_simple_expectancy + config.baseline_margin_pct
            )
            if eligible:
                candidate = variant
                break
        best_arch = architecture_rows.sort_values("expectancy", ascending=False).iloc[0]
        key_findings.append(
            f"Best architecture Holdout variant was {best_arch['strategy']} with n={int(best_arch['sample_count'])}, "
            f"expectancy={float(best_arch['expectancy']):.6f}% and PF={_safe_pf(best_arch['profit_factor']):.6f}."
        )
    if not simple_rows.empty:
        best_simple = simple_rows.sort_values("expectancy", ascending=False).iloc[0]
        key_findings.append(
            f"Best simple Holdout baseline was {best_simple['strategy']} with expectancy={float(best_simple['expectancy']):.6f}% "
            f"and PF={_safe_pf(best_simple['profit_factor']):.6f}."
        )
    if candidate is None:
        blockers.append("No Feature Architecture v2 variant beat simple baselines with positive, confidence-supported, walk-forward-stable Holdout edge.")
    else:
        blockers.append("Development candidate cannot be promoted until the frozen candidate passes untouched Fresh OOS and Forward/Paper validation.")
    key_findings.append("Aggregate score was excluded from Feature Architecture v2 model inputs; LONG and SHORT models were fitted independently.")
    key_findings.append("Structure was used as an entry gate rather than an additive score; Momentum was capped or removed in declared variants.")

    manifest = {
        "version": VERSION,
        "mode": MODE,
        "created_utc": created,
        "development_cutoff_utc": config.architecture.development_cutoff_utc,
        "selected_replay_window": selected_name,
        "candidate": candidate,
        "status": "DEVELOPMENT_CANDIDATE_REQUIRES_FRESH_OOS" if candidate else "NO_DEVELOPMENT_CANDIDATE",
        "fresh_oos_required": True,
        "promotion_applied": False,
        "paper_live_enabled": False,
        "score_used_as_feature": False,
        "config": asdict(config),
    }

    report = BenchmarkReport(
        status="COMPLETE_DEVELOPMENT_CANDIDATE_FROZEN" if candidate else "COMPLETE_NO_DEVELOPMENT_CANDIDATE",
        mode=MODE,
        version=VERSION,
        created_utc=created,
        selected_replay_window=selected_name,
        available_replay_windows=available_names,
        development_cutoff_utc=config.architecture.development_cutoff_utc,
        rows_loaded=int(len(selected)),
        rows_usable=int(len(prepared)),
        split_boundaries=split.boundaries,
        variants_evaluated=evaluated_variants,
        baselines_evaluated=sorted(baseline_returns),
        development_candidate=candidate,
        fresh_oos_required=True,
        key_findings=key_findings,
        blockers=blockers,
        warnings=warnings + ["All model and baseline results are development diagnostics only; Fresh OOS remains untouched."],
    )
    artifacts = BenchmarkArtifacts(
        holdout_benchmarks=benchmarks,
        threshold_candidates=pd.DataFrame(threshold_records),
        side_diagnostics=pd.concat(diagnostics_frames, ignore_index=True) if diagnostics_frames else pd.DataFrame(),
        feature_coefficients=pd.concat(coefficient_frames, ignore_index=True) if coefficient_frames else pd.DataFrame(),
        walk_forward=walk_forward,
        prediction_sample=pd.concat(prediction_frames, ignore_index=True).head(5000) if prediction_frames else pd.DataFrame(),
        candidate_manifest=manifest,
        frozen_candidate_payload=variant_payloads.get(candidate),
    )
    return report, artifacts


def evaluate_frozen_candidate(
    model_path: str | Path, fresh_frame: pd.DataFrame
) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Evaluate a frozen development candidate on strictly post-cutoff rows.

    The model, gates, and thresholds are loaded as-is. Nothing is fitted or
    selected on Fresh OOS.
    """
    payload = joblib.load(model_path)
    required = {"bundle", "selections", "long_only", "development_cutoff_utc"}
    if not isinstance(payload, dict) or not required.issubset(payload):
        raise ValueError("invalid frozen architecture candidate payload")
    bundle = payload["bundle"]
    predictions = predict_architecture(bundle, fresh_frame, time_scope="fresh", strict_gates=True)
    selected = apply_thresholds(predictions, payload["selections"], long_only=bool(payload["long_only"]))
    metrics = strategy_metrics(selected["__return"], total_rows=len(predictions))
    result = {
        "status": "FRESH_OOS_EVALUATED_FIXED_POLICY" if len(predictions) else "READY_AWAITING_FRESH_OOS",
        "variant": payload.get("variant"),
        "development_cutoff_utc": payload["development_cutoff_utc"],
        "fresh_rows": int(len(predictions)),
        "selected_rows": int(len(selected)),
        **metrics,
        "thresholds_reselected": False,
        "model_refit": False,
        "promotion_applied": False,
        "paper_live_enabled": False,
    }
    return result, selected


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, float) and not math.isfinite(value):
        return "inf" if value > 0 else "-inf"
    return value


def write_benchmark_outputs(report: BenchmarkReport, artifacts: BenchmarkArtifacts, output_dir: str | Path) -> Dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files: Dict[str, str] = {}
    tables = {
        "holdout_benchmarks": artifacts.holdout_benchmarks,
        "threshold_candidates": artifacts.threshold_candidates,
        "side_diagnostics": artifacts.side_diagnostics,
        "feature_coefficients": artifacts.feature_coefficients,
        "walk_forward": artifacts.walk_forward,
        "prediction_sample": artifacts.prediction_sample,
    }
    for name, table in tables.items():
        path = output / f"{name}.csv"
        table.to_csv(path, index=False, encoding="utf-8-sig")
        files[name] = str(path)
    manifest_path = output / "frozen_candidate_manifest.json"
    manifest_path.write_text(json.dumps(_json_safe(artifacts.candidate_manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    files["candidate_manifest"] = str(manifest_path)
    if artifacts.frozen_candidate_payload is not None:
        model_path = output / "frozen_architecture_candidate.joblib"
        joblib.dump(artifacts.frozen_candidate_payload, model_path)
        files["frozen_model"] = str(model_path)

    report.output_files = dict(files)
    json_path = output / "feature_architecture_v2_report.json"
    json_path.write_text(json.dumps(_json_safe(report.to_dict()), ensure_ascii=False, indent=2), encoding="utf-8")
    files["json"] = str(json_path)

    lines = [
        "# Freakto Feature Architecture v2 & Baseline Benchmark Suite",
        "",
        f"- Status: `{report.status}`",
        f"- Mode: `{report.mode}`",
        f"- Replay window: `{report.selected_replay_window}`",
        f"- Rows loaded/usable: `{report.rows_loaded} / {report.rows_usable}`",
        f"- Development candidate: `{report.development_candidate}`",
        "- Promotion applied: `False`",
        "- Paper/Live enabled: `False`",
        "",
        "## Safety contract",
        "",
        "Aggregate score is not a model input. Structure is a gate. LONG and SHORT are fitted independently. "
        "No result in this report authorizes runtime promotion; untouched Fresh OOS and Forward/Paper confirmation are mandatory.",
        "",
        "## Key findings",
    ]
    lines.extend(f"- {finding}" for finding in report.key_findings)
    lines += ["", "## Blockers"]
    lines.extend(f"- {blocker}" for blocker in report.blockers)
    lines += ["", "## Warnings"]
    lines.extend(f"- {warning}" for warning in report.warnings)
    markdown_path = output / "feature_architecture_v2_report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    files["markdown"] = str(markdown_path)
    report.output_files = dict(files)
    json_path.write_text(json.dumps(_json_safe(report.to_dict()), ensure_ascii=False, indent=2), encoding="utf-8")
    return files


def load_multi_cycle_replays(replay_root: str | Path) -> Dict[str, pd.DataFrame]:
    return load_replay_files(replay_root)
