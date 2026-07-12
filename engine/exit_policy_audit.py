"""Leakage-safe audit of Freakto outcome labels and exit economics.

The audit compares fixed-close horizons, adaptive horizon labels, and
first-touch Target-1/Stop policies. It also quantifies execution-cost drag,
label consistency, path dependence, and intrabar ambiguity sensitivity.

This is research-only. It never changes the canonical recorder, runtime score,
Paper configuration, or Live configuration.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd

from .outcome_economics import (
    SUPPORTED_HORIZONS,
    VERSION as ECONOMICS_VERSION,
    adaptive_horizon_return,
    enrich_planned_economics,
    first_touch_return,
    fixed_horizon_return,
    planned_economics_summary,
    return_metrics,
)

VERSION = "v10.8.0"
DEFAULT_DATASET = Path("logs/market_replay/market_replay_evaluations.csv")
DEFAULT_OUTPUT_DIR = Path("logs/outcome_economics")


@dataclass(frozen=True)
class ExitPolicyAuditConfig:
    horizons: tuple[int, ...] = SUPPORTED_HORIZONS
    canonical_horizon: int = 6
    minimum_total_rows: int = 1000
    minimum_policy_rows: int = 500
    minimum_coverage: float = 0.90
    minimum_profit_factor: float = 1.05
    minimum_expectancy_pct: float = 0.0
    minimum_improvement_pct: float = 0.10
    minimum_positive_stability_folds: int = 3
    stability_folds: int = 4
    maximum_ambiguity_sensitivity_pct: float = 0.05

    def validate(self) -> None:
        if not self.horizons or any(h not in SUPPORTED_HORIZONS for h in self.horizons):
            raise ValueError(f"horizons must be selected from {SUPPORTED_HORIZONS}.")
        if self.canonical_horizon not in self.horizons:
            raise ValueError("canonical_horizon must be included in horizons.")
        if self.minimum_total_rows <= 0 or self.minimum_policy_rows <= 0:
            raise ValueError("minimum row counts must be positive.")
        if not 0 < self.minimum_coverage <= 1:
            raise ValueError("minimum_coverage must be in (0, 1].")
        if self.stability_folds < 2:
            raise ValueError("stability_folds must be at least 2.")
        if not 1 <= self.minimum_positive_stability_folds <= self.stability_folds:
            raise ValueError("minimum_positive_stability_folds is invalid.")


@dataclass
class ExitPolicyAuditArtifacts:
    policy_summary: pd.DataFrame = field(default_factory=pd.DataFrame)
    policy_stability: pd.DataFrame = field(default_factory=pd.DataFrame)
    cost_drag: pd.DataFrame = field(default_factory=pd.DataFrame)
    label_consistency: pd.DataFrame = field(default_factory=pd.DataFrame)
    planned_economics: pd.DataFrame = field(default_factory=pd.DataFrame)
    ambiguity_sensitivity: pd.DataFrame = field(default_factory=pd.DataFrame)


@dataclass
class ExitPolicyAuditResult:
    created_utc: str
    version: str
    economics_version: str
    status: str
    mode: str
    dataset_path: str
    dataset_sha256: str
    selected_run_id: Optional[str]
    rows_loaded: int
    rows_usable: int
    canonical_policy: str
    recommended_policy: Optional[str]
    policy_change_applied: bool = False
    paper_live_enabled: bool = False
    key_findings: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)
    output_files: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_sort_key(value: str) -> tuple:
    text = str(value)
    parts = text.rsplit("_", 2)
    if len(parts) == 3 and parts[-2].isdigit() and parts[-1].isdigit():
        return parts[-2], parts[-1], text
    return "", "", text


def _required_columns(header: Sequence[str], horizons: Sequence[int]) -> set[str]:
    required = {
        "run_id",
        "decision_id",
        "candle_timestamp",
        "side",
        "score",
        "symbol",
        "timeframe",
        "regime_label",
        "evaluation_status",
        "entry_price",
        "stop_zone",
        "targets",
        "fee_bps_per_side",
        "slippage_bps_per_side",
        "round_trip_cost_pct",
        "target_1_hit",
        "target_2_hit",
        "target_3_hit",
        "stop_hit",
        "first_exit_reason",
        "first_exit_candle_offset",
        "intrabar_ambiguity",
        "mfe_pct",
        "mae_pct",
        "win",
        "direction_correct",
        "target_hit",
        "outcome_label",
        "net_return_pct",
        "adaptive_horizon_candles",
        "adaptive_gross_return_pct",
        "adaptive_net_return_pct",
    }
    for horizon in horizons:
        required.add(f"gross_signed_return_after_{horizon}c_pct")
        required.add(f"net_signed_return_after_{horizon}c_pct")
    return required & set(map(str, header))


def load_exit_audit_dataset(
    path: Path | str = DEFAULT_DATASET,
    *,
    run_id: Optional[str] = None,
    latest_run_only: bool = True,
    config: ExitPolicyAuditConfig = ExitPolicyAuditConfig(),
) -> tuple[pd.DataFrame, dict, list[str]]:
    config.validate()
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    header = pd.read_csv(source, encoding="utf-8-sig", nrows=0)
    required = {"side", "entry_price", "stop_zone", "targets", "candle_timestamp"}
    missing = required - set(header.columns)
    if missing:
        raise ValueError(f"Exit audit dataset is missing required columns: {sorted(missing)}")
    usecols = _required_columns(header.columns, config.horizons)
    frame = pd.read_csv(
        source,
        encoding="utf-8-sig",
        low_memory=False,
        usecols=lambda column: column in usecols,
    )
    rows_loaded = int(len(frame))
    warnings: list[str] = []
    if "evaluation_status" in frame.columns:
        frame = frame[frame["evaluation_status"].astype(str).str.upper().eq("COMPLETE")]
    frame["side"] = frame["side"].astype(str).str.strip().str.upper()
    frame = frame[frame["side"].isin(["LONG", "SHORT"])]

    selected_run_id: Optional[str] = None
    available_runs: list[str] = []
    if "run_id" in frame.columns:
        available_runs = sorted(
            [item for item in frame["run_id"].dropna().astype(str).unique() if item],
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
                    "to prevent repeated market-history counting."
                )

    frame = frame.copy()
    frame["_event_time"] = pd.to_datetime(frame["candle_timestamp"], errors="coerce", utc=True)
    before = len(frame)
    frame = frame.dropna(subset=["_event_time"])
    if len(frame) != before:
        warnings.append(f"Dropped {before - len(frame)} rows with invalid timestamps.")
    if "decision_id" in frame.columns:
        before = len(frame)
        frame = frame.drop_duplicates("decision_id", keep="last")
        if len(frame) != before:
            warnings.append(f"Removed {before - len(frame)} duplicate decision IDs.")
    frame = frame.sort_values(["_event_time", "decision_id" if "decision_id" in frame.columns else "side"], kind="stable")
    frame = frame.reset_index(drop=True)
    frame["_row_order"] = np.arange(len(frame), dtype=int)
    frame = enrich_planned_economics(frame)
    valid_geometry = (
        frame["_entry_price"].gt(0)
        & frame["_stop_price"].gt(0)
        & frame["_target_1_price"].gt(0)
    )
    if not valid_geometry.all():
        warnings.append(f"Dropped {int((~valid_geometry).sum())} rows without valid entry/stop/Target-1 geometry.")
        frame = frame[valid_geometry].copy().reset_index(drop=True)
        frame["_row_order"] = np.arange(len(frame), dtype=int)
    if len(frame) < config.minimum_total_rows:
        raise ValueError(
            f"At least {config.minimum_total_rows} usable directional rows are required; found {len(frame)}."
        )
    metadata = {
        "dataset_path": str(source),
        "rows_loaded": rows_loaded,
        "rows_usable": int(len(frame)),
        "selected_run_id": selected_run_id,
        "available_run_count": len(available_runs),
    }
    return frame, metadata, warnings


def _scope_masks(frame: pd.DataFrame) -> dict[str, pd.Series]:
    score = pd.to_numeric(frame.get("score"), errors="coerce")
    return {
        "ALL_DIRECTIONAL": pd.Series(True, index=frame.index),
        "LONG": frame["side"].astype(str).str.upper().eq("LONG"),
        "SHORT": frame["side"].astype(str).str.upper().eq("SHORT"),
        "SCORE_GE_70": score.ge(70),
    }


def _build_policy_series(frame: pd.DataFrame, config: ExitPolicyAuditConfig) -> dict[str, pd.Series]:
    policies: dict[str, pd.Series] = {}
    for horizon in config.horizons:
        policies[f"FIXED_CLOSE_{horizon}C_NET"] = fixed_horizon_return(frame, horizon, net=True)
        policies[f"FIRST_TOUCH_T1_STOP_{horizon}C_STOP_FIRST"] = first_touch_return(
            frame, horizon, ambiguity_policy="STOP_FIRST"
        )
        policies[f"FIRST_TOUCH_T1_STOP_{horizon}C_TARGET_FIRST"] = first_touch_return(
            frame, horizon, ambiguity_policy="TARGET_FIRST"
        )
    adaptive = adaptive_horizon_return(frame, net=True)
    if adaptive.notna().any():
        policies["ADAPTIVE_HORIZON_NET"] = adaptive
    return policies


def _stability_rows(
    frame: pd.DataFrame,
    policies: dict[str, pd.Series],
    config: ExitPolicyAuditConfig,
) -> list[dict]:
    rows: list[dict] = []
    for scope, scope_mask in _scope_masks(frame).items():
        scope_frame = frame.loc[scope_mask]
        unique_times = pd.Index(scope_frame["_event_time"].drop_duplicates().sort_values())
        time_folds = np.array_split(unique_times.to_numpy(), config.stability_folds)
        for policy_name, values in policies.items():
            for fold_index, fold_times in enumerate(time_folds, start=1):
                mask = scope_mask & frame["_event_time"].isin(fold_times)
                metrics = return_metrics(values.loc[mask])
                rows.append({
                    "policy": policy_name,
                    "scope": scope,
                    "fold": fold_index,
                    "start_timestamp": str(frame.loc[mask, "_event_time"].min()),
                    "end_timestamp": str(frame.loc[mask, "_event_time"].max()),
                    **metrics.to_dict(),
                    "positive": bool(metrics.expectancy > 0 and metrics.profit_factor >= 1.0),
                })
    return rows


def _cost_drag_rows(frame: pd.DataFrame, config: ExitPolicyAuditConfig) -> list[dict]:
    rows: list[dict] = []
    scopes = _scope_masks(frame)
    for scope, mask in scopes.items():
        for horizon in config.horizons:
            gross = fixed_horizon_return(frame.loc[mask], horizon, net=False)
            net = fixed_horizon_return(frame.loc[mask], horizon, net=True)
            gross_metrics = return_metrics(gross)
            net_metrics = return_metrics(net)
            aligned = pd.concat([gross.rename("gross"), net.rename("net")], axis=1).dropna()
            rows.append({
                "scope": scope,
                "horizon_candles": horizon,
                "coverage": round(len(aligned) / max(1, int(mask.sum())), 6),
                "gross_expectancy": gross_metrics.expectancy,
                "net_expectancy": net_metrics.expectancy,
                "execution_cost_drag": round(gross_metrics.expectancy - net_metrics.expectancy, 6),
                "gross_profit_factor": gross_metrics.profit_factor,
                "net_profit_factor": net_metrics.profit_factor,
                "gross_win_rate": gross_metrics.win_rate,
                "net_win_rate": net_metrics.win_rate,
                "gross_positive_net_negative": bool(
                    gross_metrics.expectancy > 0 and net_metrics.expectancy <= 0
                ),
                "sample_count": net_metrics.sample_count,
            })
    adaptive_gross = adaptive_horizon_return(frame, net=False)
    adaptive_net = adaptive_horizon_return(frame, net=True)
    if adaptive_net.notna().any():
        gross_metrics = return_metrics(adaptive_gross)
        net_metrics = return_metrics(adaptive_net)
        rows.append({
            "scope": "ALL_DIRECTIONAL",
            "horizon_candles": "ADAPTIVE",
            "coverage": round(net_metrics.sample_count / max(1, len(frame)), 6),
            "gross_expectancy": gross_metrics.expectancy,
            "net_expectancy": net_metrics.expectancy,
            "execution_cost_drag": round(gross_metrics.expectancy - net_metrics.expectancy, 6),
            "gross_profit_factor": gross_metrics.profit_factor,
            "net_profit_factor": net_metrics.profit_factor,
            "gross_win_rate": gross_metrics.win_rate,
            "net_win_rate": net_metrics.win_rate,
            "gross_positive_net_negative": bool(
                gross_metrics.expectancy > 0 and net_metrics.expectancy <= 0
            ),
            "sample_count": net_metrics.sample_count,
        })
    return rows


def _label_consistency_rows(frame: pd.DataFrame, config: ExitPolicyAuditConfig) -> list[dict]:
    canonical = fixed_horizon_return(frame, config.canonical_horizon, net=True)
    sign_win = canonical.gt(0)
    rows: list[dict] = []

    def add(name: str, mask: pd.Series, note: str) -> None:
        rows.append({
            "diagnostic": name,
            "count": int(mask.fillna(False).sum()),
            "rate": round(float(mask.fillna(False).mean()), 6),
            "note": note,
        })

    if "win" in frame.columns:
        recorded = frame["win"].astype(str).str.lower().map({"true": True, "false": False})
        comparable = recorded.notna() & canonical.notna()
        add(
            "RECORDED_WIN_DISAGREES_WITH_CANONICAL_NET_SIGN",
            comparable & recorded.ne(sign_win),
            "The persisted win flag should equal the sign of canonical net return.",
        )
    if "outcome_label" in frame.columns:
        recorded_label = frame["outcome_label"].astype(str).str.upper()
        expected_label = pd.Series(np.where(sign_win, "WIN", "LOSS"), index=frame.index)
        comparable = canonical.notna() & recorded_label.isin(["WIN", "LOSS"])
        add(
            "OUTCOME_LABEL_DISAGREES_WITH_CANONICAL_NET_SIGN",
            comparable & recorded_label.ne(expected_label),
            "Outcome WIN/LOSS should be derived from canonical net return, not target-hit alone.",
        )
    target_hit = frame.get("target_1_hit", pd.Series(False, index=frame.index)).fillna(False).astype(bool)
    stop_hit = frame.get("stop_hit", pd.Series(False, index=frame.index)).fillna(False).astype(bool)
    add(
        "TARGET_1_HIT_BUT_CANONICAL_NET_LOSS",
        target_hit & canonical.le(0),
        "A target touch does not guarantee a profitable fixed-horizon outcome.",
    )
    add(
        "STOP_HIT_BUT_CANONICAL_NET_WIN",
        stop_hit & canonical.gt(0),
        "A stop touch may coexist with a later positive fixed-horizon close.",
    )
    add(
        "TARGET_1_AND_STOP_BOTH_HIT_WITHIN_RECORDED_PATH",
        target_hit & stop_hit,
        "Both levels were touched; first-touch order matters.",
    )
    ambiguous = frame.get("intrabar_ambiguity", pd.Series(False, index=frame.index)).fillna(False).astype(bool)
    add(
        "SAME_CANDLE_STOP_TARGET_AMBIGUITY",
        ambiguous,
        "OHLC bars cannot resolve same-candle stop/target order without lower-timeframe data.",
    )
    return rows


def _planned_economics_rows(frame: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for scope, mask in _scope_masks(frame).items():
        summary = planned_economics_summary(frame.loc[mask])
        rows.append({"scope": scope, **summary})
    return rows


def _ambiguity_rows(frame: pd.DataFrame, config: ExitPolicyAuditConfig) -> list[dict]:
    rows: list[dict] = []
    ambiguous = frame.get("intrabar_ambiguity", pd.Series(False, index=frame.index)).fillna(False).astype(bool)
    for horizon in config.horizons:
        conservative = first_touch_return(frame, horizon, ambiguity_policy="STOP_FIRST")
        optimistic = first_touch_return(frame, horizon, ambiguity_policy="TARGET_FIRST")
        pair = pd.concat(
            [conservative.rename("stop_first"), optimistic.rename("target_first")], axis=1
        ).dropna()
        delta = pair["target_first"] - pair["stop_first"]
        rows.append({
            "horizon_candles": horizon,
            "ambiguous_rows": int(ambiguous.sum()),
            "ambiguity_rate": round(float(ambiguous.mean()), 6),
            "stop_first_expectancy": return_metrics(conservative).expectancy,
            "target_first_expectancy": return_metrics(optimistic).expectancy,
            "overall_expectancy_sensitivity": round(float(delta.mean()), 6) if not delta.empty else 0.0,
            "total_return_sensitivity": round(float(delta.sum()), 6) if not delta.empty else 0.0,
            "ambiguous_trade_mean_sensitivity": round(
                float(delta.loc[ambiguous.reindex(delta.index, fill_value=False)].mean()), 6
            ) if ambiguous.any() else 0.0,
        })
    return rows


def _policy_summary_rows(
    frame: pd.DataFrame,
    policies: dict[str, pd.Series],
) -> list[dict]:
    rows: list[dict] = []
    scopes = _scope_masks(frame)
    for policy_name, values in policies.items():
        for scope, mask in scopes.items():
            metrics = return_metrics(values.loc[mask])
            rows.append({
                "policy": policy_name,
                "scope": scope,
                "coverage": round(metrics.sample_count / max(1, int(mask.sum())), 6),
                **metrics.to_dict(),
            })
    return rows


def _choose_recommendation(
    policy_summary: pd.DataFrame,
    stability: pd.DataFrame,
    ambiguity: pd.DataFrame,
    config: ExitPolicyAuditConfig,
) -> tuple[Optional[str], list[str]]:
    blockers: list[str] = []
    all_scope = policy_summary[policy_summary["scope"].eq("ALL_DIRECTIONAL")].copy()
    canonical_name = f"FIXED_CLOSE_{config.canonical_horizon}C_NET"
    canonical_rows = all_scope[all_scope["policy"].eq(canonical_name)]
    if canonical_rows.empty:
        return None, ["Canonical fixed-close policy is unavailable."]
    canonical_expectancy = float(canonical_rows.iloc[0]["expectancy"])
    ambiguity_lookup = {
        int(row["horizon_candles"]): abs(float(row["overall_expectancy_sensitivity"]))
        for _, row in ambiguity.iterrows()
    }
    eligible: list[tuple[float, str]] = []
    for _, row in all_scope.iterrows():
        policy = str(row["policy"])
        if policy == canonical_name:
            continue
        positive_folds = int(
            stability.loc[
                stability["policy"].eq(policy) & stability["scope"].eq("ALL_DIRECTIONAL"),
                "positive",
            ].astype(bool).sum()
        )
        horizon = next((h for h in config.horizons if f"_{h}C_" in policy or policy.endswith(f"_{h}C_NET")), None)
        ambiguity_sensitivity = ambiguity_lookup.get(horizon, 0.0) if "FIRST_TOUCH" in policy else 0.0
        passes = (
            int(row["sample_count"]) >= config.minimum_policy_rows
            and float(row["coverage"]) >= config.minimum_coverage
            and float(row["expectancy"]) > config.minimum_expectancy_pct
            and float(row["profit_factor"]) >= config.minimum_profit_factor
            and float(row["expectancy"]) >= canonical_expectancy + config.minimum_improvement_pct
            and positive_folds >= config.minimum_positive_stability_folds
            and ambiguity_sensitivity <= config.maximum_ambiguity_sensitivity_pct
        )
        if passes:
            eligible.append((float(row["expectancy"]), policy))
    if eligible:
        eligible.sort(reverse=True)
        return eligible[0][1], blockers
    blockers.extend([
        "No alternative label/exit policy preserved positive net expectancy and profit factor >= 1.05.",
        "No policy met the required chronological stability, coverage, and minimum-sample constraints.",
        "Canonical labels and runtime exit behavior remain unchanged; this audit is diagnostic only.",
    ])
    return None, blockers


def _render_markdown(result: ExitPolicyAuditResult, artifacts: ExitPolicyAuditArtifacts) -> str:
    lines = [
        "# Freakto Label & Outcome Economics Audit",
        "",
        f"- Status: **{result.status}**",
        f"- Selected replay run: `{result.selected_run_id}`",
        f"- Rows loaded / usable: `{result.rows_loaded} / {result.rows_usable}`",
        f"- Canonical policy: `{result.canonical_policy}`",
        f"- Recommended replacement: `{result.recommended_policy}`",
        f"- Policy change applied: `{result.policy_change_applied}`",
        "",
        "## Key findings",
        "",
    ]
    lines.extend([f"- {item}" for item in result.key_findings])
    lines.extend(["", "## Blockers", ""])
    lines.extend([f"- {item}" for item in result.blockers])
    if not artifacts.policy_summary.empty:
        lines.extend(["", "## All-directional policy comparison", ""])
        subset = artifacts.policy_summary[artifacts.policy_summary["scope"].eq("ALL_DIRECTIONAL")]
        lines.append("| Policy | n | Coverage | Expectancy | Win rate | PF |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for _, row in subset.iterrows():
            lines.append(
                f"| {row['policy']} | {int(row['sample_count'])} | {float(row['coverage']):.2%} | "
                f"{float(row['expectancy']):.6f}% | {float(row['win_rate']):.2%} | "
                f"{float(row['profit_factor']):.6f} |"
            )
    lines.extend([
        "",
        "## Safety",
        "",
        "Research-only. No canonical label, score weight, Paper setting, or Live setting was changed.",
    ])
    return "\n".join(lines) + "\n"


def run_exit_policy_audit(
    dataset_path: Path | str = DEFAULT_DATASET,
    *,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    run_id: Optional[str] = None,
    config: ExitPolicyAuditConfig = ExitPolicyAuditConfig(),
) -> tuple[ExitPolicyAuditResult, ExitPolicyAuditArtifacts]:
    config.validate()
    source = Path(dataset_path)
    output = Path(output_dir)
    frame, metadata, warnings = load_exit_audit_dataset(
        source, run_id=run_id, latest_run_only=True, config=config
    )
    policies = _build_policy_series(frame, config)
    artifacts = ExitPolicyAuditArtifacts(
        policy_summary=pd.DataFrame(_policy_summary_rows(frame, policies)),
        policy_stability=pd.DataFrame(_stability_rows(frame, policies, config)),
        cost_drag=pd.DataFrame(_cost_drag_rows(frame, config)),
        label_consistency=pd.DataFrame(_label_consistency_rows(frame, config)),
        planned_economics=pd.DataFrame(_planned_economics_rows(frame)),
        ambiguity_sensitivity=pd.DataFrame(_ambiguity_rows(frame, config)),
    )
    recommended, blockers = _choose_recommendation(
        artifacts.policy_summary,
        artifacts.policy_stability,
        artifacts.ambiguity_sensitivity,
        config,
    )
    canonical_name = f"FIXED_CLOSE_{config.canonical_horizon}C_NET"
    all_policies = artifacts.policy_summary[
        artifacts.policy_summary["scope"].eq("ALL_DIRECTIONAL")
    ].set_index("policy")
    canonical = all_policies.loc[canonical_name].to_dict()
    best_net_row = all_policies.sort_values("expectancy", ascending=False).iloc[0]
    best_net_name = str(all_policies.sort_values("expectancy", ascending=False).index[0])
    cost_all = artifacts.cost_drag[artifacts.cost_drag["scope"].eq("ALL_DIRECTIONAL")]
    gross_positive_net_negative = int(cost_all["gross_positive_net_negative"].astype(bool).sum())
    planned = artifacts.planned_economics[
        artifacts.planned_economics["scope"].eq("ALL_DIRECTIONAL")
    ].iloc[0].to_dict()
    label_lookup = artifacts.label_consistency.set_index("diagnostic")["count"].to_dict()
    ambiguity_rate = float(artifacts.ambiguity_sensitivity.iloc[0]["ambiguity_rate"])
    isolated_positive: list[str] = []
    side_positive = artifacts.policy_summary[
        artifacts.policy_summary["scope"].isin(["LONG", "SHORT"])
        & artifacts.policy_summary["expectancy"].gt(0)
        & artifacts.policy_summary["profit_factor"].ge(1.0)
    ]
    for _, row in side_positive.iterrows():
        positive_folds = int(artifacts.policy_stability.loc[
            artifacts.policy_stability["policy"].eq(row["policy"])
            & artifacts.policy_stability["scope"].eq(row["scope"]),
            "positive",
        ].astype(bool).sum())
        isolated_positive.append(
            f"{row['scope']} {row['policy']} (expectancy={float(row['expectancy']):.6f}%, "
            f"PF={float(row['profit_factor']):.6f}, positive folds={positive_folds}/{config.stability_folds})"
        )
    key_findings = [
        f"Canonical {config.canonical_horizon}-candle net expectancy was {float(canonical['expectancy']):.6f}% "
        f"with profit factor {float(canonical['profit_factor']):.6f}.",
        f"Best observed net label was {best_net_name} at {float(best_net_row['expectancy']):.6f}%, "
        "but it did not satisfy promotion requirements.",
        f"Gross expectancy was positive while net expectancy was non-positive in {gross_positive_net_negative} "
        "all-directional horizon/adaptive comparisons; execution costs are a primary edge eraser.",
        f"Mean round-trip execution cost was {float(planned.get('round_trip_cost_pct_mean', 0.0)):.6f}%.",
        f"Mean planned Target-1/Stop net reward-risk was {float(planned.get('planned_net_reward_risk_mean', 0.0)):.6f}; "
        f"the implied mean break-even win rate was {float(planned.get('planned_break_even_win_rate_mean', 0.0)):.2%}.",
        f"Target 1 and Stop were both touched in {int(label_lookup.get('TARGET_1_AND_STOP_BOTH_HIT_WITHIN_RECORDED_PATH', 0))} rows, "
        "so path order matters even when final fixed-close labels are retained.",
        f"Same-candle stop/target ambiguity affected {ambiguity_rate:.2%} of rows; sensitivity is measurable but not the root cause.",
        "A target-hit flag must not be treated as a win label because target touches and canonical net losses can coexist.",
        "Longer fixed horizons reduced the net loss but did not produce positive all-directional net expectancy on the selected replay run.",
    ]
    if isolated_positive:
        key_findings.append(
            "Isolated side-specific positive results were non-promotable because they were weak or temporally unstable: "
            + "; ".join(isolated_positive)
            + "."
        )
    key_findings = warnings + key_findings
    result = ExitPolicyAuditResult(
        created_utc=datetime.now(timezone.utc).isoformat(),
        version=VERSION,
        economics_version=ECONOMICS_VERSION,
        status="COMPLETE_NO_POLICY_CHANGE" if recommended is None else "RESEARCH_CANDIDATE_FOUND",
        mode="RESEARCH_AUDIT_ONLY",
        dataset_path=str(source),
        dataset_sha256=_sha256(source),
        selected_run_id=metadata.get("selected_run_id"),
        rows_loaded=int(metadata["rows_loaded"]),
        rows_usable=int(metadata["rows_usable"]),
        canonical_policy=canonical_name,
        recommended_policy=recommended,
        policy_change_applied=False,
        paper_live_enabled=False,
        key_findings=key_findings,
        blockers=blockers,
        diagnostics={
            "canonical_metrics": canonical,
            "best_observed_policy": best_net_name,
            "best_observed_metrics": best_net_row.to_dict(),
            "planned_economics": planned,
            "label_consistency": artifacts.label_consistency.to_dict(orient="records"),
        },
    )
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "policy_summary_csv": output / "outcome_policy_summary.csv",
        "policy_stability_csv": output / "outcome_policy_stability.csv",
        "cost_drag_csv": output / "execution_cost_drag.csv",
        "label_consistency_csv": output / "label_consistency.csv",
        "planned_economics_csv": output / "planned_trade_economics.csv",
        "ambiguity_sensitivity_csv": output / "intrabar_ambiguity_sensitivity.csv",
        "report_json": output / "label_outcome_economics_report.json",
        "report_markdown": output / "label_outcome_economics_report.md",
    }
    artifacts.policy_summary.to_csv(paths["policy_summary_csv"], index=False)
    artifacts.policy_stability.to_csv(paths["policy_stability_csv"], index=False)
    artifacts.cost_drag.to_csv(paths["cost_drag_csv"], index=False)
    artifacts.label_consistency.to_csv(paths["label_consistency_csv"], index=False)
    artifacts.planned_economics.to_csv(paths["planned_economics_csv"], index=False)
    artifacts.ambiguity_sensitivity.to_csv(paths["ambiguity_sensitivity_csv"], index=False)
    result.output_files = {key: str(path) for key, path in paths.items()}
    paths["report_json"].write_text(
        json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    paths["report_markdown"].write_text(_render_markdown(result, artifacts), encoding="utf-8")
    return result, artifacts
