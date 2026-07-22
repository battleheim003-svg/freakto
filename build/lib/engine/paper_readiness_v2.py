"""Fail-closed paper-trade launch readiness for Freakto.

This module separates two very different states:

* RESEARCH_PAPER_COLLECTION_ONLY: virtual observations may be recorded to test
  operations and accumulate untouched forward evidence.  It is not a strategy
  promotion and carries zero capital allocation.
* STRATEGY_PAPER_VALIDATION: a frozen deterministic event policy has passed
  development Holdout and chronological stability checks.  It is still paper
  only and never authorizes live orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from engine.baseline_benchmarks import block_bootstrap_expectancy_ci, strategy_metrics

VERSION = "1.0.0"
MODE = "PAPER_LAUNCH_FAIL_CLOSED"
DEFAULT_EVENT_DIR = Path("logs") / "event_opportunity_v2"
DEFAULT_COST_DIR = Path("logs") / "cost_gate_diagnostics"
DEFAULT_FRESH_REPORT = Path("logs") / "fresh_oos_v2" / "fresh_oos_report.json"
DEFAULT_OUTPUT_DIR = Path("logs") / "paper_launch_v2"


@dataclass(frozen=True)
class PaperReadinessConfig:
    deterministic_strategies: Tuple[str, ...] = (
        "EVENT_COST_GATED",
        "EVENT_BREAKOUT_CONFIRMATION_COST_GATED",
        "EVENT_VOLATILITY_EXPANSION_COST_GATED",
        "EVENT_REGIME_TRANSITION_COST_GATED",
    )
    minimum_event_rows: int = 300
    minimum_cost_gated_rows: int = 100
    minimum_holdout_samples: int = 100
    minimum_holdout_expectancy_pct: float = 0.0
    minimum_holdout_profit_factor: float = 1.05
    minimum_holdout_ci_low_pct: float = 0.0
    walk_forward_folds: int = 4
    walk_forward_purge_timestamps: int = 6
    minimum_fold_samples: int = 30
    minimum_valid_folds: int = 3
    minimum_positive_fold_fraction: float = 2.0 / 3.0
    fresh_oos_min_directional_rows: int = 300
    fresh_oos_min_fixed_gate_samples: int = 50
    fresh_oos_min_expectancy_pct: float = 0.0
    fresh_oos_min_profit_factor: float = 1.0
    bootstrap_samples: int = 400
    bootstrap_block_size: int = 24
    random_seed: int = 42


@dataclass(frozen=True)
class DeterministicCandidateAssessment:
    strategy: str
    eligible: bool
    holdout_sample_count: int
    holdout_expectancy_pct: float
    holdout_profit_factor: float
    holdout_ci_low_pct: float
    holdout_ci_high_pct: float
    valid_walk_forward_folds: int
    positive_walk_forward_folds: int
    positive_walk_forward_fraction: float
    blockers: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PaperLaunchReadiness:
    status: str
    created_utc: str
    research_collection_ready: bool
    strategy_paper_ready: bool
    selected_policy: Optional[str]
    event_rows: int
    cost_gated_event_rows: int
    fresh_directional_rows: int
    fresh_fixed_gate_samples: int
    fresh_expectancy_pct: float
    fresh_profit_factor: float
    candidate_assessments: List[DeterministicCandidateAssessment] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    paper_live_enabled: bool = False
    live_orders_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["candidate_assessments"] = [item.to_dict() for item in self.candidate_assessments]
        return payload


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except Exception:
        try:
            return pd.read_csv(path, low_memory=False)
        except Exception:
            return pd.DataFrame()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _pf(returns: Sequence[float]) -> float:
    values = pd.to_numeric(pd.Series(list(returns), dtype=float), errors="coerce").dropna()
    gains = float(values[values > 0].sum())
    losses = abs(float(values[values < 0].sum()))
    if losses <= 1e-12:
        return math.inf if gains > 0 else 0.0
    return gains / losses


def _strategy_mask(frame: pd.DataFrame, strategy: str) -> pd.Series:
    if frame.empty:
        return pd.Series(False, index=frame.index, dtype=bool)
    gated = frame.get("cost_gate_pass", pd.Series(False, index=frame.index)).astype(bool)
    if strategy == "EVENT_COST_GATED":
        return gated
    prefix = "EVENT_"
    suffix = "_COST_GATED"
    if strategy.startswith(prefix) and strategy.endswith(suffix):
        event = strategy[len(prefix) : -len(suffix)]
        return gated & frame.get("primary_event", pd.Series("", index=frame.index)).astype(str).eq(event)
    return pd.Series(False, index=frame.index, dtype=bool)


def deterministic_walk_forward(
    event_universe: pd.DataFrame,
    strategy: str,
    config: PaperReadinessConfig,
) -> pd.DataFrame:
    """Evaluate a fixed policy on non-overlapping chronological folds.

    No threshold or event definition is fitted in these folds.  They are a
    temporal stability diagnostic for a pre-declared deterministic strategy.
    """
    if event_universe is None or event_universe.empty or "__timestamp" not in event_universe.columns:
        return pd.DataFrame()
    work = event_universe.copy()
    work["__timestamp"] = pd.to_datetime(work["__timestamp"], utc=True, errors="coerce")
    work = work.dropna(subset=["__timestamp"]).sort_values("__timestamp", kind="stable")
    unique = pd.Index(work["__timestamp"].drop_duplicates().sort_values())
    folds = max(1, int(config.walk_forward_folds))
    if len(unique) < folds * 4:
        return pd.DataFrame()
    edges = np.linspace(0, len(unique), folds + 1, dtype=int)
    records: List[Dict[str, Any]] = []
    purge = max(0, int(config.walk_forward_purge_timestamps))
    for fold in range(folds):
        start_pos = edges[fold] + (purge if fold > 0 else 0)
        end_pos = edges[fold + 1]
        if end_pos <= start_pos:
            continue
        start = unique[start_pos]
        end = unique[end_pos - 1]
        segment = work[(work["__timestamp"] >= start) & (work["__timestamp"] <= end)].copy()
        selected = segment[_strategy_mask(segment, strategy)]
        returns = pd.to_numeric(selected.get("realized_net_return_pct"), errors="coerce").dropna()
        metrics = strategy_metrics(returns, total_rows=len(segment))
        positive = bool(
            metrics["sample_count"] >= config.minimum_fold_samples
            and metrics["expectancy"] > 0
            and metrics["profit_factor"] >= 1.0
        )
        records.append(
            {
                "strategy": strategy,
                "fold": fold + 1,
                "start_utc": pd.Timestamp(start).isoformat(),
                "end_utc": pd.Timestamp(end).isoformat(),
                **metrics,
                "positive": positive,
                "no_overlap": True,
            }
        )
    return pd.DataFrame(records)


def assess_deterministic_candidate(
    strategy: str,
    holdout_benchmarks: pd.DataFrame,
    walk_forward: pd.DataFrame,
    config: PaperReadinessConfig,
) -> DeterministicCandidateAssessment:
    row = holdout_benchmarks[holdout_benchmarks.get("strategy", pd.Series(dtype=str)).astype(str).eq(strategy)]
    blockers: List[str] = []
    if row.empty:
        return DeterministicCandidateAssessment(strategy, False, 0, 0.0, 0.0, 0.0, 0.0, 0, 0, 0.0, ("Holdout benchmark is missing.",))
    item = row.iloc[0]
    sample = int(float(item.get("sample_count", 0) or 0))
    expectancy = float(item.get("expectancy", 0.0) or 0.0)
    profit_factor = float(item.get("profit_factor", 0.0) or 0.0)
    ci_low = float(item.get("expectancy_ci_low", 0.0) or 0.0)
    ci_high = float(item.get("expectancy_ci_high", 0.0) or 0.0)
    valid = walk_forward.copy()
    if not valid.empty:
        valid = valid[valid.get("strategy", pd.Series("", index=valid.index)).astype(str).eq(strategy)]
        valid = valid[pd.to_numeric(valid.get("sample_count"), errors="coerce").ge(config.minimum_fold_samples)]
    positive = int(valid.get("positive", pd.Series(dtype=bool)).astype(bool).sum()) if not valid.empty else 0
    valid_count = int(len(valid))
    fraction = float(positive / valid_count) if valid_count else 0.0
    if sample < config.minimum_holdout_samples:
        blockers.append(f"Holdout samples {sample} < {config.minimum_holdout_samples}.")
    if expectancy <= config.minimum_holdout_expectancy_pct:
        blockers.append("Holdout expectancy is not positive.")
    if profit_factor < config.minimum_holdout_profit_factor:
        blockers.append("Holdout profit factor is below the minimum.")
    if ci_low <= config.minimum_holdout_ci_low_pct:
        blockers.append("Holdout confidence interval does not stay above zero.")
    if valid_count < config.minimum_valid_folds:
        blockers.append(f"Valid walk-forward folds {valid_count} < {config.minimum_valid_folds}.")
    if fraction < config.minimum_positive_fold_fraction:
        blockers.append("Walk-forward positive-fold fraction is insufficient.")
    return DeterministicCandidateAssessment(
        strategy=strategy,
        eligible=not blockers,
        holdout_sample_count=sample,
        holdout_expectancy_pct=expectancy,
        holdout_profit_factor=profit_factor,
        holdout_ci_low_pct=ci_low,
        holdout_ci_high_pct=ci_high,
        valid_walk_forward_folds=valid_count,
        positive_walk_forward_folds=positive,
        positive_walk_forward_fraction=fraction,
        blockers=tuple(blockers),
    )


def build_paper_launch_readiness(
    event_dir: str | Path = DEFAULT_EVENT_DIR,
    cost_dir: str | Path = DEFAULT_COST_DIR,
    fresh_report_path: str | Path = DEFAULT_FRESH_REPORT,
    config: Optional[PaperReadinessConfig] = None,
) -> Tuple[PaperLaunchReadiness, pd.DataFrame]:
    config = config or PaperReadinessConfig()
    event_dir = Path(event_dir)
    cost_dir = Path(cost_dir)
    universe = _read_csv(event_dir / "event_universe.csv")
    holdout = _read_csv(event_dir / "holdout_benchmarks.csv")
    cost_report = _read_json(cost_dir / "cost_gate_diagnostics_report.json")
    event_report = _read_json(event_dir / "event_opportunity_v2_report.json")
    fresh = _read_json(Path(fresh_report_path))

    event_rows = int(event_report.get("event_rows", len(universe)) or 0)
    cost_rows = int(event_report.get("cost_gated_event_rows", universe.get("cost_gate_pass", pd.Series(dtype=bool)).astype(bool).sum() if not universe.empty else 0) or 0)
    blockers: List[str] = []
    warnings: List[str] = []
    if universe.empty:
        blockers.append("Event universe is missing; run event_opportunity_v2_analysis.py.")
    if holdout.empty:
        blockers.append("Holdout benchmarks are missing.")
    if not cost_report:
        blockers.append("Cost-gate diagnostics report is missing.")
    if event_rows < config.minimum_event_rows:
        blockers.append(f"Event rows {event_rows} < {config.minimum_event_rows}.")
    if cost_rows < config.minimum_cost_gated_rows:
        blockers.append(f"Cost-gated event rows {cost_rows} < {config.minimum_cost_gated_rows}.")

    all_walk = []
    assessments: List[DeterministicCandidateAssessment] = []
    for strategy in config.deterministic_strategies:
        walk = deterministic_walk_forward(universe, strategy, config)
        if not walk.empty:
            all_walk.append(walk)
        assessments.append(assess_deterministic_candidate(strategy, holdout, walk, config))
    walk_table = pd.concat(all_walk, ignore_index=True) if all_walk else pd.DataFrame()
    eligible = [item for item in assessments if item.eligible]
    eligible.sort(
        key=lambda item: (item.holdout_expectancy_pct, item.holdout_profit_factor, item.holdout_sample_count),
        reverse=True,
    )
    selected = eligible[0].strategy if eligible else None

    fresh_directional = int(fresh.get("fresh_directional_rows", 0) or 0)
    fresh_samples = int(fresh.get("fixed_gate_samples", 0) or 0)
    fresh_exp = float(fresh.get("fixed_gate_expectancy", fresh.get("fixed_gate_expectancy_pct", 0.0)) or 0.0)
    fresh_pf = float(fresh.get("fixed_gate_profit_factor", 0.0) or 0.0)
    fresh_ok = bool(
        fresh_directional >= config.fresh_oos_min_directional_rows
        and fresh_samples >= config.fresh_oos_min_fixed_gate_samples
        and fresh_exp > config.fresh_oos_min_expectancy_pct
        and fresh_pf >= config.fresh_oos_min_profit_factor
    )
    research_ready = not blockers
    strategy_ready = bool(research_ready and selected and fresh_ok)
    if research_ready and not selected:
        warnings.append("No deterministic strategy passed all development stability gates; research paper observations remain zero-allocation only.")
    if selected and not fresh_ok:
        warnings.append("A development policy passed, but untouched Fresh OOS requirements are not yet met.")
    if fresh_directional < config.fresh_oos_min_directional_rows:
        warnings.append(
            f"Fresh OOS directional rows {fresh_directional}/{config.fresh_oos_min_directional_rows}; strategy paper remains blocked."
        )
    status = (
        "READY_FOR_STRATEGY_PAPER_VALIDATION"
        if strategy_ready
        else "READY_FOR_RESEARCH_PAPER_COLLECTION"
        if research_ready
        else "BLOCKED_PAPER_LAUNCH"
    )
    readiness = PaperLaunchReadiness(
        status=status,
        created_utc=datetime.now(timezone.utc).isoformat(),
        research_collection_ready=research_ready,
        strategy_paper_ready=strategy_ready,
        selected_policy=selected,
        event_rows=event_rows,
        cost_gated_event_rows=cost_rows,
        fresh_directional_rows=fresh_directional,
        fresh_fixed_gate_samples=fresh_samples,
        fresh_expectancy_pct=fresh_exp,
        fresh_profit_factor=fresh_pf,
        candidate_assessments=assessments,
        blockers=blockers,
        warnings=warnings,
        paper_live_enabled=False,
        live_orders_enabled=False,
    )
    return readiness, walk_table


def write_paper_readiness_outputs(
    readiness: PaperLaunchReadiness,
    walk_forward: pd.DataFrame,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> Dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "paper_launch_readiness.json"
    json_path.write_text(json.dumps(readiness.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    walk_path = output / "deterministic_candidate_walk_forward.csv"
    walk_forward.to_csv(walk_path, index=False, encoding="utf-8-sig")
    candidate_path = output / "deterministic_candidate_assessments.csv"
    pd.DataFrame([item.to_dict() for item in readiness.candidate_assessments]).to_csv(
        candidate_path, index=False, encoding="utf-8-sig"
    )
    lines = [
        "# Freakto Paper Launch Readiness v2",
        "",
        f"- Status: `{readiness.status}`",
        f"- Research collection ready: `{readiness.research_collection_ready}`",
        f"- Strategy paper ready: `{readiness.strategy_paper_ready}`",
        f"- Selected policy: `{readiness.selected_policy}`",
        f"- Event / cost-gated rows: `{readiness.event_rows} / {readiness.cost_gated_event_rows}`",
        f"- Fresh directional / selected samples: `{readiness.fresh_directional_rows} / {readiness.fresh_fixed_gate_samples}`",
        "- Live orders enabled: `False`",
        "",
        "## Blockers",
    ]
    lines.extend(f"- {item}" for item in readiness.blockers)
    lines += ["", "## Warnings"]
    lines.extend(f"- {item}" for item in readiness.warnings)
    md_path = output / "paper_launch_readiness.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "walk_forward": str(walk_path), "candidates": str(candidate_path)}
