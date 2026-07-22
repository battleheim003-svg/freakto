"""
engine/historical_edge.py

Historical Edge Engine

این ماژول بررسی می‌کند وضعیت‌های تاریخی مشابه چه نتیجه‌ای داشته‌اند
و بر اساس Win Rate، Stop Rate و Avg Return یک امتیاز مستقل به تصمیم اضافه یا کم می‌کند.
"""

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

from history_db import DB_FILE, init_history_db
from .common import ScoreComponent


@dataclass
class HistoricalEdgeStats:
    matched: int = 0
    evaluated: int = 0
    average_similarity: int = 0
    win_rate: float = 0.0
    loss_rate: float = 0.0
    flat_rate: float = 0.0
    stop_rate: float = 0.0
    t1_rate: float = 0.0
    t2_rate: float = 0.0
    t3_rate: float = 0.0
    avg_24h_return: float = 0.0


def _component_score(components: List[ScoreComponent], name: str) -> int:
    for component in components:
        if component.name == name:
            return component.points
    return 0


def _current_vector(components: List[ScoreComponent], base_score: int):
    return {
        "trend_score": _component_score(components, "Trend"),
        "momentum_score": _component_score(components, "Momentum"),
        "volume_score": _component_score(components, "Volume"),
        "structure_score": _component_score(components, "Structure"),
        "regime_score": _component_score(components, "Regime Adjustment"),
        "risk_penalty": _component_score(components, "Risk Penalty"),
        "score": base_score,
    }


def _distance(current, historical):
    weights = {
        "trend_score": 1.2,
        "momentum_score": 1.2,
        "volume_score": 1.4,
        "structure_score": 1.4,
        "regime_score": 1.0,
        "risk_penalty": 1.0,
        "score": 0.8,
    }

    total = 0.0

    for key, weight in weights.items():
        total += abs(float(current.get(key, 0)) - float(historical.get(key, 0))) * weight

    return total


def _similarity_from_distance(distance):
    similarity = 100 - distance
    return max(0, min(100, int(round(similarity))))


