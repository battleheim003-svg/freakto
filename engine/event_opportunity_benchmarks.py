"""Benchmark orchestration for Event Opportunity Universe & Cost-Aware Label v2."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import joblib
import numpy as np
import pandas as pd

from engine.baseline_benchmarks import (
    block_bootstrap_expectancy_ci,
    load_multi_cycle_replays,
    select_longest_replay,
    strategy_metrics,
)
from engine.cost_aware_label_v2 import (
    EventMetaLabelConfig,
    EventMetaModel,
    MetaThresholdSelection,
    apply_meta_threshold,
    build_cost_aware_labels,
    chronological_event_split,
    event_family_benchmarks,
    event_meta_coefficients,
    fit_event_meta_model,
    predict_event_meta,
    select_meta_threshold,
    walk_forward_event_meta,
)
from engine.event_opportunity_universe import (
    EventUniverseDiagnostics,
    build_event_opportunity_universe,
    event_overlap_table,
    prepare_event_rows,
)

VERSION = "2.0.0"
MODE = "EVENT_OPPORTUNITY_COST_AWARE_DEVELOPMENT_ONLY"
DEFAULT_REPLAY_ROOT = Path("logs") / "multi_cycle_archive_v2"
DEFAULT_OUTPUT_DIR = Path("logs") / "event_opportunity_v2"


@dataclass
class EventOpportunityReport:
    status: str
    mode: str
    version: str
    created_utc: str
    selected_replay_window: Optional[str]
    available_replay_windows: List[str]
    development_cutoff_utc: str
    rows_loaded: int
    directional_rows: int
    event_rows: int
    cost_gated_event_rows: int
    event_rate: float
    split_boundaries: Dict[str, str]
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
class EventOpportunityArtifacts:
    event_universe: pd.DataFrame = field(default_factory=pd.DataFrame)
    event_overlap: pd.DataFrame = field(default_factory=pd.DataFrame)
    label_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    event_family_benchmarks: pd.DataFrame = field(default_factory=pd.DataFrame)
    holdout_benchmarks: pd.DataFrame = field(default_factory=pd.DataFrame)
    threshold_candidates: pd.DataFrame = field(default_factory=pd.DataFrame)
    model_coefficients: pd.DataFrame = field(default_factory=pd.DataFrame)
    walk_forward: pd.DataFrame = field(default_factory=pd.DataFrame)
    prediction_sample: pd.DataFrame = field(default_factory=pd.DataFrame)
    candidate_manifest: Dict[str, Any] = field(default_factory=dict)
    frozen_candidate_payload: Any = field(default=None, repr=False)


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return "inf" if value > 0 else "-inf" if value < 0 else None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def _record(
    strategy: str,
    family: str,
    returns: Sequence[float],
    total_rows: int,
    config: EventMetaLabelConfig,
    **extra: Any,
) -> Dict[str, Any]:
    metrics = strategy_metrics(returns, total_rows=total_rows)
    low, high = block_bootstrap_expectancy_ci(
        returns,
        samples=config.bootstrap_samples,
        block_size=config.bootstrap_block_size,
        seed=config.random_seed,
    )
    return {
        "strategy": strategy,
        "family": family,
        **metrics,
        "expectancy_ci_low": low,
        "expectancy_ci_high": high,
        **extra,
    }


def _no_trade_record(total_rows: int) -> Dict[str, Any]:
    return {
        "strategy": "NO_TRADE",
        "family": "NULL_BASELINE",
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
        "expectancy_ci_low": 0.0,
        "expectancy_ci_high": 0.0,
        "holdout_rows": int(total_rows),
    }


def _label_summary(labels: pd.DataFrame) -> pd.DataFrame:
    if labels is None or labels.empty:
        return pd.DataFrame()
    records: List[Dict[str, Any]] = []
    for keys, group in labels.groupby(["primary_event", "triple_barrier_label"], dropna=False):
        event, barrier = keys
        metrics = strategy_metrics(group["realized_net_return_pct"], total_rows=len(labels))
        records.append(
            {
                "primary_event": event,
                "triple_barrier_label": barrier,
                "meta_positive_rate": float(group["meta_label"].mean()),
                "mean_cost_drag_pct": float(group["realized_cost_drag_pct"].mean()),
                **metrics,
            }
        )
    return pd.DataFrame(records)


def _family_scope_table(split, labels: pd.DataFrame) -> pd.DataFrame:
    frames = [
        event_family_benchmarks(split.train, scope="TRAIN"),
        event_family_benchmarks(split.optimize, scope="OPTIMIZE"),
        event_family_benchmarks(split.holdout, scope="HOLDOUT"),
    ]
    frames = [frame for frame in frames if not frame.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _threshold_table(selection: MetaThresholdSelection) -> pd.DataFrame:
    if not selection.candidate_rows:
        return pd.DataFrame()
    table = pd.DataFrame(selection.candidate_rows)
    table["selected"] = table["threshold"].eq(selection.threshold) if selection.threshold is not None else False
    table["selection_eligible"] = selection.eligible
    table["selection_reason"] = selection.reason
    return table


def _fresh_candidate_eligible(
    holdout_record: Dict[str, Any],
    walk_forward: pd.DataFrame,
    config: EventMetaLabelConfig,
    *,
    best_baseline_expectancy: float = 0.0,
) -> Tuple[bool, List[str], float]:
    blockers: List[str] = []
    valid_folds = walk_forward[walk_forward.get("error").isna()] if not walk_forward.empty and "error" in walk_forward.columns else walk_forward
    wf_fraction = float(valid_folds["positive"].mean()) if not valid_folds.empty and "positive" in valid_folds.columns else 0.0
    if holdout_record["sample_count"] < config.promotion_min_samples:
        blockers.append("Meta-label Holdout sample count is below the promotion minimum.")
    if holdout_record["expectancy"] <= config.promotion_min_expectancy_pct:
        blockers.append("Meta-label Holdout expectancy is not positive.")
    if holdout_record["profit_factor"] < config.promotion_min_profit_factor:
        blockers.append("Meta-label Holdout profit factor is below the promotion minimum.")
    if holdout_record["expectancy_ci_low"] <= config.promotion_min_ci_low_pct:
        blockers.append("Meta-label Holdout confidence interval does not stay above zero.")
    if wf_fraction < config.promotion_min_positive_walk_forward_fraction:
        blockers.append("Meta-label walk-forward positive-fold fraction is insufficient.")
    if holdout_record["expectancy"] < best_baseline_expectancy + config.promotion_baseline_margin_pct:
        blockers.append(
            "Meta-label Holdout expectancy did not beat the best adequately sampled simple/event baseline by the required margin."
        )
    return not blockers, blockers, wf_fraction


def analyze_event_opportunity_universe(
    replay_frames: Mapping[str, pd.DataFrame],
    config: Optional[EventMetaLabelConfig] = None,
) -> Tuple[EventOpportunityReport, EventOpportunityArtifacts]:
    config = config or EventMetaLabelConfig()
    config.validate()
    created = datetime.now(timezone.utc).isoformat()
    selected_name, selected = select_longest_replay(replay_frames)
    available = sorted(str(name).upper() for name, frame in replay_frames.items() if frame is not None and not frame.empty)
    if selected.empty:
        report = EventOpportunityReport(
            status="READY_AWAITING_MULTI_CYCLE_REPLAY",
            mode=MODE,
            version=VERSION,
            created_utc=created,
            selected_replay_window=None,
            available_replay_windows=available,
            development_cutoff_utc=config.event.development_cutoff_utc,
            rows_loaded=0,
            directional_rows=0,
            event_rows=0,
            cost_gated_event_rows=0,
            event_rate=0.0,
            split_boundaries={},
            development_candidate=None,
            fresh_oos_required=True,
            key_findings=[],
            blockers=["No multi-cycle replay rows were available."],
            warnings=[],
        )
        return report, EventOpportunityArtifacts()

    directional = prepare_event_rows(selected, config.event, time_scope="development")
    event_rows, diagnostics = build_event_opportunity_universe(selected, config.event, time_scope="development")
    labels = build_cost_aware_labels(event_rows, config.label)
    event_rate = float(len(labels) / max(1, len(directional)))
    warnings = [
        "Event detectors use entry-time replay fields only; replay proxies are not equivalent to full order-book events.",
        "Triple-Barrier labels use future outcome fields only after the event universe is frozen.",
    ]
    if labels.empty or len(labels) < config.minimum_train_events + config.minimum_optimize_events + config.minimum_holdout_events:
        report = EventOpportunityReport(
            status="INSUFFICIENT_EVENT_UNIVERSE",
            mode=MODE,
            version=VERSION,
            created_utc=created,
            selected_replay_window=selected_name,
            available_replay_windows=available,
            development_cutoff_utc=config.event.development_cutoff_utc,
            rows_loaded=int(len(selected)),
            directional_rows=int(len(directional)),
            event_rows=int(len(labels)),
            cost_gated_event_rows=int(labels.get("cost_gate_pass", pd.Series(dtype=bool)).sum()) if not labels.empty else 0,
            event_rate=event_rate,
            split_boundaries={},
            development_candidate=None,
            fresh_oos_required=True,
            key_findings=[],
            blockers=["The sparse event universe does not yet contain enough chronological events."],
            warnings=warnings,
        )
        artifacts = EventOpportunityArtifacts(
            event_universe=labels,
            event_overlap=event_overlap_table(event_rows),
            label_summary=_label_summary(labels),
            candidate_manifest={
                "status": report.status,
                "fresh_oos_required": True,
                "promotion_applied": False,
                "paper_live_enabled": False,
            },
        )
        return report, artifacts

    try:
        split = chronological_event_split(labels, config)
    except ValueError as exc:
        report = EventOpportunityReport(
            status="INSUFFICIENT_CHRONOLOGICAL_EVENTS",
            mode=MODE,
            version=VERSION,
            created_utc=created,
            selected_replay_window=selected_name,
            available_replay_windows=available,
            development_cutoff_utc=config.event.development_cutoff_utc,
            rows_loaded=int(len(selected)),
            directional_rows=int(len(directional)),
            event_rows=int(len(labels)),
            cost_gated_event_rows=int(labels["cost_gate_pass"].sum()),
            event_rate=event_rate,
            split_boundaries={},
            development_candidate=None,
            fresh_oos_required=True,
            key_findings=[],
            blockers=[str(exc)],
            warnings=warnings,
        )
        return report, EventOpportunityArtifacts(event_universe=labels)

    model: Optional[EventMetaModel] = None
    selection = MetaThresholdSelection(None, False, "Meta model was not fitted", [])
    optimize_predictions = split.optimize.copy()
    holdout_predictions = split.holdout.copy()
    selected_holdout = split.holdout.iloc[0:0].copy()
    coefficient_table = pd.DataFrame()
    model_error: Optional[str] = None
    try:
        model = fit_event_meta_model(split.train, config)
        optimize_predictions = predict_event_meta(model, split.optimize)
        selection = select_meta_threshold(optimize_predictions, config)
        holdout_predictions = predict_event_meta(model, split.holdout)
        selected_holdout = apply_meta_threshold(holdout_predictions, selection)
        coefficient_table = event_meta_coefficients(model)
    except ValueError as exc:
        model_error = str(exc)

    holdout_start = pd.Timestamp(split.boundaries["holdout_start_utc"])
    directional_holdout = directional[directional["__timestamp"] >= holdout_start].copy()
    holdout_records: List[Dict[str, Any]] = [_no_trade_record(len(directional_holdout))]
    holdout_records.append(
        _record("ALL_DIRECTIONAL", "SIMPLE_BASELINE", directional_holdout["__return"], len(directional_holdout), config)
    )
    score = (
        pd.to_numeric(directional_holdout["score"], errors="coerce")
        if "score" in directional_holdout.columns
        else pd.Series(np.nan, index=directional_holdout.index)
    )
    holdout_records.append(
        _record(
            "CHAMPION_SCORE_GE_70",
            "SIMPLE_BASELINE",
            directional_holdout.loc[score.ge(70), "__return"],
            len(directional_holdout),
            config,
        )
    )
    event_holdout_scopes = event_family_benchmarks(split.holdout, scope="HOLDOUT")
    if not event_holdout_scopes.empty:
        for _, row in event_holdout_scopes.iterrows():
            subset_name = str(row["strategy"])
            if subset_name == "EVENT_ANY":
                subset = split.holdout
            elif subset_name == "EVENT_COST_GATED":
                subset = split.holdout[split.holdout["cost_gate_pass"].astype(bool)]
            elif subset_name.endswith("_COST_GATED"):
                event_name = subset_name[len("EVENT_") : -len("_COST_GATED")]
                subset = split.holdout[
                    split.holdout["primary_event"].astype(str).eq(event_name)
                    & split.holdout["cost_gate_pass"].astype(bool)
                ]
            else:
                event_name = subset_name[len("EVENT_") :]
                subset = split.holdout[split.holdout["primary_event"].astype(str).eq(event_name)]
            holdout_records.append(
                _record(subset_name, "EVENT_BASELINE", subset["realized_net_return_pct"], len(directional_holdout), config)
            )

    meta_record = _record(
        "EVENT_META_LABEL_V2",
        "META_LABEL_MODEL",
        selected_holdout.get("realized_net_return_pct", pd.Series(dtype=float)),
        len(directional_holdout),
        config,
        selected_probability_threshold=selection.threshold,
        optimize_eligible=selection.eligible,
    )
    holdout_records.append(meta_record)
    holdout_table = pd.DataFrame(holdout_records).sort_values(
        ["expectancy", "profit_factor", "sample_count"], ascending=False
    ).reset_index(drop=True)

    walk = walk_forward_event_meta(labels, config)
    baseline_pool = holdout_table[
        ~holdout_table["strategy"].eq("EVENT_META_LABEL_V2")
        & holdout_table["sample_count"].ge(config.promotion_min_samples)
    ]
    best_baseline_expectancy = (
        float(baseline_pool["expectancy"].max()) if not baseline_pool.empty else 0.0
    )
    candidate_ok, candidate_blockers, wf_fraction = _fresh_candidate_eligible(
        meta_record, walk, config, best_baseline_expectancy=best_baseline_expectancy
    )
    if model_error:
        candidate_blockers.insert(0, f"Meta-label model was not fitted: {model_error}")
    if not selection.eligible:
        candidate_blockers.insert(0, selection.reason)
    candidate_ok = bool(candidate_ok and model is not None and selection.eligible)
    candidate_name = "EVENT_META_LABEL_V2" if candidate_ok else None

    event_counts = labels["primary_event"].value_counts()
    top_event = str(event_counts.index[0]) if not event_counts.empty else "NONE"
    top_event_rows = int(event_counts.iloc[0]) if not event_counts.empty else 0
    cost_gate_rate = float(labels["cost_gate_pass"].mean()) if not labels.empty else 0.0
    key_findings = [
        f"Sparse event detection retained {len(labels)} of {len(directional)} directional rows ({event_rate:.2%}).",
        f"The most common primary event was {top_event} with {top_event_rows} rows.",
        f"The pre-trade cost gate retained {int(labels['cost_gate_pass'].sum())} event rows ({cost_gate_rate:.2%}).",
        f"The fixed no-trade baseline has zero expectancy and zero drawdown; every tradable candidate must beat it after costs.",
        f"Meta-label Holdout selected n={meta_record['sample_count']}, expectancy={meta_record['expectancy']:.6f}% and PF={meta_record['profit_factor']}.",
        f"Walk-forward positive-fold fraction was {wf_fraction:.2%}.",
        f"Best adequately sampled non-meta Holdout baseline expectancy was {best_baseline_expectancy:.6f}%.",
    ]
    if diagnostics.multi_event_decisions:
        key_findings.append(
            f"{diagnostics.multi_event_decisions} decisions triggered multiple events; pre-declared priority prevented double counting."
        )
    if not candidate_ok:
        key_findings.append("No event/meta-label candidate is eligible for Fresh OOS freezing.")

    status = "COMPLETE_DEVELOPMENT_CANDIDATE_FROZEN" if candidate_ok else "COMPLETE_NO_DEVELOPMENT_CANDIDATE"
    manifest = {
        "version": VERSION,
        "status": status,
        "candidate": candidate_name,
        "selected_probability_threshold": selection.threshold,
        "development_cutoff_utc": config.event.development_cutoff_utc,
        "event_detection_uses_outcomes": False,
        "labels_are_cost_aware": True,
        "intrabar_policy": config.label.ambiguity_policy,
        "fresh_oos_required": True,
        "model_refit_on_fresh_oos_forbidden": True,
        "threshold_reselection_on_fresh_oos_forbidden": True,
        "promotion_applied": False,
        "paper_live_enabled": False,
        "blockers": candidate_blockers,
    }
    frozen_payload = None
    if candidate_ok and model is not None:
        frozen_payload = {
            "version": VERSION,
            "model": model,
            "selection": selection,
            "config": config,
            "development_cutoff_utc": config.event.development_cutoff_utc,
        }

    report = EventOpportunityReport(
        status=status,
        mode=MODE,
        version=VERSION,
        created_utc=created,
        selected_replay_window=selected_name,
        available_replay_windows=available,
        development_cutoff_utc=config.event.development_cutoff_utc,
        rows_loaded=int(len(selected)),
        directional_rows=int(len(directional)),
        event_rows=int(len(labels)),
        cost_gated_event_rows=int(labels["cost_gate_pass"].sum()),
        event_rate=event_rate,
        split_boundaries=split.boundaries,
        development_candidate=candidate_name,
        fresh_oos_required=True,
        key_findings=key_findings,
        blockers=candidate_blockers,
        warnings=warnings,
    )
    prediction_columns = [
        column
        for column in (
            "decision_id",
            "__timestamp",
            "symbol",
            "side",
            "regime",
            "primary_event",
            "cost_gate_pass",
            "triple_barrier_label",
            "realized_net_return_pct",
            "meta_label",
            "predicted_meta_probability",
            "predicted_event_ev_pct",
        )
        if column in holdout_predictions.columns
    ]
    artifacts = EventOpportunityArtifacts(
        event_universe=labels,
        event_overlap=event_overlap_table(event_rows),
        label_summary=_label_summary(labels),
        event_family_benchmarks=_family_scope_table(split, labels),
        holdout_benchmarks=holdout_table,
        threshold_candidates=_threshold_table(selection),
        model_coefficients=coefficient_table,
        walk_forward=walk,
        prediction_sample=holdout_predictions[prediction_columns].head(1000).copy(),
        candidate_manifest=manifest,
        frozen_candidate_payload=frozen_payload,
    )
    return report, artifacts


def write_event_opportunity_outputs(
    report: EventOpportunityReport,
    artifacts: EventOpportunityArtifacts,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files: Dict[str, str] = {}
    tables = {
        "event_universe": artifacts.event_universe,
        "event_overlap": artifacts.event_overlap,
        "cost_aware_label_summary": artifacts.label_summary,
        "event_family_benchmarks": artifacts.event_family_benchmarks,
        "holdout_benchmarks": artifacts.holdout_benchmarks,
        "meta_threshold_candidates": artifacts.threshold_candidates,
        "meta_model_coefficients": artifacts.model_coefficients,
        "walk_forward": artifacts.walk_forward,
        "prediction_sample": artifacts.prediction_sample,
    }
    for name, table in tables.items():
        path = output / f"{name}.csv"
        table.to_csv(path, index=False, encoding="utf-8-sig")
        files[name] = str(path)
    manifest_path = output / "frozen_event_candidate_manifest.json"
    manifest_path.write_text(json.dumps(_json_safe(artifacts.candidate_manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    files["candidate_manifest"] = str(manifest_path)
    if artifacts.frozen_candidate_payload is not None:
        model_path = output / "frozen_event_meta_candidate.joblib"
        joblib.dump(artifacts.frozen_candidate_payload, model_path)
        files["frozen_model"] = str(model_path)

    report.output_files = dict(files)
    json_path = output / "event_opportunity_v2_report.json"
    json_path.write_text(json.dumps(_json_safe(report.to_dict()), ensure_ascii=False, indent=2), encoding="utf-8")
    files["json"] = str(json_path)
    lines = [
        "# Freakto Event-Based Opportunity Universe & Cost-Aware Label v2",
        "",
        f"- Status: `{report.status}`",
        f"- Mode: `{report.mode}`",
        f"- Replay window: `{report.selected_replay_window}`",
        f"- Rows loaded/directional/events: `{report.rows_loaded} / {report.directional_rows} / {report.event_rows}`",
        f"- Cost-gated events: `{report.cost_gated_event_rows}`",
        f"- Development candidate: `{report.development_candidate}`",
        "- Promotion applied: `False`",
        "- Paper/Live enabled: `False`",
        "",
        "## Safety contract",
        "",
        "Events use entry-time fields only. Outcome fields are used only after event freezing to build conservative, cost-aware labels. "
        "Threshold selection is Optimize-only; Holdout is evaluated once. No result authorizes runtime promotion.",
        "",
        "## Key findings",
    ]
    lines.extend(f"- {item}" for item in report.key_findings)
    lines += ["", "## Blockers"]
    lines.extend(f"- {item}" for item in report.blockers)
    lines += ["", "## Warnings"]
    lines.extend(f"- {item}" for item in report.warnings)
    markdown_path = output / "event_opportunity_v2_report.md"
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    files["markdown"] = str(markdown_path)
    report.output_files = dict(files)
    json_path.write_text(json.dumps(_json_safe(report.to_dict()), ensure_ascii=False, indent=2), encoding="utf-8")
    return files
