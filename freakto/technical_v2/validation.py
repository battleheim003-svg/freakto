"""Purged walk-forward splits and leakage-resistant challenger evaluation."""

from __future__ import annotations

from collections.abc import Iterable


def purged_walk_forward_splits(
    length: int,
    *,
    train_size: int,
    test_size: int,
    purge_bars: int = 1,
    embargo_bars: int = 1,
) -> list[dict[str, tuple[int, int]]]:
    if min(length, train_size, test_size) <= 0 or min(purge_bars, embargo_bars) < 0:
        raise ValueError("Walk-forward sizes must be positive and gaps non-negative")
    splits = []
    train_start = 0
    while True:
        train_end = train_start + train_size
        test_start = train_end + purge_bars
        test_end = test_start + test_size
        if test_end > length:
            break
        splits.append({"train": (train_start, train_end), "purge": (train_end, test_start), "test": (test_start, test_end), "embargo": (test_end, min(length, test_end + embargo_bars))})
        train_start = test_end + embargo_bars - train_size
    return splits


def validate_walk_forward(fold_metrics: Iterable[dict[str, float]], *, minimum_folds: int = 3) -> dict[str, object]:
    folds = list(fold_metrics)
    expectancy = [float(item.get("expectancy_pct", 0)) for item in folds]
    positive = sum(value > 0 for value in expectancy)
    stability = positive / len(folds) if folds else 0.0
    status = "PASSED" if len(folds) >= minimum_folds and stability >= 0.67 and sum(expectancy) / len(expectancy) > 0 else "RESEARCH_CANDIDATE"
    return {"status": status, "folds": len(folds), "positive_folds": positive, "stability": round(stability, 4), "mean_expectancy_pct": round(sum(expectancy) / len(expectancy), 6) if expectancy else None}


def sequential_oos_report(records: Iterable[dict[str, object]], *, folds: int = 3) -> dict[str, object]:
    rows = list(records)
    if len(rows) < folds:
        return validate_walk_forward([], minimum_folds=folds)
    size = len(rows) // folds
    metrics = []
    for index in range(folds):
        start = index * size
        end = len(rows) if index == folds - 1 else (index + 1) * size
        pnl = [float(item.get("pnl_pct", 0) or 0) for item in rows[start:end]]
        metrics.append({"expectancy_pct": sum(pnl) / max(1, len(pnl))})
    return validate_walk_forward(metrics, minimum_folds=folds)
