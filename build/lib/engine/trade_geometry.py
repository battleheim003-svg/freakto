"""Execution-cost and trade-geometry primitives for Freakto research.

The module reconstructs pre-trade risk units from recorded replay geometry and
simulates alternative stop/target layouts from direction-adjusted MFE/MAE and
fixed-horizon returns.  It is intentionally independent from runtime trading.

Important limitation
--------------------
Replay rows currently contain MFE/MAE summaries, not the complete candle path.
Therefore path-sensitive break-even and trailing policies are reported under an
explicit path assumption.  Only conservative fixed-geometry simulations should
be considered promotion-eligible until full intrabar paths are recorded.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Optional

import numpy as np
import pandas as pd

from .outcome_economics import enrich_planned_economics, fixed_horizon_return, numeric_series

VERSION = "v10.9.0"
SUPPORTED_MANAGEMENT_POLICIES = ("NONE", "BREAK_EVEN", "TRAILING")
SUPPORTED_PATH_ASSUMPTIONS = ("STOP_FIRST", "MANAGEMENT_FIRST")


@dataclass(frozen=True)
class GeometrySpec:
    horizon_candles: int = 12
    stop_multiplier: float = 1.0
    reward_risk: float = 1.5
    management_policy: str = "NONE"
    break_even_trigger_r: float = 1.0
    trailing_trigger_r: float = 1.0
    trailing_distance_r: float = 0.75
    path_assumption: str = "STOP_FIRST"
    cost_multiplier: float = 1.0

    def validate(self) -> None:
        if self.horizon_candles not in (1, 3, 6, 12):
            raise ValueError("horizon_candles must be one of 1, 3, 6, or 12.")
        if self.stop_multiplier <= 0 or self.reward_risk <= 0:
            raise ValueError("stop_multiplier and reward_risk must be positive.")
        if self.management_policy not in SUPPORTED_MANAGEMENT_POLICIES:
            raise ValueError(f"Unsupported management_policy: {self.management_policy}")
        if self.path_assumption not in SUPPORTED_PATH_ASSUMPTIONS:
            raise ValueError(f"Unsupported path_assumption: {self.path_assumption}")
        if self.break_even_trigger_r <= 0 or self.trailing_trigger_r <= 0:
            raise ValueError("management trigger R values must be positive.")
        if self.trailing_distance_r <= 0:
            raise ValueError("trailing_distance_r must be positive.")
        if self.cost_multiplier < 0:
            raise ValueError("cost_multiplier must be non-negative.")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class GeometryDiagnostics:
    sample_count: int
    target_hit_count: int
    stop_hit_count: int
    both_hit_count: int
    neither_hit_count: int
    break_even_count: int
    trailing_count: int
    volatility_source: str
    path_assumption: str

    def to_dict(self) -> dict:
        return asdict(self)


def _first_numeric_column(frame: pd.DataFrame, candidates: tuple[str, ...]) -> tuple[pd.Series, Optional[str]]:
    for column in candidates:
        if column not in frame.columns:
            continue
        values = pd.to_numeric(frame[column], errors="coerce").astype(float)
        if values.notna().any():
            return values, column
    return pd.Series(float("nan"), index=frame.index, dtype=float), None


def derive_geometry_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add pre-trade geometry and execution-cost features.

    Native ATR percentages are preferred when a future recorder provides one.
    The current replay schema lacks ATR, so the planned stop distance is used as
    a transparent risk-unit proxy.  No future-return field is used here.
    """

    output = frame.copy()
    if "_entry_price" not in output.columns or "_stop_gross_return_pct" not in output.columns:
        output = enrich_planned_economics(output)

    atr_values, atr_column = _first_numeric_column(
        output,
        ("atr_pct", "atr_14_pct", "atr_percent", "atr14_pct", "normalized_atr_pct"),
    )
    planned_stop = numeric_series(output, "_stop_gross_return_pct").abs()
    planned_target = numeric_series(output, "_target_1_gross_return_pct").clip(lower=0.0)
    cost = numeric_series(output, "_round_trip_cost_pct").clip(lower=0.0)

    native_atr = atr_values.where(atr_values.gt(0))
    risk_unit = native_atr.where(native_atr.notna(), planned_stop.where(planned_stop.gt(0)))
    source = pd.Series("PLANNED_STOP_PROXY", index=output.index, dtype=object)
    if atr_column is not None:
        source.loc[native_atr.notna()] = f"ATR:{atr_column}"

    output["_risk_unit_pct"] = risk_unit
    output["_risk_unit_source"] = source
    output["_planned_stop_gross_pct"] = planned_stop
    output["_planned_target_1_gross_pct"] = planned_target
    output["_execution_cost_pct"] = cost
    output["_planned_cost_to_target"] = cost / planned_target.replace(0.0, np.nan)
    output["_planned_cost_to_risk"] = cost / planned_stop.replace(0.0, np.nan)
    output["_planned_target_cost_multiple"] = planned_target / cost.replace(0.0, np.nan)
    return output


