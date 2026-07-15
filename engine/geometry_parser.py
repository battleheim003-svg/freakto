"""Robust parsing for replay entry/stop/target geometry.

The parser accepts native numbers, lists/tuples, JSON/Python literals, mappings,
and textual ranges.  It never reads outcome fields and is therefore safe for
entry-time cost-gate diagnostics.
"""
from __future__ import annotations

from dataclasses import dataclass
import ast
import json
import math
import re
from typing import Any, Iterable, List, Mapping, Sequence, Tuple

import numpy as np

VERSION = "1.0.0"
_NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
_NULLS = {"", "nan", "none", "null", "---", "n/a", "na"}


@dataclass(frozen=True)
class ParsedGeometry:
    entry: float
    stop: float
    target: float
    entry_values: Tuple[float, ...]
    stop_values: Tuple[float, ...]
    target_values: Tuple[float, ...]
    entry_valid: bool
    stop_valid: bool
    target_valid: bool
    geometry_valid: bool
    parse_reason: str


def _finite_positive(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def extract_numeric_values(value: Any) -> List[float]:
    """Extract all finite positive numeric values while preserving order."""
    if value is None:
        return []
    if isinstance(value, (int, float, np.integer, np.floating)):
        return [float(value)] if _finite_positive(value) else []
    if isinstance(value, Mapping):
        preferred = ("price", "value", "mid", "entry", "stop", "target", "t1", "target_1")
        values: List[float] = []
        for key in preferred:
            if key in value:
                values.extend(extract_numeric_values(value[key]))
        if values:
            return values
        for item in value.values():
            values.extend(extract_numeric_values(item))
        return values
    if isinstance(value, (list, tuple, set, np.ndarray)):
        values: List[float] = []
        for item in value:
            values.extend(extract_numeric_values(item))
        return values

    text = str(value).strip().replace("`", "")
    if text.lower() in _NULLS:
        return []
    for loader in (json.loads, ast.literal_eval):
        try:
            decoded = loader(text)
        except Exception:
            continue
        if decoded is not value and not isinstance(decoded, str):
            values = extract_numeric_values(decoded)
            if values:
                return values
    normalized = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", text)
    return [float(match.group(0)) for match in _NUMBER.finditer(normalized) if _finite_positive(match.group(0))]


def _midpoint(values: Sequence[float]) -> float:
    clean = [float(v) for v in values if _finite_positive(v)]
    if not clean:
        return float("nan")
    if len(clean) == 1:
        return clean[0]
    return float((min(clean) + max(clean)) / 2.0)


def _select_target(values: Sequence[float], entry: float, side: str) -> float:
    clean = sorted({float(v) for v in values if _finite_positive(v)})
    if not clean or not _finite_positive(entry):
        return float("nan")
    if side == "LONG":
        favorable = [v for v in clean if v > entry]
        return min(favorable) if favorable else float("nan")
    if side == "SHORT":
        favorable = [v for v in clean if v < entry]
        return max(favorable) if favorable else float("nan")
    return float("nan")


def _select_stop(values: Sequence[float], entry: float, side: str) -> float:
    clean = sorted({float(v) for v in values if _finite_positive(v)})
    if not clean or not _finite_positive(entry):
        return float("nan")
    if side == "LONG":
        adverse = [v for v in clean if v < entry]
        return max(adverse) if adverse else float("nan")
    if side == "SHORT":
        adverse = [v for v in clean if v > entry]
        return min(adverse) if adverse else float("nan")
    return float("nan")


def parse_trade_geometry(entry_value: Any, stop_value: Any, target_value: Any, side: Any) -> ParsedGeometry:
    side_text = str(side or "").strip().upper()
    entry_values = tuple(extract_numeric_values(entry_value))
    stop_values = tuple(extract_numeric_values(stop_value))
    target_values = tuple(extract_numeric_values(target_value))
    entry = _midpoint(entry_values)
    stop = _select_stop(stop_values, entry, side_text)
    target = _select_target(target_values, entry, side_text)
    entry_valid = _finite_positive(entry)
    stop_valid = _finite_positive(stop)
    target_valid = _finite_positive(target)
    reasons: List[str] = []
    if side_text not in {"LONG", "SHORT"}:
        reasons.append("INVALID_SIDE")
    if not entry_valid:
        reasons.append("INVALID_ENTRY")
    if not stop_valid:
        reasons.append("INVALID_STOP")
    if not target_valid:
        reasons.append("INVALID_TARGET")
    geometry_valid = side_text in {"LONG", "SHORT"} and entry_valid and stop_valid and target_valid
    return ParsedGeometry(
        entry=entry,
        stop=stop,
        target=target,
        entry_values=entry_values,
        stop_values=stop_values,
        target_values=target_values,
        entry_valid=entry_valid,
        stop_valid=stop_valid,
        target_valid=target_valid,
        geometry_valid=geometry_valid,
        parse_reason="OK" if geometry_valid else "|".join(reasons),
    )
