"""Statistical safeguards for feature research and multiple comparisons."""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple

import pandas as pd


def approximate_correlation_p_value(correlation: float, samples: int) -> float:
    """Two-sided normal approximation for a correlation significance check."""
    n = int(samples)
    r = max(-0.999999, min(0.999999, float(correlation)))
    if n < 4:
        return 1.0
    z = abs(math.atanh(r)) * math.sqrt(max(1.0, n - 3.0))
    return max(0.0, min(1.0, math.erfc(z / math.sqrt(2.0))))


def benjamini_hochberg(p_values: Iterable[float]) -> List[float]:
    """Return FDR-adjusted q-values in the original order."""
    values = [max(0.0, min(1.0, float(value))) for value in p_values]
    count = len(values)
    if not count:
        return []
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    adjusted = [1.0] * count
    running = 1.0
    for reverse_rank, (original_index, value) in enumerate(reversed(ordered), start=1):
        rank = count - reverse_rank + 1
        running = min(running, value * count / rank)
        adjusted[original_index] = max(0.0, min(1.0, running))
    return adjusted


def add_fdr_to_feature_rows(rows: List[Dict], split_prefix: str = "test_20") -> List[Dict]:
    eligible: List[Tuple[int, float]] = []
    for index, row in enumerate(rows):
        corr = row.get(f"{split_prefix}_correlation")
        samples = int(row.get(f"{split_prefix}_correlation_samples", 0) or 0)
        if corr is None or samples < 4:
            row["test_p_value"] = 1.0
            row["test_fdr_q_value"] = 1.0
            row["multiple_testing_significant"] = False
            continue
        p_value = approximate_correlation_p_value(float(corr), samples)
        row["test_p_value"] = round(p_value, 8)
        eligible.append((index, p_value))
    q_values = benjamini_hochberg(value for _, value in eligible)
    for (index, _), q_value in zip(eligible, q_values):
        rows[index]["test_fdr_q_value"] = round(q_value, 8)
        rows[index]["multiple_testing_significant"] = bool(q_value <= 0.05)
    return rows


def dataset_fingerprint(frame: pd.DataFrame, columns: Iterable[str]) -> str:
    import hashlib

    selected = [column for column in columns if column in frame.columns]
    if not selected or frame.empty:
        return "empty"
    work = frame[selected].copy()
    hashed = pd.util.hash_pandas_object(work, index=False).values.tobytes()
    return hashlib.sha256(hashed).hexdigest()