def candidate_pretrade_features(frame: pd.DataFrame, spec: GeometrySpec) -> pd.DataFrame:
    """Return candidate geometry derived only from information known at entry."""

    spec.validate()
    enriched = frame if "_risk_unit_pct" in frame.columns else derive_geometry_features(frame)
    output = pd.DataFrame(index=enriched.index)
    risk = numeric_series(enriched, "_risk_unit_pct") * float(spec.stop_multiplier)
    target = risk * float(spec.reward_risk)
    cost = numeric_series(enriched, "_execution_cost_pct").clip(lower=0.0) * float(spec.cost_multiplier)
    target_net = target - cost
    stop_net_loss = risk + cost
    output["risk_gross_pct"] = risk
    output["target_gross_pct"] = target
    output["execution_cost_pct"] = cost
    output["target_net_pct"] = target_net
    output["stop_net_loss_pct"] = stop_net_loss
    output["net_reward_risk"] = target_net.clip(lower=0.0) / stop_net_loss.replace(0.0, np.nan)
    output["break_even_win_rate"] = stop_net_loss / (target_net.clip(lower=0.0) + stop_net_loss).replace(0.0, np.nan)
    output["cost_to_target"] = cost / target.replace(0.0, np.nan)
    output["cost_to_risk"] = cost / risk.replace(0.0, np.nan)
    output["target_cost_multiple"] = target / cost.replace(0.0, np.nan)
    output["valid_geometry"] = (
        risk.gt(0)
        & target.gt(0)
        & target_net.gt(0)
        & np.isfinite(risk)
        & np.isfinite(target)
    )
    return output