def _load_historical_rows(symbol: str, timeframe: str, side: str, current_timestamp: str):
    init_history_db()

    if not DB_FILE.exists():
        return []

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                s.candle_timestamp,
                s.side,
                s.score,
                s.trend_score,
                s.momentum_score,
                s.volume_score,
                s.structure_score,
                s.regime_score,
                s.risk_penalty,

                o.outcome_label,
                o.return_after_24h_pct,
                o.t1_hit,
                o.t2_hit,
                o.t3_hit,
                o.stop_hit

            FROM snapshots s
            LEFT JOIN snapshot_outcomes o
              ON s.symbol = o.symbol
             AND s.timeframe = o.timeframe
             AND s.candle_timestamp = o.candle_timestamp

            WHERE s.symbol = ?
              AND s.timeframe = ?
              AND s.side = ?
              AND s.candle_timestamp != ?

            ORDER BY s.id DESC
            LIMIT 500
            """,
            (symbol, timeframe, side, str(current_timestamp)),
        ).fetchall()

    return rows


def _calculate_stats(matches) -> HistoricalEdgeStats:
    if not matches:
        return HistoricalEdgeStats()

    evaluated = [
        item for item in matches
        if item["outcome_label"] in {"WIN", "LOSS", "FLAT"}
    ]

    avg_similarity = int(round(sum(item["similarity"] for item in matches) / len(matches)))

    if not evaluated:
        return HistoricalEdgeStats(
            matched=len(matches),
            evaluated=0,
            average_similarity=avg_similarity,
        )

    total = len(evaluated)

    wins = sum(1 for item in evaluated if item["outcome_label"] == "WIN")
    losses = sum(1 for item in evaluated if item["outcome_label"] == "LOSS")
    flats = sum(1 for item in evaluated if item["outcome_label"] == "FLAT")

    stops = sum(1 for item in evaluated if item["stop_hit"])
    t1 = sum(1 for item in evaluated if item["t1_hit"])
    t2 = sum(1 for item in evaluated if item["t2_hit"])
    t3 = sum(1 for item in evaluated if item["t3_hit"])

    returns = [
        item["return_after_24h_pct"]
        for item in evaluated
        if item["return_after_24h_pct"] is not None
    ]

    avg_return = sum(returns) / len(returns) if returns else 0.0

    return HistoricalEdgeStats(
        matched=len(matches),
        evaluated=total,
        average_similarity=avg_similarity,
        win_rate=wins / total * 100,
        loss_rate=losses / total * 100,
        flat_rate=flats / total * 100,
        stop_rate=stops / total * 100,
        t1_rate=t1 / total * 100,
        t2_rate=t2 / total * 100,
        t3_rate=t3 / total * 100,
        avg_24h_return=avg_return,
    )


def _score_from_stats(stats: HistoricalEdgeStats):
    points = 0
    reasons = []
    warnings = []

    if stats.evaluated < 5:
        warnings.append(
            f"نمونه تاریخی قابل ارزیابی کافی نیست؛ فقط {stats.evaluated} نمونه نتیجه‌دار وجود دارد."
        )
        return 0, reasons, warnings

    reasons.append(
        f"{stats.evaluated} نمونه مشابه نتیجه‌دار پیدا شد؛ میانگین شباهت {stats.average_similarity}%."
    )

    if stats.win_rate >= 70:
        points += 8
        reasons.append(f"Win Rate تاریخی قوی است: {stats.win_rate:.1f}%")
    elif stats.win_rate >= 58:
        points += 4
        reasons.append(f"Win Rate تاریخی قابل قبول است: {stats.win_rate:.1f}%")
    elif stats.win_rate <= 42:
        points -= 5
        warnings.append(f"Win Rate تاریخی ضعیف است: {stats.win_rate:.1f}%")

    if stats.avg_24h_return >= 1.5:
        points += 4
        reasons.append(f"میانگین بازده 24h مثبت و خوب است: {stats.avg_24h_return:.2f}%")
    elif stats.avg_24h_return >= 0.3:
        points += 2
        reasons.append(f"میانگین بازده 24h کمی مثبت است: {stats.avg_24h_return:.2f}%")
    elif stats.avg_24h_return <= -0.5:
        points -= 4
        warnings.append(f"میانگین بازده 24h منفی است: {stats.avg_24h_return:.2f}%")

    if stats.t1_rate >= 65:
        points += 3
        reasons.append(f"Target 1 در نمونه‌های مشابه زیاد خورده است: {stats.t1_rate:.1f}%")
    elif stats.t1_rate <= 35:
        points -= 2
        warnings.append(f"نرخ رسیدن به Target 1 پایین است: {stats.t1_rate:.1f}%")

    if stats.stop_rate >= 65:
        points -= 7
        warnings.append(f"Stop Rate تاریخی بالاست: {stats.stop_rate:.1f}%")
    elif stats.stop_rate >= 45:
        points -= 3
        warnings.append(f"Stop Rate تاریخی متوسط/بالاست: {stats.stop_rate:.1f}%")
    elif stats.stop_rate <= 25:
        points += 2
        reasons.append(f"Stop Rate تاریخی پایین است: {stats.stop_rate:.1f}%")

    points = max(-12, min(12, points))

    return points, reasons, warnings


def score_historical_edge(
    symbol: str,
    timeframe: str,
    side: str,
    components: List[ScoreComponent],
    base_score: int,
    current_timestamp: str,
    min_similarity: int = 70,
    limit: int = 20,
) -> ScoreComponent:
    """
    خروجی:
    ScoreComponent با نام Historical Edge

    این کامپوننت می‌تواند مثبت یا منفی باشد:
    - سابقه تاریخی خوب: امتیاز مثبت
    - سابقه تاریخی بد: امتیاز منفی
    """

    if side not in {"LONG", "SHORT"}:
        return ScoreComponent(
            name="Historical Edge",
            points=0,
            max_points=12,
            warnings=["Historical Edge فقط برای LONG/SHORT محاسبه می‌شود."],
        )

    current = _current_vector(components, base_score)

    rows = _load_historical_rows(
        symbol=symbol,
        timeframe=timeframe,
        side=side,
        current_timestamp=current_timestamp,
    )

    matches = []

    for row in rows:
        historical = {
            "trend_score": row["trend_score"] or 0,
            "momentum_score": row["momentum_score"] or 0,
            "volume_score": row["volume_score"] or 0,
            "structure_score": row["structure_score"] or 0,
            "regime_score": row["regime_score"] or 0,
            "risk_penalty": row["risk_penalty"] or 0,
            "score": row["score"] or 0,
        }

        similarity = _similarity_from_distance(_distance(current, historical))

        if similarity >= min_similarity:
            matches.append({
                "similarity": similarity,
                "outcome_label": row["outcome_label"] or "",
                "return_after_24h_pct": row["return_after_24h_pct"],
                "t1_hit": int(row["t1_hit"] or 0),
                "t2_hit": int(row["t2_hit"] or 0),
                "t3_hit": int(row["t3_hit"] or 0),
                "stop_hit": int(row["stop_hit"] or 0),
            })

    matches = sorted(matches, key=lambda item: item["similarity"], reverse=True)[:limit]
    stats = _calculate_stats(matches)

    points, reasons, warnings = _score_from_stats(stats)

    if stats.matched == 0:
        warnings.append("هیچ نمونه تاریخی مشابهی برای Historical Edge پیدا نشد.")
    elif stats.evaluated > 0:
        reasons.append(
            f"Historical Edge Summary: Win {stats.win_rate:.1f}% | "
            f"Stop {stats.stop_rate:.1f}% | Avg 24h {stats.avg_24h_return:.2f}%"
        )

    return ScoreComponent(
        name="Historical Edge",
        points=points,
        max_points=12,
        reasons=reasons,
        warnings=warnings,
    )