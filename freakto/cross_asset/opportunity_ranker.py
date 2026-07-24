"""Fail-closed, research-only ranking of calibrated cross-asset opportunities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = (
    "period_utc",
    "symbol",
    "asset_class",
    "side",
    "raw_score",
    "calibrated_probability",
    "confidence",
    "expected_gross_return_bps",
    "expected_cost_bps",
    "calibration_status",
    "calibration_version",
    "calibration_samples",
    "data_quality_status",
)


@dataclass(frozen=True)
class RankingReport:
    status: str
    input_rows: int
    eligible_rows: int
    periods: int
    selected_periods: int
    no_selection_periods: int
    rankings: tuple[dict[str, Any], ...]
    exclusions: tuple[dict[str, Any], ...]
    blockers: tuple[str, ...]
    notes: tuple[str, ...]


def rank_opportunities(
    frame: pd.DataFrame,
    *,
    min_asset_classes: int = 2,
    min_calibration_samples: int = 100,
    min_probability: float = 0.5,
) -> RankingReport:
    """Rank standardized opportunities without emitting trading decisions."""
    if frame is None or frame.empty:
        return _empty_report("NO_INPUT_ROWS")
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        return _empty_report("MISSING_COLUMNS:" + ",".join(missing), input_rows=len(frame))

    work = frame.copy()
    work["period_utc"] = pd.to_datetime(work["period_utc"], utc=True, errors="coerce")
    numeric_columns = (
        "raw_score",
        "calibrated_probability",
        "confidence",
        "expected_gross_return_bps",
        "expected_cost_bps",
        "calibration_samples",
    )
    for column in numeric_columns:
        work[column] = pd.to_numeric(work[column], errors="coerce")

    exclusions: list[dict[str, Any]] = []
    eligible_indices: list[Any] = []
    for index, row in work.iterrows():
        reasons: list[str] = []
        if pd.isna(row["period_utc"]):
            reasons.append("INVALID_PERIOD")
        if not str(row["symbol"]).strip() or not str(row["asset_class"]).strip():
            reasons.append("MISSING_IDENTITY")
        if str(row["side"]).strip().upper() not in {"LONG", "SHORT"}:
            reasons.append("INVALID_SIDE")
        if not all(np.isfinite(row[column]) for column in numeric_columns):
            reasons.append("INVALID_NUMERIC")
        else:
            if not 0 <= float(row["raw_score"]) <= 100:
                reasons.append("RAW_SCORE_OUT_OF_RANGE")
            if not 0 <= float(row["calibrated_probability"]) <= 1:
                reasons.append("PROBABILITY_OUT_OF_RANGE")
            if not 0 <= float(row["confidence"]) <= 1:
                reasons.append("CONFIDENCE_OUT_OF_RANGE")
            if float(row["expected_cost_bps"]) < 0:
                reasons.append("NEGATIVE_EXPECTED_COST")
            if int(row["calibration_samples"]) < max(1, int(min_calibration_samples)):
                reasons.append("INSUFFICIENT_CALIBRATION_SAMPLE")
        if str(row["calibration_status"]).strip().upper() != "VALIDATED":
            reasons.append("CALIBRATION_NOT_VALIDATED")
        if str(row["data_quality_status"]).strip().upper() != "PASSED":
            reasons.append("DATA_QUALITY_NOT_PASSED")
        if not str(row["calibration_version"]).strip():
            reasons.append("MISSING_CALIBRATION_VERSION")
        if reasons:
            exclusions.append(
                {
                    "row": int(index) if isinstance(index, (int, np.integer)) else str(index),
                    "symbol": str(row["symbol"]),
                    "reasons": reasons,
                }
            )
        else:
            eligible_indices.append(index)

    eligible = work.loc[eligible_indices].copy()
    if eligible.empty:
        return RankingReport(
            status="BLOCKED",
            input_rows=len(frame),
            eligible_rows=0,
            periods=0,
            selected_periods=0,
            no_selection_periods=0,
            rankings=(),
            exclusions=tuple(exclusions),
            blockers=("NO_ELIGIBLE_CALIBRATED_ROWS",),
            notes=_notes(),
        )

    eligible["side"] = eligible["side"].astype(str).str.upper()
    eligible["asset_class"] = eligible["asset_class"].astype(str).str.lower()
    eligible["symbol"] = eligible["symbol"].astype(str).str.upper()
    eligible["expected_net_return_bps"] = (
        eligible["expected_gross_return_bps"] - eligible["expected_cost_bps"]
    )
    # Confidence discounts a provider's own net-return estimate. Probability is
    # kept as a gate/tie-breaker, avoiding a made-up probability-to-return map.
    eligible["rank_score"] = (
        eligible["expected_net_return_bps"] * eligible["confidence"]
    )

    ranking_rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    selected_periods = 0
    no_selection_periods = 0
    for period, part in eligible.groupby("period_utc", sort=True):
        asset_classes = int(part["asset_class"].nunique())
        if asset_classes < max(2, int(min_asset_classes)):
            blockers.append(
                f"INSUFFICIENT_ASSET_CLASSES:{period.isoformat()}:{asset_classes}"
            )
            continue
        ordered = part.sort_values(
            [
                "rank_score",
                "calibrated_probability",
                "confidence",
                "symbol",
            ],
            ascending=[False, False, False, True],
        )
        can_select = bool(
            float(ordered.iloc[0]["expected_net_return_bps"]) > 0
            and float(ordered.iloc[0]["calibrated_probability"]) >= float(min_probability)
        )
        selected_periods += int(can_select)
        no_selection_periods += int(not can_select)
        for rank, (_, row) in enumerate(ordered.iterrows(), start=1):
            ranking_rows.append(
                {
                    "period_utc": period.isoformat(),
                    "symbol": row["symbol"],
                    "asset_class": row["asset_class"],
                    "side": row["side"],
                    "rank": rank,
                    "raw_score": float(row["raw_score"]),
                    "calibrated_probability": float(row["calibrated_probability"]),
                    "confidence": float(row["confidence"]),
                    "expected_gross_return_bps": float(
                        row["expected_gross_return_bps"]
                    ),
                    "expected_cost_bps": float(row["expected_cost_bps"]),
                    "expected_net_return_bps": float(row["expected_net_return_bps"]),
                    "rank_score": float(row["rank_score"]),
                    "calibration_version": str(row["calibration_version"]),
                    "research_selection": bool(rank == 1 and can_select),
                    "selection_status": "SELECTED" if rank == 1 and can_select else (
                        "NO_SELECTION" if rank == 1 else "RANKED_ONLY"
                    ),
                }
            )

    status = "RESEARCH_REPORT" if ranking_rows and not blockers else "BLOCKED"
    return RankingReport(
        status=status,
        input_rows=len(frame),
        eligible_rows=len(eligible),
        periods=int(eligible["period_utc"].nunique()),
        selected_periods=selected_periods,
        no_selection_periods=no_selection_periods,
        rankings=tuple(ranking_rows),
        exclusions=tuple(exclusions),
        blockers=tuple(blockers),
        notes=_notes(),
    )


def _notes() -> tuple[str, ...]:
    return (
        "Output is a research comparison, not a Decision Engine signal.",
        "Every row requires validated calibration and passed data quality.",
        "The ranker may select nothing when estimated net opportunity is non-positive.",
    )


def _empty_report(blocker: str, *, input_rows: int = 0) -> RankingReport:
    return RankingReport(
        status="BLOCKED",
        input_rows=input_rows,
        eligible_rows=0,
        periods=0,
        selected_periods=0,
        no_selection_periods=0,
        rankings=(),
        exclusions=(),
        blockers=(blocker,),
        notes=_notes(),
    )
