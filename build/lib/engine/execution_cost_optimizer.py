"""Leakage-safe execution-cost and trade-geometry optimizer for Freakto.

Candidates are generated from entry-time geometry and selected on chronological
Train/Optimize data.  Untouched Holdout is used exactly once for the final audit.
The optimizer is research-only and never edits runtime weights, Paper, or Live.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from .exit_policy_audit import ExitPolicyAuditConfig, load_exit_audit_dataset
from .outcome_economics import fixed_horizon_return, return_metrics
from .trade_geometry import (
    VERSION as GEOMETRY_VERSION,
    GeometrySpec,
    candidate_pretrade_features,
    derive_geometry_features,
    geometry_filter_mask,
    simulate_geometry_returns,
)

VERSION = "v10.9.0"
DEFAULT_DATASET = Path("logs/market_replay/market_replay_evaluations.csv")
DEFAULT_OUTPUT_DIR = Path("logs/execution_geometry")


@dataclass(frozen=True)
class ExecutionGeometryConfig:
    horizons: tuple[int, ...] = (6, 12)
    stop_multipliers: tuple[float, ...] = (0.75, 1.0, 1.25)
    reward_risks: tuple[float, ...] = (1.0, 1.5, 2.0, 3.0)
    minimum_target_cost_multiples: tuple[float, ...] = (2.0, 3.0, 4.0)
    maximum_cost_to_risks: tuple[float, ...] = (0.30, 0.50)
    minimum_net_reward_risks: tuple[float, ...] = (0.75,)
    minimum_scores: tuple[int, ...] = (0, 70)
    scopes: tuple[str, ...] = ("ALL", "LONG", "SHORT")
    management_policies: tuple[str, ...] = ("NONE", "BREAK_EVEN", "TRAILING")
    management_shortlist: int = 12
    path_assumption: str = "STOP_FIRST"
    train_fraction: float = 0.50
    optimize_fraction: float = 0.25
    purge_candles: int = 12
    minimum_total_rows: int = 1000
    minimum_train_rows: int = 300
    minimum_optimize_rows: int = 150
    minimum_holdout_rows: int = 150
    minimum_expectancy_pct: float = 0.0
    minimum_profit_factor: float = 1.05
    minimum_walk_forward_pass_rate: float = 2 / 3
    walk_forward_folds: int = 3
    maximum_candidate_drawdown_multiple: float = 1.10
    canonical_horizon: int = 6
    top_candidates_to_holdout: int = 1
    allow_path_sensitive_promotion: bool = False

    def validate(self) -> None:
        if not 0 < self.train_fraction < 1 or not 0 < self.optimize_fraction < 1:
            raise ValueError("train_fraction and optimize_fraction must be in (0, 1).")
        if self.train_fraction + self.optimize_fraction >= 1:
            raise ValueError("Train plus Optimize must leave a Holdout partition.")
        if self.purge_candles < max(self.horizons):
            raise ValueError("purge_candles must be at least the maximum evaluated horizon.")
        if self.walk_forward_folds < 2:
            raise ValueError("walk_forward_folds must be at least 2.")
        if self.top_candidates_to_holdout != 1:
            raise ValueError("Exactly one Optimize-selected candidate may be audited on Holdout.")
        if self.path_assumption != "STOP_FIRST":
            raise ValueError("Promotion optimizer must use conservative STOP_FIRST path assumption.")
        if any(value <= 0 for value in self.stop_multipliers + self.reward_risks):
            raise ValueError("Geometry multipliers must be positive.")
        if any(scope not in {"ALL", "LONG", "SHORT"} for scope in self.scopes):
            raise ValueError("Unsupported scope.")


@dataclass(frozen=True)
class CandidateSpec:
    scope: str
    minimum_score: int
    minimum_target_cost_multiple: float
    maximum_cost_to_risk: float
    minimum_net_reward_risk: float
    geometry: GeometrySpec

    @property
    def candidate_id(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["geometry"] = self.geometry.to_dict()
        return payload


@dataclass
class ExecutionGeometryArtifacts:
    candidate_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    holdout_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    walk_forward: pd.DataFrame = field(default_factory=pd.DataFrame)
    cost_sensitivity: pd.DataFrame = field(default_factory=pd.DataFrame)
    shadow_predictions: pd.DataFrame = field(default_factory=pd.DataFrame)


@dataclass
class ExecutionGeometryResult:
    created_utc: str
    version: str
    geometry_version: str
    status: str
    mode: str
    dataset_path: str
    dataset_sha256: str
    selected_run_id: Optional[str]
    rows_loaded: int
    rows_usable: int
    split_summary: dict
    canonical_metrics: dict
    selected_candidate: Optional[dict]
    holdout_metrics: dict
    recommended_policy: Optional[dict]
    promotion_applied: bool = False
    paper_live_enabled: bool = False
    key_findings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    output_files: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def chronological_split(frame: pd.DataFrame, config: ExecutionGeometryConfig) -> tuple[dict[str, pd.Series], dict]:
    """Split by unique event timestamp and purge full outcome horizons."""

    config.validate()
    times = pd.Index(frame["_event_time"].drop_duplicates().sort_values())
    if len(times) < 20:
        raise ValueError("Not enough unique timestamps for chronological split.")
    train_end = int(len(times) * config.train_fraction)
    optimize_end = int(len(times) * (config.train_fraction + config.optimize_fraction))
    purge = int(config.purge_candles)
    train_times = times[: max(0, train_end - purge)]
    optimize_times = times[min(len(times), train_end + purge): max(0, optimize_end - purge)]
    holdout_times = times[min(len(times), optimize_end + purge):]
    if len(train_times) == 0 or len(optimize_times) == 0 or len(holdout_times) == 0:
        raise ValueError("Chronological split became empty after purge.")
    masks = {
        "TRAIN": frame["_event_time"].isin(train_times),
        "OPTIMIZE": frame["_event_time"].isin(optimize_times),
        "HOLDOUT": frame["_event_time"].isin(holdout_times),
    }
    summary = {
        name.lower(): {
            "rows": int(mask.sum()),
            "unique_timestamps": int(frame.loc[mask, "_event_time"].nunique()),
            "start": str(frame.loc[mask, "_event_time"].min()),
            "end": str(frame.loc[mask, "_event_time"].max()),
        }
        for name, mask in masks.items()
    }
    summary["purge_candles"] = purge
    return masks, summary


def generate_candidates(
    config: ExecutionGeometryConfig,
    *,
    management_policies: Optional[tuple[str, ...]] = None,
) -> Iterable[CandidateSpec]:
    policies = management_policies or config.management_policies
    for horizon in config.horizons:
        for stop_multiplier in config.stop_multipliers:
            for reward_risk in config.reward_risks:
                for management in policies:
                    geometry = GeometrySpec(
                        horizon_candles=horizon,
                        stop_multiplier=stop_multiplier,
                        reward_risk=reward_risk,
                        management_policy=management,
                        path_assumption=config.path_assumption,
                    )
                    for scope in config.scopes:
                        for minimum_score in config.minimum_scores:
                            for target_cost_multiple in config.minimum_target_cost_multiples:
                                for maximum_cost_to_risk in config.maximum_cost_to_risks:
                                    for minimum_net_rr in config.minimum_net_reward_risks:
                                        yield CandidateSpec(
                                            scope=scope,
                                            minimum_score=minimum_score,
                                            minimum_target_cost_multiple=target_cost_multiple,
                                            maximum_cost_to_risk=maximum_cost_to_risk,
                                            minimum_net_reward_risk=minimum_net_rr,
                                            geometry=geometry,
                                        )


def _scope_score_mask(frame: pd.DataFrame, candidate: CandidateSpec) -> pd.Series:
    side = frame["side"].astype(str).str.upper()
    scope_mask = pd.Series(True, index=frame.index)
    if candidate.scope in {"LONG", "SHORT"}:
        scope_mask = side.eq(candidate.scope)
    score = pd.to_numeric(frame.get("score"), errors="coerce").fillna(-math.inf)
    return scope_mask & score.ge(candidate.minimum_score)


def candidate_mask(frame: pd.DataFrame, candidate: CandidateSpec, pretrade: pd.DataFrame) -> pd.Series:
    return _scope_score_mask(frame, candidate) & geometry_filter_mask(
        pretrade,
        minimum_target_cost_multiple=candidate.minimum_target_cost_multiple,
        maximum_cost_to_risk=candidate.maximum_cost_to_risk,
        minimum_net_reward_risk=candidate.minimum_net_reward_risk,
    )


def _candidate_metrics(
    returns: pd.Series,
    base_mask: pd.Series,
    split_mask: pd.Series,
) -> dict:
    selected = returns.loc[base_mask & split_mask]
    metrics = return_metrics(selected)
    eligible_rows = int((base_mask & split_mask).sum())
    return {
        **metrics.to_dict(),
        "eligible_rows": eligible_rows,
        "coverage": round(metrics.sample_count / max(1, int(split_mask.sum())), 6),
    }


def _walk_forward_rows(
    frame: pd.DataFrame,
    returns: pd.Series,
    base_mask: pd.Series,
    development_mask: pd.Series,
    candidate_id: str,
    config: ExecutionGeometryConfig,
) -> list[dict]:
    times = pd.Index(frame.loc[development_mask, "_event_time"].drop_duplicates().sort_values())
    folds = np.array_split(times.to_numpy(), config.walk_forward_folds)
    rows: list[dict] = []
    for index, fold_times in enumerate(folds, start=1):
        fold_mask = development_mask & frame["_event_time"].isin(fold_times)
        metrics = _candidate_metrics(returns, base_mask, fold_mask)
        passed = (
            metrics["sample_count"] >= max(30, config.minimum_optimize_rows // config.walk_forward_folds)
            and metrics["expectancy"] > config.minimum_expectancy_pct
            and metrics["profit_factor"] >= config.minimum_profit_factor
        )
        rows.append({
            "candidate_id": candidate_id,
            "fold": index,
            "start": str(frame.loc[fold_mask, "_event_time"].min()),
            "end": str(frame.loc[fold_mask, "_event_time"].max()),
            **metrics,
            "passed": bool(passed),
        })
    return rows


def _selection_score(metrics: dict, walk_forward_pass_rate: float) -> float:
    if metrics["sample_count"] <= 0:
        return -math.inf
    drawdown_penalty = abs(min(0.0, float(metrics["max_drawdown"]))) / max(1.0, metrics["sample_count"])
    return (
        float(metrics["expectancy"])
        + 0.10 * max(0.0, float(metrics["profit_factor"]) - 1.0)
        + 0.05 * walk_forward_pass_rate
        - 0.05 * drawdown_penalty
    )


def _candidate_cache_key(candidate: CandidateSpec) -> tuple:
    spec = candidate.geometry
    return (
        spec.horizon_candles,
        spec.stop_multiplier,
        spec.reward_risk,
        spec.management_policy,
        spec.break_even_trigger_r,
        spec.trailing_trigger_r,
        spec.trailing_distance_r,
        spec.path_assumption,
        spec.cost_multiplier,
    )


def optimize_execution_geometry(
    frame: pd.DataFrame,
    config: ExecutionGeometryConfig,
) -> tuple[Optional[CandidateSpec], ExecutionGeometryArtifacts, dict]:
    """Select one candidate on Train/Optimize without reading Holdout outcomes.

    Search is intentionally staged. Fixed geometry is evaluated exhaustively
    first; break-even and trailing variants are then tested only around the best
    development candidates. This avoids an unnecessary Cartesian explosion while
    preserving full coverage of the actual entry gates and base geometries.
    """

    config.validate()
    enriched = frame if "_risk_unit_pct" in frame.columns else derive_geometry_features(frame)
    splits, split_summary = chronological_split(enriched, config)
    development_mask = splits["TRAIN"] | splits["OPTIMIZE"]
    candidate_rows: list[dict] = []
    walk_rows: list[dict] = []
    cache: dict[tuple, tuple[pd.Series, pd.DataFrame, dict]] = {}
    evaluated_specs: dict[str, CandidateSpec] = {}

    selected: Optional[CandidateSpec] = None
    selected_score = -math.inf

    def evaluate(candidate: CandidateSpec) -> tuple[bool, float]:
        nonlocal selected, selected_score
        if candidate.candidate_id in evaluated_specs:
            return False, -math.inf
        evaluated_specs[candidate.candidate_id] = candidate
        key = _candidate_cache_key(candidate)
        if key not in cache:
            returns, diagnostics, detail = simulate_geometry_returns(enriched, candidate.geometry)
            pretrade = detail[[
                "valid_geometry", "target_cost_multiple", "cost_to_risk", "net_reward_risk",
            ]].copy()
            cache[key] = (returns, pretrade, diagnostics.to_dict())
        returns, pretrade, diagnostics = cache[key]
        mask = candidate_mask(enriched, candidate, pretrade)
        train_metrics = _candidate_metrics(returns, mask, splits["TRAIN"])
        optimize_metrics = _candidate_metrics(returns, mask, splits["OPTIMIZE"])
        if train_metrics["sample_count"] < config.minimum_train_rows:
            return False, -math.inf
        if optimize_metrics["sample_count"] < config.minimum_optimize_rows:
            return False, -math.inf
        wf_rows = _walk_forward_rows(
            enriched, returns, mask, development_mask, candidate.candidate_id, config
        )
        pass_rate = sum(bool(row["passed"]) for row in wf_rows) / len(wf_rows)
        train_pass = (
            train_metrics["expectancy"] > config.minimum_expectancy_pct
            and train_metrics["profit_factor"] >= 1.0
        )
        optimize_pass = (
            optimize_metrics["expectancy"] > config.minimum_expectancy_pct
            and optimize_metrics["profit_factor"] >= config.minimum_profit_factor
        )
        stable = pass_rate >= config.minimum_walk_forward_pass_rate
        score = _selection_score(optimize_metrics, pass_rate)
        eligible = bool(train_pass and optimize_pass and stable)
        candidate_rows.append({
            "candidate_id": candidate.candidate_id,
            **candidate.to_dict(),
            "train_metrics": train_metrics,
            "optimize_metrics": optimize_metrics,
            "walk_forward_pass_rate": round(pass_rate, 6),
            "selection_score": round(score, 6) if math.isfinite(score) else None,
            "development_eligible": eligible,
            "path_promotion_eligible": bool(
                candidate.geometry.management_policy == "NONE" or config.allow_path_sensitive_promotion
            ),
            "diagnostics": diagnostics,
        })
        walk_rows.extend(wf_rows)
        if eligible and score > selected_score:
            selected = candidate
            selected_score = score
        return eligible, score

    # Stage 1: exhaustive base geometry with no path-sensitive management.
    base_scored: list[tuple[float, CandidateSpec]] = []
    for candidate in generate_candidates(config, management_policies=("NONE",)):
        _, score = evaluate(candidate)
        if math.isfinite(score):
            base_scored.append((score, candidate))

    # Stage 2: management overlays only around strongest development candidates.
    if any(policy != "NONE" for policy in config.management_policies):
        base_scored.sort(key=lambda item: item[0], reverse=True)
        shortlist = base_scored[: max(0, int(config.management_shortlist))]
        for _, base in shortlist:
            for management in config.management_policies:
                if management == "NONE":
                    continue
                geometry = GeometrySpec(**{**base.geometry.to_dict(), "management_policy": management})
                managed = CandidateSpec(
                    scope=base.scope,
                    minimum_score=base.minimum_score,
                    minimum_target_cost_multiple=base.minimum_target_cost_multiple,
                    maximum_cost_to_risk=base.maximum_cost_to_risk,
                    minimum_net_reward_risk=base.minimum_net_reward_risk,
                    geometry=geometry,
                )
                evaluate(managed)

    artifacts = ExecutionGeometryArtifacts(
        candidate_summary=pd.json_normalize(candidate_rows),
        walk_forward=pd.DataFrame(walk_rows),
    )
    base_generated = sum(1 for _ in generate_candidates(config, management_policies=("NONE",)))
    diagnostics = {
        "split_summary": split_summary,
        "generated_base_candidates": base_generated,
        "management_shortlist": int(config.management_shortlist),
        "evaluated_candidates": len(candidate_rows),
        "development_eligible_candidates": int(
            artifacts.candidate_summary.get("development_eligible", pd.Series(dtype=bool)).fillna(False).sum()
        ) if not artifacts.candidate_summary.empty else 0,
    }
    return selected, artifacts, diagnostics

def _cost_sensitivity_rows(
    frame: pd.DataFrame,
    candidate: CandidateSpec,
    base_filter: CandidateSpec,
    holdout_mask: pd.Series,
) -> list[dict]:
    rows: list[dict] = []
    for multiplier in (0.50, 0.75, 1.0, 1.25, 1.50):
        spec = GeometrySpec(**{**candidate.geometry.to_dict(), "cost_multiplier": multiplier})
        returns, _, detail = simulate_geometry_returns(frame, spec)
        pretrade = detail[["valid_geometry", "target_cost_multiple", "cost_to_risk", "net_reward_risk"]]
        adjusted = CandidateSpec(
            scope=base_filter.scope,
            minimum_score=base_filter.minimum_score,
            minimum_target_cost_multiple=base_filter.minimum_target_cost_multiple,
            maximum_cost_to_risk=base_filter.maximum_cost_to_risk,
            minimum_net_reward_risk=base_filter.minimum_net_reward_risk,
            geometry=spec,
        )
        mask = candidate_mask(frame, adjusted, pretrade)
        metrics = _candidate_metrics(returns, mask, holdout_mask)
        rows.append({"cost_multiplier": multiplier, **metrics})
    return rows


def _render_markdown(result: ExecutionGeometryResult, artifacts: ExecutionGeometryArtifacts) -> str:
    lines = [
        "# Freakto Execution Cost & Trade Geometry Optimizer",
        "",
        f"- Status: **{result.status}**",
        f"- Mode: `{result.mode}`",
        f"- Selected replay run: `{result.selected_run_id}`",
        f"- Rows loaded/usable: `{result.rows_loaded} / {result.rows_usable}`",
        f"- Promotion applied: `{result.promotion_applied}`",
        "",
        "## Canonical Holdout",
        "",
        f"```json\n{json.dumps(result.canonical_metrics, indent=2)}\n```",
        "",
        "## Selected Candidate",
        "",
        f"```json\n{json.dumps(result.selected_candidate, indent=2)}\n```",
        "",
        "## Candidate Holdout",
        "",
        f"```json\n{json.dumps(result.holdout_metrics, indent=2)}\n```",
        "",
        "## Key findings",
    ]
    lines.extend(f"- {item}" for item in result.key_findings)
    lines.extend(["", "## Blockers"])
    lines.extend(f"- {item}" for item in result.blockers)
    lines.extend([
        "",
        "## Safety",
        "",
        "This tool is research-only. It does not modify runtime score weights, canonical labels, Paper, or Live settings.",
    ])
    return "\n".join(lines) + "\n"


def run_execution_geometry_optimizer(
    dataset_path: Path | str = DEFAULT_DATASET,
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    run_id: Optional[str] = None,
    config: ExecutionGeometryConfig = ExecutionGeometryConfig(),
) -> tuple[ExecutionGeometryResult, ExecutionGeometryArtifacts]:
    config.validate()
    source = Path(dataset_path)
    audit_config = ExitPolicyAuditConfig(
        horizons=(1, 3, 6, 12),
        minimum_total_rows=config.minimum_total_rows,
        minimum_policy_rows=min(config.minimum_optimize_rows, 100),
    )
    frame, metadata, warnings = load_exit_audit_dataset(
        source, run_id=run_id, latest_run_only=True, config=audit_config
    )
    frame = derive_geometry_features(frame)
    selected, artifacts, diagnostics = optimize_execution_geometry(frame, config)
    splits, split_summary = chronological_split(frame, config)

    canonical_returns = fixed_horizon_return(frame, config.canonical_horizon, net=True)
    canonical_metrics = return_metrics(canonical_returns.loc[splits["HOLDOUT"]]).to_dict()
    selected_payload: Optional[dict] = None
    holdout_metrics: dict = return_metrics([]).to_dict()
    recommended: Optional[dict] = None
    blockers: list[str] = []
    key_findings: list[str] = []

    if selected is None:
        blockers.append("No cost/geometry candidate preserved positive Train and Optimize edge with walk-forward stability.")
    else:
        selected_payload = {"candidate_id": selected.candidate_id, **selected.to_dict()}
        returns, geometry_diagnostics, detail = simulate_geometry_returns(frame, selected.geometry)
        pretrade = detail[["valid_geometry", "target_cost_multiple", "cost_to_risk", "net_reward_risk"]]
        mask = candidate_mask(frame, selected, pretrade)
        holdout_metrics = _candidate_metrics(returns, mask, splits["HOLDOUT"])
        candidate_drawdown_ok = abs(min(0.0, holdout_metrics["max_drawdown"])) <= (
            abs(min(0.0, canonical_metrics["max_drawdown"])) * config.maximum_candidate_drawdown_multiple
            + 1e-12
        )
        path_promotion_eligible = bool(
            selected.geometry.management_policy == "NONE" or config.allow_path_sensitive_promotion
        )
        holdout_pass = (
            holdout_metrics["sample_count"] >= config.minimum_holdout_rows
            and holdout_metrics["expectancy"] > config.minimum_expectancy_pct
            and holdout_metrics["profit_factor"] >= config.minimum_profit_factor
            and candidate_drawdown_ok
            and path_promotion_eligible
        )
        artifacts.holdout_summary = pd.DataFrame([{
            "candidate_id": selected.candidate_id,
            **holdout_metrics,
            "candidate_drawdown_ok": candidate_drawdown_ok,
            "path_promotion_eligible": path_promotion_eligible,
            "holdout_pass": holdout_pass,
            **geometry_diagnostics.to_dict(),
        }])
        shadow = frame.loc[splits["HOLDOUT"], [
            column for column in ("decision_id", "candle_timestamp", "symbol", "side", "score", "regime_label")
            if column in frame.columns
        ]].copy()
        shadow["selected_by_candidate"] = mask.loc[splits["HOLDOUT"]].to_numpy()
        shadow["simulated_net_return_pct"] = returns.loc[splits["HOLDOUT"]].to_numpy()
        artifacts.shadow_predictions = shadow
        artifacts.cost_sensitivity = pd.DataFrame(
            _cost_sensitivity_rows(frame, selected, selected, splits["HOLDOUT"])
        )
        if holdout_pass:
            recommended = selected_payload
        else:
            blockers.append("The Optimize-selected candidate failed untouched Holdout promotion constraints.")
            if not path_promotion_eligible:
                blockers.append(
                    "The selected break-even/trailing policy is diagnostic-only because aggregate MFE/MAE does not preserve full path order."
                )

    native_atr_rate = float(frame["_risk_unit_source"].astype(str).str.startswith("ATR:").mean())
    mean_cost = float(pd.to_numeric(frame["_execution_cost_pct"], errors="coerce").mean())
    mean_risk = float(pd.to_numeric(frame["_risk_unit_pct"], errors="coerce").mean())
    key_findings.append(
        f"Mean recorded round-trip cost was {mean_cost:.6f}% versus mean baseline risk unit {mean_risk:.6f}%."
    )
    if native_atr_rate == 0:
        key_findings.append(
            "No native ATR percentage column was present; planned stop distance was used as the explicit risk-unit proxy."
        )
    else:
        key_findings.append(f"Native ATR geometry coverage was {native_atr_rate:.2%}.")
    key_findings.append(
        "Cost-to-target, cost-to-risk, net reward/risk, side, and score gates use entry-time fields only."
    )
    key_findings.append(
        "Break-even and trailing candidates use conservative STOP_FIRST ordering; optimistic path assumptions are not promotion eligible."
    )
    if not artifacts.candidate_summary.empty:
        fixed_rows = artifacts.candidate_summary[
            artifacts.candidate_summary.get("geometry.management_policy", pd.Series(index=artifacts.candidate_summary.index, dtype=object)).eq("NONE")
        ]
        fixed_eligible = int(fixed_rows.get("development_eligible", pd.Series(dtype=bool)).fillna(False).sum())
        managed_rows = artifacts.candidate_summary[
            ~artifacts.candidate_summary.get("geometry.management_policy", pd.Series(index=artifacts.candidate_summary.index, dtype=object)).eq("NONE")
        ]
        managed_eligible = int(managed_rows.get("development_eligible", pd.Series(dtype=bool)).fillna(False).sum())
        key_findings.append(
            f"Development eligibility: fixed geometry={fixed_eligible}, path-managed diagnostics={managed_eligible}."
        )

    if selected is None:
        key_findings.append(
            f"Evaluated {diagnostics['evaluated_candidates']} sufficiently sampled staged candidates; none survived development selection."
        )
    else:
        key_findings.append(
            f"One candidate was selected on development data and audited once on Holdout: {selected.candidate_id}."
        )
        key_findings.append(
            f"The selected gate retained {holdout_metrics.get('coverage', 0):.2%} of Holdout rows and produced "
            f"{holdout_metrics.get('expectancy', 0):.6f}% expectancy with PF {holdout_metrics.get('profit_factor', 0):.6f}."
        )
        if not artifacts.cost_sensitivity.empty:
            half_cost = artifacts.cost_sensitivity.loc[
                artifacts.cost_sensitivity['cost_multiplier'].eq(0.50)
            ]
            if not half_cost.empty:
                row = half_cost.iloc[0]
                key_findings.append(
                    f"At 50% of recorded execution cost, selected-candidate Holdout expectancy remained "
                    f"{float(row['expectancy']):.6f}% with PF {float(row['profit_factor']):.6f}."
                )
    if recommended is None:
        key_findings.append("No runtime geometry or execution-cost policy is recommended for promotion.")

    status = "PASS" if recommended is not None else "FAIL"
    result = ExecutionGeometryResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        version=VERSION,
        geometry_version=GEOMETRY_VERSION,
        status=status,
        mode="RESEARCH_OPTIMIZATION_ONLY",
        dataset_path=str(source),
        dataset_sha256=_sha256(source),
        selected_run_id=metadata.get("selected_run_id"),
        rows_loaded=int(metadata.get("rows_loaded", 0)),
        rows_usable=int(metadata.get("rows_usable", len(frame))),
        split_summary=split_summary,
        canonical_metrics=canonical_metrics,
        selected_candidate=selected_payload,
        holdout_metrics=holdout_metrics,
        recommended_policy=recommended,
        key_findings=key_findings,
        blockers=blockers,
        warnings=warnings,
    )

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "report_json": output / "execution_geometry_report.json",
        "report_markdown": output / "execution_geometry_report.md",
        "candidate_summary_csv": output / "execution_geometry_candidates.csv",
        "walk_forward_csv": output / "execution_geometry_walk_forward.csv",
        "holdout_summary_csv": output / "execution_geometry_holdout.csv",
        "cost_sensitivity_csv": output / "execution_cost_sensitivity.csv",
        "shadow_predictions_csv": output / "execution_geometry_shadow_predictions.csv",
    }
    result.output_files = {key: str(path) for key, path in paths.items()}
    artifacts.candidate_summary.to_csv(paths["candidate_summary_csv"], index=False)
    artifacts.walk_forward.to_csv(paths["walk_forward_csv"], index=False)
    artifacts.holdout_summary.to_csv(paths["holdout_summary_csv"], index=False)
    artifacts.cost_sensitivity.to_csv(paths["cost_sensitivity_csv"], index=False)
    artifacts.shadow_predictions.to_csv(paths["shadow_predictions_csv"], index=False)
    paths["report_json"].write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    paths["report_markdown"].write_text(_render_markdown(result, artifacts), encoding="utf-8")
    return result, artifacts
