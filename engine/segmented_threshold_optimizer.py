"""Segment-aware threshold search helpers for Freakto research.

This module deliberately keeps segment construction outside the optimizer.  It
receives a chronologically valid, already calibrated frame for exactly one
segment and searches the same edge-gate policy family used by the global
validator.  Keeping the wrapper small makes the leakage boundary explicit and
lets the caller use stricter per-segment sample constraints.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Sequence

import numpy as np
import pandas as pd

from .threshold_optimizer import (
    EdgeGatePolicyCandidate,
    apply_policy,
    optimize_edge_thresholds,
    selection_metrics,
)

VERSION = "v10.5.0"


@dataclass(frozen=True)
class SegmentedThresholdSearchConfig:
    """Conservative threshold grid for one pre-defined market segment."""

    raw_score_thresholds: tuple[int, ...] = tuple(range(50, 91, 5))
    probability_thresholds: tuple[float, ...] = tuple(
        round(0.50 + index * 0.01, 2) for index in range(21)
    )
    minimum_samples_grid: tuple[int, ...] = (10, 20, 30, 50, 75, 100)
    expected_edge_grid: tuple[float, ...] = (0.0, 0.02, 0.03, 0.05)
    break_even_probability: float = 0.50
    minimum_selected: int = 20
    target_sample_count: int = 80

    def validate(self) -> None:
        if not self.raw_score_thresholds:
            raise ValueError("raw_score_thresholds cannot be empty.")
        if not self.probability_thresholds:
            raise ValueError("probability_thresholds cannot be empty.")
        if not self.minimum_samples_grid:
            raise ValueError("minimum_samples_grid cannot be empty.")
        if not self.expected_edge_grid:
            raise ValueError("expected_edge_grid cannot be empty.")
        if self.minimum_selected <= 0:
            raise ValueError("minimum_selected must be positive.")
        if self.target_sample_count <= 0:
            raise ValueError("target_sample_count must be positive.")
        if not 0.0 <= self.break_even_probability <= 1.0:
            raise ValueError("break_even_probability must be between 0 and 1.")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SegmentPolicyEvaluation:
    segment_id: str
    selected_count: int
    expectancy: float
    profit_factor: float
    win_rate: float
    max_drawdown: float
    total_return: float
    viable: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _validated_frame(frame: pd.DataFrame) -> pd.DataFrame:
    required = {
        "score",
        "calibrated_probability",
        "calibration_sample_count",
        "evaluated_return",
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing segment optimizer columns: {', '.join(missing)}")
    return frame.copy()


def _bounded_sample_grid(frame: pd.DataFrame, configured: Sequence[int]) -> tuple[int, ...]:
    support = pd.to_numeric(frame["calibration_sample_count"], errors="coerce").dropna()
    max_support = int(support.max()) if not support.empty else 0
    candidates = sorted({max(1, int(value)) for value in configured if int(value) > 0})
    bounded = tuple(value for value in candidates if value <= max_support)
    if bounded:
        return bounded
    # Keep the search executable on very small research fixtures, but the
    # caller's split/sample gates still prevent promotion of weak segments.
    return (max(1, max_support),) if max_support > 0 else (1,)


def _fast_metrics(values: np.ndarray) -> dict:
    clean = values[np.isfinite(values)]
    if clean.size == 0:
        return {
            "sample_count": 0,
            "win_count": 0,
            "loss_count": 0,
            "flat_count": 0,
            "win_rate": 0.0,
            "avg_return": 0.0,
            "median_return": 0.0,
            "expectancy": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": 0.0,
            "total_return": 0.0,
        }
    wins = clean[clean > 0]
    losses = clean[clean < 0]
    flat = clean[clean == 0]
    gross_profit = float(wins.sum())
    gross_loss = abs(float(losses.sum()))
    profit_factor = (gross_profit if gross_profit > 0 else 0.0) if gross_loss == 0 else gross_profit / gross_loss
    equity = np.cumsum(clean)
    running_max = np.maximum.accumulate(equity)
    max_drawdown = float(np.min(equity - running_max)) if equity.size else 0.0
    mean = float(np.mean(clean))
    return {
        "sample_count": int(clean.size),
        "win_count": int(wins.size),
        "loss_count": int(losses.size),
        "flat_count": int(flat.size),
        "win_rate": round(float(wins.size / clean.size), 6),
        "avg_return": round(mean, 6),
        "median_return": round(float(np.median(clean)), 6),
        "expectancy": round(mean, 6),
        "profit_factor": round(float(profit_factor), 6),
        "max_drawdown": round(max_drawdown, 6),
        "total_return": round(float(np.sum(clean)), 6),
    }


def _fast_objective(metrics: dict, *, target_sample_count: int) -> float:
    if metrics["sample_count"] <= 0:
        return float("-inf")
    reliability = min(1.0, metrics["sample_count"] / max(1, target_sample_count))
    pf_term = math.log1p(min(metrics["profit_factor"], 5.0))
    drawdown_penalty = abs(min(metrics["max_drawdown"], 0.0)) * 0.015
    return round(
        metrics["expectancy"] * 3.0
        + (metrics["win_rate"] - 0.5) * 2.0
        + pf_term * 0.25
        + reliability * 0.20
        - drawdown_penalty,
        8,
    )


def optimize_segment_thresholds(
    frame: pd.DataFrame,
    *,
    segment_id: str,
    config: SegmentedThresholdSearchConfig = SegmentedThresholdSearchConfig(),
) -> tuple[EdgeGatePolicyCandidate | None, pd.DataFrame]:
    """Search one segment with cached NumPy masks instead of repeated pandas scans."""

    data = _validated_frame(frame)
    config.validate()
    sample_grid = _bounded_sample_grid(data, config.minimum_samples_grid)

    score = pd.to_numeric(data["score"], errors="coerce").to_numpy(dtype=float)
    probability = pd.to_numeric(data["calibrated_probability"], errors="coerce").to_numpy(dtype=float)
    samples = pd.to_numeric(data["calibration_sample_count"], errors="coerce").to_numpy(dtype=float)
    returns = pd.to_numeric(data["evaluated_return"], errors="coerce").to_numpy(dtype=float)
    finite = np.isfinite(score) & np.isfinite(probability) & np.isfinite(samples) & np.isfinite(returns)

    rows: list[dict] = []
    cache: dict[tuple[int, int, float], dict] = {}
    best: EdgeGatePolicyCandidate | None = None
    best_key: tuple[float, int, float, float] | None = None

    for raw_score in config.raw_score_thresholds:
        for min_probability in config.probability_thresholds:
            for min_samples in sample_grid:
                for min_edge in config.expected_edge_grid:
                    effective_probability = round(
                        max(float(min_probability), float(config.break_even_probability) + float(min_edge)),
                        10,
                    )
                    cache_key = (int(raw_score), int(min_samples), effective_probability)
                    metrics = cache.get(cache_key)
                    if metrics is None:
                        mask = (
                            finite
                            & (score >= int(raw_score))
                            & (probability >= effective_probability)
                            & (samples >= int(min_samples))
                        )
                        metrics = _fast_metrics(returns[mask])
                        cache[cache_key] = metrics

                    viable = (
                        metrics["sample_count"] >= config.minimum_selected
                        and metrics["expectancy"] > 0
                        and metrics["profit_factor"] >= 1.0
                    )
                    objective = (
                        _fast_objective(metrics, target_sample_count=config.target_sample_count)
                        if viable
                        else float("-inf")
                    )
                    policy = EdgeGatePolicyCandidate(
                        raw_score_threshold=int(raw_score),
                        min_probability=float(min_probability),
                        min_samples=int(min_samples),
                        break_even_probability=float(config.break_even_probability),
                        min_expected_edge=float(min_edge),
                    )
                    rows.append(
                        {
                            "segment_id": str(segment_id),
                            "optimizer_version": VERSION,
                            **policy.to_dict(),
                            **metrics,
                            "viable": viable,
                            "objective": objective,
                        }
                    )
                    key = (
                        objective,
                        metrics["sample_count"],
                        metrics["expectancy"],
                        metrics["profit_factor"],
                    )
                    if viable and (best_key is None or key > best_key):
                        best_key = key
                        best = policy

    candidates = pd.DataFrame(rows)
    if not candidates.empty:
        candidates = candidates.sort_values(
            ["viable", "objective", "sample_count", "expectancy", "profit_factor"],
            ascending=[False, False, False, False, False],
            kind="stable",
        ).reset_index(drop=True)
    return best, candidates


def evaluate_segment_policy(
    frame: pd.DataFrame,
    policy: EdgeGatePolicyCandidate | None,
    *,
    segment_id: str,
    minimum_selected: int,
    minimum_expectancy: float = 0.0,
    minimum_profit_factor: float = 1.0,
) -> SegmentPolicyEvaluation:
    """Evaluate a selected policy on data not used for threshold selection."""

    data = _validated_frame(frame)
    if policy is None:
        return SegmentPolicyEvaluation(
            segment_id=str(segment_id),
            selected_count=0,
            expectancy=0.0,
            profit_factor=0.0,
            win_rate=0.0,
            max_drawdown=0.0,
            total_return=0.0,
            viable=False,
        )

    mask = apply_policy(data, policy)
    metrics = selection_metrics(data.loc[mask, "evaluated_return"])
    viable = (
        metrics.sample_count >= int(minimum_selected)
        and metrics.expectancy > float(minimum_expectancy)
        and metrics.profit_factor >= float(minimum_profit_factor)
    )
    return SegmentPolicyEvaluation(
        segment_id=str(segment_id),
        selected_count=metrics.sample_count,
        expectancy=metrics.expectancy,
        profit_factor=metrics.profit_factor,
        win_rate=metrics.win_rate,
        max_drawdown=metrics.max_drawdown,
        total_return=metrics.total_return,
        viable=viable,
    )
