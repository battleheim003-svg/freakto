"""Backtest-style diagnostics for immutable Airdrop Radar predictions."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from airdrop.outcomes.tracker import OutcomeTracker, RESOLVED_STATUSES


@dataclass(frozen=True)
class AirdropBacktestReport:
    status: str
    predictions: int
    observed_projects: int
    resolved_projects: int
    pending_projects: int
    success_rate_pct: float | None
    total_net_reward_usd: float
    average_net_reward_usd: float | None
    min_resolved_required: int
    buckets: tuple[dict, ...]
    blockers: tuple[str, ...]
    notes: tuple[str, ...]


def build_backtest_report(
    tracker: OutcomeTracker,
    *,
    min_resolved: int = 30,
) -> AirdropBacktestReport:
    """Evaluate the first prediction against the latest known observation.

    Pending projects are right-censored and excluded from success-rate and
    reward averages. This prevents unresolved projects from becoming false
    negatives.
    """
    with tracker.connect() as connection:
        predictions = int(
            connection.execute("SELECT COUNT(*) FROM prediction_snapshots").fetchone()[0]
        )
        rows = connection.execute(
            """
            WITH first_prediction AS (
                SELECT p.*
                FROM prediction_snapshots p
                JOIN (
                    SELECT identity, MIN(predicted_at) AS predicted_at
                    FROM prediction_snapshots GROUP BY identity
                ) first
                ON first.identity=p.identity AND first.predicted_at=p.predicted_at
            ),
            latest_outcome AS (
                SELECT o.*
                FROM outcome_observations o
                JOIN (
                    SELECT identity, MAX(observed_at) AS observed_at
                    FROM outcome_observations GROUP BY identity
                ) latest
                ON latest.identity=o.identity AND latest.observed_at=o.observed_at
            )
            SELECT p.identity, p.score, p.predicted_at, o.observed_at, o.status,
                   o.eligible, o.claimed, o.gross_reward_usd, o.cost_usd
            FROM first_prediction p
            LEFT JOIN latest_outcome o ON o.identity=p.identity
            ORDER BY p.predicted_at, p.identity
            """
        ).fetchall()

    frame = pd.DataFrame.from_records([dict(row) for row in rows])
    if frame.empty:
        return AirdropBacktestReport(
            status="RESEARCH_CANDIDATE",
            predictions=predictions,
            observed_projects=0,
            resolved_projects=0,
            pending_projects=0,
            success_rate_pct=None,
            total_net_reward_usd=0.0,
            average_net_reward_usd=None,
            min_resolved_required=max(1, int(min_resolved)),
            buckets=(),
            blockers=("NO_PREDICTION_SNAPSHOTS",),
            notes=("Pending projects are excluded from resolved metrics.",),
        )

    observed = frame["status"].notna()
    resolved = frame["status"].isin(RESOLVED_STATUSES)
    pending = ~resolved
    resolved_frame = frame.loc[resolved].copy()
    if not resolved_frame.empty:
        reward = pd.to_numeric(
            resolved_frame["gross_reward_usd"], errors="coerce"
        ).fillna(0.0)
        cost = pd.to_numeric(resolved_frame["cost_usd"], errors="coerce").fillna(0.0)
        resolved_frame["net_reward_usd"] = reward - cost
        resolved_frame["success"] = resolved_frame["net_reward_usd"] > 0
    else:
        resolved_frame["net_reward_usd"] = pd.Series(dtype=float)
        resolved_frame["success"] = pd.Series(dtype=bool)

    bucket_rows: list[dict] = []
    if not resolved_frame.empty:
        resolved_frame["score_bucket"] = pd.cut(
            resolved_frame["score"],
            bins=[-0.1, 39, 54, 69, 84, 100],
            labels=["0-39", "40-54", "55-69", "70-84", "85-100"],
        )
        for bucket, part in resolved_frame.groupby(
            "score_bucket", observed=False, sort=True
        ):
            bucket_rows.append(
                {
                    "score_bucket": str(bucket),
                    "resolved": len(part),
                    "success_rate_pct": round(float(part["success"].mean() * 100), 3),
                    "average_net_reward_usd": round(
                        float(part["net_reward_usd"].mean()), 4
                    ),
                }
            )

    required = max(1, int(min_resolved))
    blockers: list[str] = []
    if len(resolved_frame) < required:
        blockers.append(f"INSUFFICIENT_RESOLVED_SAMPLE:{len(resolved_frame)}<{required}")
    if not observed.any():
        blockers.append("NO_OUTCOME_OBSERVATIONS")

    total_net = (
        float(resolved_frame["net_reward_usd"].sum()) if not resolved_frame.empty else 0.0
    )
    average_net = (
        float(resolved_frame["net_reward_usd"].mean())
        if not resolved_frame.empty
        else None
    )
    success_rate = (
        float(resolved_frame["success"].mean() * 100)
        if not resolved_frame.empty
        else None
    )
    return AirdropBacktestReport(
        status="PASSED" if not blockers else "RESEARCH_CANDIDATE",
        predictions=predictions,
        observed_projects=int(observed.sum()),
        resolved_projects=len(resolved_frame),
        pending_projects=int(pending.sum()),
        success_rate_pct=None if success_rate is None else round(success_rate, 3),
        total_net_reward_usd=round(total_net, 4),
        average_net_reward_usd=(
            None if average_net is None else round(average_net, 4)
        ),
        min_resolved_required=required,
        buckets=tuple(bucket_rows),
        blockers=tuple(blockers),
        notes=(
            "The first stored prediction is used to reduce post-signal information leakage.",
            "Pending and unobserved projects are right-censored, not counted as failures.",
            "PASSED indicates sample/report completeness, not profitability or Live readiness.",
        ),
    )
