"""Outcome-label and trade-economics primitives for Freakto research.

The functions in this module are intentionally independent from runtime trading.
They reconstruct net planned stop/target payoffs and compare fixed-close labels
with path-aware first-touch labels using only already-recorded replay fields.
No model weight, Paper setting, Live setting, or canonical label is modified.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
import re
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd

VERSION = "v10.8.0"
SUPPORTED_HORIZONS: tuple[int, ...] = (1, 3, 6, 12)
AMBIGUITY_POLICIES: tuple[str, ...] = ("STOP_FIRST", "TARGET_FIRST", "DROP")


@dataclass(frozen=True)
class ReturnMetrics:
    sample_count: int
    win_count: int
    loss_count: int
    flat_count: int
    win_rate: float
    avg_return: float
    median_return: float
    avg_win: float
    avg_loss: float
    payoff_ratio: float
    break_even_win_rate: float
    expectancy: float
    profit_factor: float
    max_drawdown: float
    total_return: float

    def to_dict(self) -> dict:
        return asdict(self)


def parse_price(value: object) -> float:
    """Parse one formatted price; return NaN for missing/unusable values."""

    if value is None or (isinstance(value, float) and math.isnan(value)):
        return float("nan")
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "null", "نامشخص", "---"}:
        return float("nan")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else float("nan")


def parse_targets(value: object) -> list[float]:
    """Parse a JSON/list/string target representation into numeric prices."""

    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    if isinstance(value, (list, tuple)):
        raw: Iterable[object] = value
    else:
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null", "[]"}:
            return []
        try:
            decoded = json.loads(text)
            raw = decoded if isinstance(decoded, list) else [decoded]
        except (TypeError, ValueError, json.JSONDecodeError):
            raw = re.findall(r"-?\d[\d,]*(?:\.\d+)?", text)
    output: list[float] = []
    for item in raw:
        parsed = parse_price(item)
        if math.isfinite(parsed):
            output.append(parsed)
    return output


def numeric_series(frame: pd.DataFrame, column: str, default: float = float("nan")) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(default, index=frame.index, dtype=float)
    return pd.to_numeric(frame[column], errors="coerce").astype(float)


def round_trip_cost_pct(frame: pd.DataFrame) -> pd.Series:
    """Return percentage-point round-trip costs for each row.

    Prefer the recorder's explicit ``round_trip_cost_pct`` when present.  For
    legacy replay rows, reconstruct costs as twice per-side fee plus slippage.
    Bps are converted to percentage points by dividing by 100.
    """

    explicit = numeric_series(frame, "round_trip_cost_pct")
    fee = numeric_series(frame, "fee_bps_per_side", 0.0).fillna(0.0)
    slippage = numeric_series(frame, "slippage_bps_per_side", 0.0).fillna(0.0)
    reconstructed = 2.0 * (fee + slippage) / 100.0
    cost = explicit.where(explicit.notna() & explicit.ge(0), reconstructed)
    return cost.clip(lower=0.0)


def signed_price_return_pct(
    entry_price: pd.Series,
    exit_price: pd.Series,
    side: pd.Series,
) -> pd.Series:
    entry = pd.to_numeric(entry_price, errors="coerce")
    exit_value = pd.to_numeric(exit_price, errors="coerce")
    normalized_side = side.astype(str).str.strip().str.upper()
    result = pd.Series(float("nan"), index=entry.index, dtype=float)
    valid = entry.gt(0) & exit_value.gt(0) & normalized_side.isin(["LONG", "SHORT"])
    long_mask = valid & normalized_side.eq("LONG")
    short_mask = valid & normalized_side.eq("SHORT")
    result.loc[long_mask] = (
        (exit_value.loc[long_mask] - entry.loc[long_mask]) / entry.loc[long_mask] * 100.0
    )
    result.loc[short_mask] = (
        (entry.loc[short_mask] - exit_value.loc[short_mask]) / entry.loc[short_mask] * 100.0
    )
    return result


def enrich_planned_economics(frame: pd.DataFrame) -> pd.DataFrame:
    """Add canonical entry/stop/target and planned payoff columns."""

    output = frame.copy()
    output["_entry_price"] = numeric_series(output, "entry_price")
    output["_stop_price"] = output.get("stop_zone", pd.Series(index=output.index, dtype=object)).map(parse_price)
    target_lists = output.get("targets", pd.Series(index=output.index, dtype=object)).map(parse_targets)
    for index in range(3):
        output[f"_target_{index + 1}_price"] = target_lists.map(
            lambda values, i=index: values[i] if len(values) > i else float("nan")
        )
    output["_round_trip_cost_pct"] = round_trip_cost_pct(output)
    side = output["side"].astype(str).str.upper()
    output["_stop_gross_return_pct"] = signed_price_return_pct(
        output["_entry_price"], output["_stop_price"], side
    )
    output["_stop_net_return_pct"] = (
        output["_stop_gross_return_pct"] - output["_round_trip_cost_pct"]
    )
    for index in range(1, 4):
        gross_column = f"_target_{index}_gross_return_pct"
        net_column = f"_target_{index}_net_return_pct"
        output[gross_column] = signed_price_return_pct(
            output["_entry_price"], output[f"_target_{index}_price"], side
        )
        output[net_column] = output[gross_column] - output["_round_trip_cost_pct"]

    net_reward = output["_target_1_net_return_pct"].clip(lower=0.0)
    net_loss = (-output["_stop_net_return_pct"]).clip(lower=0.0)
    output["_planned_net_reward_risk"] = net_reward / net_loss.replace(0.0, np.nan)
    denominator = net_reward + net_loss
    output["_planned_break_even_win_rate"] = net_loss / denominator.replace(0.0, np.nan)
    gross_reward = output["_target_1_gross_return_pct"].clip(lower=0.0)
    gross_loss = (-output["_stop_gross_return_pct"]).clip(lower=0.0)
    output["_planned_gross_reward_risk"] = gross_reward / gross_loss.replace(0.0, np.nan)
    return output


def fixed_horizon_return(frame: pd.DataFrame, horizon: int, *, net: bool = True) -> pd.Series:
    if horizon not in SUPPORTED_HORIZONS:
        raise ValueError(f"Unsupported horizon: {horizon}")
    prefix = "net_signed" if net else "gross_signed"
    column = f"{prefix}_return_after_{horizon}c_pct"
    return numeric_series(frame, column)


def first_touch_return(
    frame: pd.DataFrame,
    horizon: int,
    *,
    ambiguity_policy: str = "STOP_FIRST",
) -> pd.Series:
    """Construct a no-lookahead first-touch-or-time-exit label.

    A stop or Target 1 is used only when the recorded first exit occurred on or
    before ``horizon``. Otherwise the fixed-close net return at ``horizon`` is
    used. Intrabar bars that touched both stop and target can be treated
    conservatively (stop first), optimistically (target first), or dropped.
    """

    policy = str(ambiguity_policy).strip().upper()
    if policy not in AMBIGUITY_POLICIES:
        raise ValueError(f"Unsupported ambiguity policy: {ambiguity_policy}")
    if horizon not in SUPPORTED_HORIZONS:
        raise ValueError(f"Unsupported horizon: {horizon}")
    required = {"_stop_net_return_pct", "_target_1_net_return_pct"}
    if not required.issubset(frame.columns):
        frame = enrich_planned_economics(frame)

    result = fixed_horizon_return(frame, horizon, net=True).copy()
    offset = numeric_series(frame, "first_exit_candle_offset")
    reason = frame.get("first_exit_reason", pd.Series("", index=frame.index)).astype(str).str.upper()
    within = offset.notna() & offset.le(horizon)
    stop = within & reason.str.startswith("STOP")
    target = within & reason.eq("TARGET_1")
    result.loc[stop] = numeric_series(frame, "_stop_net_return_pct").loc[stop]
    result.loc[target] = numeric_series(frame, "_target_1_net_return_pct").loc[target]

    ambiguous = within & frame.get(
        "intrabar_ambiguity", pd.Series(False, index=frame.index)
    ).fillna(False).astype(bool)
    if policy == "TARGET_FIRST":
        result.loc[ambiguous] = numeric_series(frame, "_target_1_net_return_pct").loc[ambiguous]
    elif policy == "DROP":
        result.loc[ambiguous] = float("nan")
    else:
        result.loc[ambiguous] = numeric_series(frame, "_stop_net_return_pct").loc[ambiguous]
    return result


def adaptive_horizon_return(frame: pd.DataFrame, *, net: bool = True) -> pd.Series:
    column = "adaptive_net_return_pct" if net else "adaptive_gross_return_pct"
    return numeric_series(frame, column)


def return_metrics(values: Sequence[float] | pd.Series) -> ReturnMetrics:
    series = pd.to_numeric(pd.Series(values), errors="coerce").dropna().astype(float)
    if series.empty:
        return ReturnMetrics(0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    wins = series[series > 0]
    losses = series[series < 0]
    flats = series[series == 0]
    win_count = int(len(wins))
    loss_count = int(len(losses))
    avg_win = float(wins.mean()) if win_count else 0.0
    avg_loss = float((-losses).mean()) if loss_count else 0.0
    payoff_ratio = avg_win / avg_loss if avg_loss > 0 else (float("inf") if avg_win > 0 else 0.0)
    break_even = avg_loss / (avg_win + avg_loss) if avg_win > 0 and avg_loss > 0 else 0.0
    gross_profit = float(wins.sum())
    gross_loss = float(-losses.sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)
    equity = series.cumsum()
    drawdown = equity - equity.cummax()
    maximum_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0
    return ReturnMetrics(
        sample_count=int(len(series)),
        win_count=win_count,
        loss_count=loss_count,
        flat_count=int(len(flats)),
        win_rate=round(win_count / len(series), 6),
        avg_return=round(float(series.mean()), 6),
        median_return=round(float(series.median()), 6),
        avg_win=round(avg_win, 6),
        avg_loss=round(avg_loss, 6),
        payoff_ratio=round(payoff_ratio, 6) if math.isfinite(payoff_ratio) else float("inf"),
        break_even_win_rate=round(break_even, 6),
        expectancy=round(float(series.mean()), 6),
        profit_factor=round(profit_factor, 6) if math.isfinite(profit_factor) else float("inf"),
        max_drawdown=round(maximum_drawdown, 6),
        total_return=round(float(series.sum()), 6),
    )


def planned_economics_summary(frame: pd.DataFrame) -> dict:
    enriched = frame if "_planned_net_reward_risk" in frame.columns else enrich_planned_economics(frame)
    required = [
        "_round_trip_cost_pct",
        "_target_1_gross_return_pct",
        "_target_1_net_return_pct",
        "_stop_gross_return_pct",
        "_stop_net_return_pct",
        "_planned_gross_reward_risk",
        "_planned_net_reward_risk",
        "_planned_break_even_win_rate",
    ]
    summary: dict[str, float | int] = {"sample_count": int(len(enriched))}
    for column in required:
        values = pd.to_numeric(enriched[column], errors="coerce").dropna()
        summary[f"{column.removeprefix('_')}_mean"] = round(float(values.mean()), 6) if not values.empty else 0.0
        summary[f"{column.removeprefix('_')}_median"] = round(float(values.median()), 6) if not values.empty else 0.0
    non_positive_target = pd.to_numeric(enriched["_target_1_net_return_pct"], errors="coerce").le(0)
    summary["target_1_non_positive_after_cost_count"] = int(non_positive_target.sum())
    summary["target_1_non_positive_after_cost_rate"] = round(float(non_positive_target.mean()), 6)
    return summary
