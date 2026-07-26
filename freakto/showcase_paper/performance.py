"""Research-only performance summaries for Showcase sessions."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from freakto.showcase_paper.quality import outcome_metrics, quality_admission_reason, quality_profile


def performance_summary(trades: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = [
        trade for trade in trades
        if trade.get("status") == "CLOSED" and trade.get("close_reason") != "SESSION_STOP"
    ]
    base = outcome_metrics(rows)
    wins = [float(row.get("pnl_usdt", 0) or 0) for row in rows if float(row.get("pnl_usdt", 0) or 0) > 0]
    losses = [float(row.get("pnl_usdt", 0) or 0) for row in rows if float(row.get("pnl_usdt", 0) or 0) <= 0]
    average_win = sum(wins) / len(wins) if wins else 0.0
    average_loss = abs(sum(losses) / len(losses)) if losses else 0.0
    break_even = average_loss / (average_win + average_loss) if average_win + average_loss else 0.0
    count = len(rows)
    return {
        **base,
        "expectancy_usdt": round(sum(float(row.get("pnl_usdt", 0) or 0) for row in rows) / count, 6) if count else 0.0,
        "average_win_usdt": round(average_win, 6),
        "average_loss_usdt": round(average_loss, 6),
        "break_even_win_rate": round(break_even, 6),
    }


def grouped_performance(trades: Iterable[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trade in trades:
        if trade.get("status") == "CLOSED":
            buckets[str(trade.get(field, "UNKNOWN") or "UNKNOWN")].append(trade)
    return [
        {field: key, **performance_summary(rows)}
        for key, rows in sorted(buckets.items(), key=lambda item: len(item[1]), reverse=True)
    ]


def walk_forward_quality_comparison(trades: Iterable[dict[str, Any]], *, profile_key: str = "WIN_RATE") -> dict[str, Any]:
    """Compare a profile using only outcomes available before each decision."""
    profile = quality_profile(profile_key)
    history: list[dict[str, Any]] = []
    baseline: list[dict[str, Any]] = []
    candidate: list[dict[str, Any]] = []
    rejection_counts: dict[str, int] = defaultdict(int)
    ordered = sorted(
        (trade for trade in trades if trade.get("status") == "CLOSED"),
        key=lambda trade: str(trade.get("opened_utc", "")),
    )
    for trade in ordered:
        baseline.append(trade)
        signal = dict(trade)
        signal["symbol"] = str(trade.get("symbol", ""))
        reason, _ = quality_admission_reason(signal, history, profile)
        if reason is None:
            candidate.append(trade)
        else:
            rejection_counts[reason] += 1
        history.append(trade)
    return {
        "profile": profile.to_dict(),
        "method": "CAUSAL_WALK_FORWARD_FILTER",
        "official_evidence_eligible": False,
        "baseline": performance_summary(baseline),
        "candidate": performance_summary(candidate),
        "rejections": dict(sorted(rejection_counts.items())),
    }


def performance_report(trades: Iterable[dict[str, Any]], *, session_baseline: int = 0) -> dict[str, Any]:
    rows = list(trades)
    closed = [trade for trade in rows if trade.get("status") == "CLOSED"]
    current = closed[max(0, int(session_baseline)):]
    return {
        "all": performance_summary(closed),
        "session": performance_summary(current),
        "by_quality_mode": grouped_performance(closed, "quality_mode"),
        "by_side": grouped_performance(closed, "side"),
        "by_symbol": grouped_performance(closed, "symbol"),
        "walk_forward_quality": walk_forward_quality_comparison(closed),
        "official_evidence_eligible": False,
    }