def simulate_geometry_returns(
    frame: pd.DataFrame,
    spec: GeometrySpec,
) -> tuple[pd.Series, GeometryDiagnostics, pd.DataFrame]:
    """Simulate net returns for one geometry specification.

    MFE is expected to be positive favorable excursion and MAE negative adverse
    excursion, both already direction-adjusted by the replay recorder.
    Alternative target/stop ordering cannot be known from aggregate MFE/MAE.
    ``STOP_FIRST`` is conservative. ``MANAGEMENT_FIRST`` is a diagnostic upper
    bound for break-even/trailing behavior and is not promotion eligible.
    """

    spec.validate()
    enriched = frame if "_risk_unit_pct" in frame.columns else derive_geometry_features(frame)
    pretrade = candidate_pretrade_features(enriched, spec)
    risk = pretrade["risk_gross_pct"]
    target = pretrade["target_gross_pct"]
    cost = pretrade["execution_cost_pct"]
    mfe = numeric_series(enriched, "mfe_pct").clip(lower=0.0)
    adverse = (-numeric_series(enriched, "mae_pct")).clip(lower=0.0)
    horizon_gross = fixed_horizon_return(enriched, spec.horizon_candles, net=False)

    target_hit = mfe.ge(target) & pretrade["valid_geometry"]
    stop_hit = adverse.ge(risk) & pretrade["valid_geometry"]
    both_hit = target_hit & stop_hit
    only_target = target_hit & ~stop_hit
    only_stop = stop_hit & ~target_hit
    neither = ~target_hit & ~stop_hit & pretrade["valid_geometry"]

    gross_return = horizon_gross.clip(lower=-risk, upper=target)
    gross_return = gross_return.where(pretrade["valid_geometry"])
    gross_return.loc[only_target] = target.loc[only_target]
    gross_return.loc[only_stop] = -risk.loc[only_stop]
    if spec.path_assumption == "STOP_FIRST":
        gross_return.loc[both_hit] = -risk.loc[both_hit]
    else:
        gross_return.loc[both_hit] = target.loc[both_hit]

    break_even_mask = pd.Series(False, index=enriched.index)
    trailing_mask = pd.Series(False, index=enriched.index)
    trigger = risk * float(spec.break_even_trigger_r)

    if spec.management_policy == "BREAK_EVEN":
        activated = mfe.ge(trigger) & ~target_hit & pretrade["valid_geometry"]
        if spec.path_assumption == "MANAGEMENT_FIRST":
            break_even_mask = activated & stop_hit
            gross_return.loc[break_even_mask] = 0.0
        else:
            # Conservative: management helps only rows that did not reach the full stop.
            break_even_mask = activated & ~stop_hit & horizon_gross.lt(0)
            gross_return.loc[break_even_mask] = 0.0

    elif spec.management_policy == "TRAILING":
        trailing_trigger = risk * float(spec.trailing_trigger_r)
        activated = mfe.ge(trailing_trigger) & ~target_hit & pretrade["valid_geometry"]
        trailing_floor = (mfe - risk * float(spec.trailing_distance_r)).clip(lower=0.0)
        trailing_floor = pd.concat([trailing_floor, target], axis=1).min(axis=1)
        if spec.path_assumption == "MANAGEMENT_FIRST":
            trailing_mask = activated
        else:
            trailing_mask = activated & ~stop_hit
        gross_return.loc[trailing_mask] = pd.concat(
            [gross_return.loc[trailing_mask], trailing_floor.loc[trailing_mask]], axis=1
        ).max(axis=1)

    net_return = gross_return - cost
    net_return = net_return.where(pretrade["valid_geometry"] & horizon_gross.notna())

    source_counts = enriched.loc[net_return.notna(), "_risk_unit_source"].astype(str).value_counts()
    volatility_source = source_counts.index[0] if not source_counts.empty else "UNKNOWN"
    diagnostics = GeometryDiagnostics(
        sample_count=int(net_return.notna().sum()),
        target_hit_count=int(target_hit.sum()),
        stop_hit_count=int(stop_hit.sum()),
        both_hit_count=int(both_hit.sum()),
        neither_hit_count=int(neither.sum()),
        break_even_count=int(break_even_mask.sum()),
        trailing_count=int(trailing_mask.sum()),
        volatility_source=volatility_source,
        path_assumption=spec.path_assumption,
    )
    detail = pretrade.copy()
    detail["mfe_pct"] = mfe
    detail["adverse_excursion_pct"] = adverse
    detail["target_hit"] = target_hit
    detail["stop_hit"] = stop_hit
    detail["both_hit"] = both_hit
    detail["break_even_applied"] = break_even_mask
    detail["trailing_applied"] = trailing_mask
    detail["simulated_net_return_pct"] = net_return
    return net_return, diagnostics, detail


def geometry_filter_mask(
    pretrade: pd.DataFrame,
    *,
    minimum_target_cost_multiple: float = 0.0,
    maximum_cost_to_risk: float = math.inf,
    minimum_net_reward_risk: float = 0.0,
) -> pd.Series:
    """Build an entry-time cost/geometry gate without future information."""

    return (
        pretrade["valid_geometry"].fillna(False)
        & pretrade["target_cost_multiple"].fillna(-math.inf).ge(minimum_target_cost_multiple)
        & pretrade["cost_to_risk"].fillna(math.inf).le(maximum_cost_to_risk)
        & pretrade["net_reward_risk"].fillna(-math.inf).ge(minimum_net_reward_risk)
    )
