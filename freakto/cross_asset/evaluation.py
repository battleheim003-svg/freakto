"""Historical comparison of ranker selections against an eligible benchmark."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class RankerEvaluation:
    status: str
    completed_periods: int
    pending_periods: int
    selected_average_net_return_bps: float | None
    benchmark_average_net_return_bps: float | None
    average_excess_return_bps: float | None
    positive_excess_periods_pct: float | None
    period_results: tuple[dict[str, Any], ...]
    blockers: tuple[str, ...]


def evaluate_rankings(
    rankings: pd.DataFrame,
    outcomes: pd.DataFrame,
    *,
    min_completed_periods: int = 20,
) -> RankerEvaluation:
    required_rankings = {
        "period_utc",
        "symbol",
        "side",
        "research_selection",
    }
    required_outcomes = {
        "period_utc",
        "symbol",
        "outcome_observed_utc",
        "realized_gross_return_bps",
        "realized_cost_bps",
    }
    if not required_rankings.issubset(rankings.columns):
        return _blocked("RANKING_COLUMNS_MISSING")
    if not required_outcomes.issubset(outcomes.columns):
        return _blocked("OUTCOME_COLUMNS_MISSING")

    ranked = rankings.copy()
    actual = outcomes.copy()
    for frame in (ranked, actual):
        frame["period_utc"] = pd.to_datetime(frame["period_utc"], utc=True, errors="coerce")
        frame["symbol"] = frame["symbol"].astype(str).str.upper()
    actual["outcome_observed_utc"] = pd.to_datetime(
        actual["outcome_observed_utc"], utc=True, errors="coerce"
    )
    actual["realized_gross_return_bps"] = pd.to_numeric(
        actual["realized_gross_return_bps"], errors="coerce"
    )
    actual["realized_cost_bps"] = pd.to_numeric(
        actual["realized_cost_bps"], errors="coerce"
    )
    if ranked.duplicated(["period_utc", "symbol"]).any():
        return _blocked("DUPLICATE_RANKING_KEYS")
    if actual.duplicated(["period_utc", "symbol"]).any():
        return _blocked("DUPLICATE_OUTCOME_KEYS")
    if actual[["realized_gross_return_bps", "realized_cost_bps"]].isna().any(axis=None):
        return _blocked("INVALID_OUTCOME_NUMERIC")
    selection_text = ranked["research_selection"].astype(str).str.strip().str.lower()
    if not selection_text.isin({"true", "false", "1", "0"}).all():
        return _blocked("INVALID_RESEARCH_SELECTION")
    ranked["research_selection"] = selection_text.isin({"true", "1"})
    invalid_causality = (
        actual["period_utc"].isna()
        | actual["outcome_observed_utc"].isna()
        | (actual["outcome_observed_utc"] <= actual["period_utc"])
    )
    if invalid_causality.any():
        return _blocked(f"NON_CAUSAL_OUTCOMES:{int(invalid_causality.sum())}")

    merged = ranked.merge(
        actual,
        on=["period_utc", "symbol"],
        how="left",
        validate="one_to_one",
    )
    merged["signed_gross_bps"] = merged["realized_gross_return_bps"].where(
        merged["side"].astype(str).str.upper().eq("LONG"),
        -merged["realized_gross_return_bps"],
    )
    merged["realized_net_bps"] = (
        merged["signed_gross_bps"] - merged["realized_cost_bps"]
    )

    rows: list[dict[str, Any]] = []
    pending = 0
    for period, part in merged.groupby("period_utc", sort=True):
        selected = part[part["research_selection"]]
        if len(selected) != 1 or part["realized_net_bps"].isna().any():
            pending += 1
            continue
        selected_net = float(selected.iloc[0]["realized_net_bps"])
        benchmark = float(part["realized_net_bps"].mean())
        rows.append(
            {
                "period_utc": period.isoformat(),
                "selected_symbol": str(selected.iloc[0]["symbol"]),
                "selected_net_return_bps": selected_net,
                "eligible_equal_weight_benchmark_bps": benchmark,
                "excess_return_bps": selected_net - benchmark,
            }
        )

    result = pd.DataFrame(rows)
    required = max(1, int(min_completed_periods))
    blockers = (
        ()
        if len(result) >= required
        else (f"INSUFFICIENT_COMPLETED_PERIODS:{len(result)}<{required}",)
    )
    if result.empty:
        return RankerEvaluation(
            status="RESEARCH_CANDIDATE",
            completed_periods=0,
            pending_periods=pending,
            selected_average_net_return_bps=None,
            benchmark_average_net_return_bps=None,
            average_excess_return_bps=None,
            positive_excess_periods_pct=None,
            period_results=(),
            blockers=blockers,
        )
    return RankerEvaluation(
        status="PASSED" if not blockers else "RESEARCH_CANDIDATE",
        completed_periods=len(result),
        pending_periods=pending,
        selected_average_net_return_bps=round(
            float(result["selected_net_return_bps"].mean()), 4
        ),
        benchmark_average_net_return_bps=round(
            float(result["eligible_equal_weight_benchmark_bps"].mean()), 4
        ),
        average_excess_return_bps=round(
            float(result["excess_return_bps"].mean()), 4
        ),
        positive_excess_periods_pct=round(
            float(result["excess_return_bps"].gt(0).mean() * 100), 3
        ),
        period_results=tuple(rows),
        blockers=blockers,
    )


def _blocked(reason: str) -> RankerEvaluation:
    return RankerEvaluation(
        status="BLOCKED",
        completed_periods=0,
        pending_periods=0,
        selected_average_net_return_bps=None,
        benchmark_average_net_return_bps=None,
        average_excess_return_bps=None,
        positive_excess_periods_pct=None,
        period_results=(),
        blockers=(reason,),
    )
