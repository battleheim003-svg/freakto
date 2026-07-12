"""Robust edge-gate threshold optimization for Freakto.

The optimizer only consumes out-of-sample predictions produced by a calibration
mapping fitted elsewhere.  It never fits a calibration model itself, which keeps
model fitting, threshold selection, and final holdout evaluation separable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Iterable, Sequence

import pandas as pd

VERSION = "v10.4.0"


@dataclass(frozen=True)
class EdgeGatePolicyCandidate:
    raw_score_threshold: int
    min_probability: float
    min_samples: int
    break_even_probability: float
    min_expected_edge: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SelectionMetrics:
    sample_count: int
    win_count: int
    loss_count: int
    flat_count: int
    win_rate: float
    avg_return: float
    median_return: float
    expectancy: float
    profit_factor: float
    max_drawdown: float
    total_return: float

    def to_dict(self) -> dict:
        return asdict(self)


def thresholds() -> list[int]:
    """Backward-compatible raw-score research grid."""
    return [40, 50, 60, 70, 80, 90]


def _as_float_series(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce")


def apply_policy(frame: pd.DataFrame, policy: EdgeGatePolicyCandidate) -> pd.Series:
    required = {"score", "calibrated_probability", "calibration_sample_count"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing policy columns: {', '.join(missing)}")

    score = _as_float_series(frame["score"])
    probability = _as_float_series(frame["calibrated_probability"])
    samples = _as_float_series(frame["calibration_sample_count"])
    expected_edge = probability - float(policy.break_even_probability)

    return (
        score.ge(policy.raw_score_threshold)
        & probability.ge(policy.min_probability)
        & samples.ge(policy.min_samples)
        & expected_edge.ge(policy.min_expected_edge)
        & score.notna()
        & probability.notna()
        & samples.notna()
    )


def selection_metrics(returns: pd.Series) -> SelectionMetrics:
    clean = _as_float_series(returns).dropna()
    if clean.empty:
        return SelectionMetrics(0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    wins = clean[clean > 0]
    losses = clean[clean < 0]
    flat = clean[clean == 0]
    gross_profit = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    if gross_loss == 0:
        profit_factor = gross_profit if gross_profit > 0 else 0.0
    else:
        profit_factor = gross_profit / gross_loss

    equity = clean.cumsum()
    drawdown = equity - equity.cummax()
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0

    return SelectionMetrics(
        sample_count=int(len(clean)),
        win_count=int(len(wins)),
        loss_count=int(len(losses)),
        flat_count=int(len(flat)),
        win_rate=round(float(len(wins) / len(clean)), 6),
        avg_return=round(float(clean.mean()), 6),
        median_return=round(float(clean.median()), 6),
        expectancy=round(float(clean.mean()), 6),
        profit_factor=round(float(profit_factor), 6),
        max_drawdown=round(max_drawdown, 6),
        total_return=round(float(clean.sum()), 6),
    )


def _objective(metrics: SelectionMetrics, *, target_sample_count: int) -> float:
    if metrics.sample_count <= 0:
        return float("-inf")

    reliability = min(1.0, metrics.sample_count / max(1, target_sample_count))
    pf_term = math.log1p(min(metrics.profit_factor, 5.0))
    drawdown_penalty = abs(min(metrics.max_drawdown, 0.0)) * 0.015
    return round(
        metrics.expectancy * 3.0
        + (metrics.win_rate - 0.5) * 2.0
        + pf_term * 0.25
        + reliability * 0.20
        - drawdown_penalty,
        8,
    )


def optimize_edge_thresholds(
    frame: pd.DataFrame,
    *,
    return_column: str = "evaluated_return",
    raw_score_thresholds: Sequence[int] = tuple(range(50, 91, 5)),
    probability_thresholds: Sequence[float] = tuple(round(0.50 + i * 0.01, 2) for i in range(21)),
    minimum_samples_grid: Sequence[int] = (30, 50, 75, 100, 150, 200),
    expected_edge_grid: Sequence[float] = (0.0, 0.02, 0.03, 0.05),
    break_even_probability: float = 0.50,
    minimum_selected: int = 30,
    target_sample_count: int = 150,
) -> tuple[EdgeGatePolicyCandidate | None, pd.DataFrame]:
    if return_column not in frame.columns:
        raise ValueError(f"Return column not found: {return_column}")

    rows: list[dict] = []
    best: EdgeGatePolicyCandidate | None = None
    best_key: tuple[float, int, float, float] | None = None

    for raw_score in raw_score_thresholds:
        for probability in probability_thresholds:
            for min_samples in minimum_samples_grid:
                for min_edge in expected_edge_grid:
                    policy = EdgeGatePolicyCandidate(
                        raw_score_threshold=int(raw_score),
                        min_probability=float(probability),
                        min_samples=int(min_samples),
                        break_even_probability=float(break_even_probability),
                        min_expected_edge=float(min_edge),
                    )
                    mask = apply_policy(frame, policy)
                    metrics = selection_metrics(frame.loc[mask, return_column])
                    viable = (
                        metrics.sample_count >= minimum_selected
                        and metrics.expectancy > 0
                        and metrics.profit_factor >= 1.0
                    )
                    objective = _objective(metrics, target_sample_count=target_sample_count) if viable else float("-inf")
                    row = {**policy.to_dict(), **metrics.to_dict(), "viable": viable, "objective": objective}
                    rows.append(row)

                    key = (objective, metrics.sample_count, metrics.expectancy, metrics.profit_factor)
                    if viable and (best_key is None or key > best_key):
                        best_key = key
                        best = policy

    results = pd.DataFrame(rows)
    if not results.empty:
        results = results.sort_values(
            ["viable", "objective", "sample_count", "expectancy", "profit_factor"],
            ascending=[False, False, False, False, False],
            kind="stable",
        ).reset_index(drop=True)
    return best, results
