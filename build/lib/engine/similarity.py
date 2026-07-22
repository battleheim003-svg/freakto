from dataclasses import dataclass, field
from typing import List
import sqlite3

from history_db import DB_FILE, init_history_db


@dataclass
class SimilarSnapshot:
    similarity: int
    candle_timestamp: str
    side: str
    score: int
    confidence_value: int
    actionability: str
    regime_label: str
    price: float

    outcome_label: str = ""
    return_after_24h_pct: float | None = None
    mfe_pct: float | None = None
    mae_pct: float | None = None
    t1_hit: int = 0
    t2_hit: int = 0
    t3_hit: int = 0
    stop_hit: int = 0


@dataclass
class SimilarityResult:
    found: int
    average_similarity: int
    matches: List[SimilarSnapshot] = field(default_factory=list)
    summary: List[str] = field(default_factory=list)


def _component_score(opportunity, name):
    for component in opportunity.components:
        if component.name == name:
            return component.points
    return 0


def _current_vector(opportunity):
    return {
        "trend_score": _component_score(opportunity, "Trend"),
        "momentum_score": _component_score(opportunity, "Momentum"),
        "volume_score": _component_score(opportunity, "Volume"),
        "structure_score": _component_score(opportunity, "Structure"),
        "regime_score": _component_score(opportunity, "Regime Adjustment"),
        "risk_penalty": _component_score(opportunity, "Risk Penalty"),
        "score": opportunity.score,
        "confidence_value": opportunity.confidence.value,
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
        "confidence_value": 0.8,
    }

    total = 0.0

    for key, weight in weights.items():
        total += abs(float(current.get(key, 0)) - float(historical.get(key, 0))) * weight

    return total


def _similarity_from_distance(distance):
    similarity = 100 - distance
    return max(0, min(100, int(round(similarity))))


def _current_timestamp(opportunity):
    return str(opportunity.raw.get("timestamp", "")).strip()


def _summarize_outcomes(matches: List[SimilarSnapshot]) -> List[str]:
    evaluated = [
        item for item in matches
        if item.outcome_label in {"WIN", "LOSS", "FLAT"}
    ]

    if not evaluated:
        return ["هنوز نتیجه تاریخی قابل اتکا برای نمونه‌های مشابه ثبت نشده است."]

    total = len(evaluated)
    wins = sum(1 for item in evaluated if item.outcome_label == "WIN")
    losses = sum(1 for item in evaluated if item.outcome_label == "LOSS")
    flats = sum(1 for item in evaluated if item.outcome_label == "FLAT")

    t1 = sum(1 for item in evaluated if item.t1_hit)
    t2 = sum(1 for item in evaluated if item.t2_hit)
    t3 = sum(1 for item in evaluated if item.t3_hit)
    stops = sum(1 for item in evaluated if item.stop_hit)

    returns = [
        item.return_after_24h_pct
        for item in evaluated
        if item.return_after_24h_pct is not None
    ]

    avg_return = sum(returns) / len(returns) if returns else 0

    return [
        f"نتایج تاریخی موجود برای {total} نمونه مشابه:",
        f"Win Rate: {wins / total * 100:.1f}% | Loss: {losses / total * 100:.1f}% | Flat: {flats / total * 100:.1f}%",
        f"T1: {t1 / total * 100:.1f}% | T2: {t2 / total * 100:.1f}% | T3: {t3 / total * 100:.1f}% | Stop: {stops / total * 100:.1f}%",
        f"Avg 24h Return: {avg_return:.2f}%",
    ]


def find_similar_snapshots(opportunity, limit=10, min_similarity=70) -> SimilarityResult:
    init_history_db()

    if not DB_FILE.exists():
        return SimilarityResult(
            found=0,
            average_similarity=0,
            summary=["هنوز دیتابیس تاریخی ساخته نشده است."],
        )

    current = _current_vector(opportunity)
    current_timestamp = _current_timestamp(opportunity)

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT
                s.candle_timestamp,
                s.side,
                s.score,
                s.confidence_value,
                s.actionability,
                s.regime_label,
                s.price,
                s.trend_score,
                s.momentum_score,
                s.volume_score,
                s.structure_score,
                s.regime_score,
                s.risk_penalty,

                o.outcome_label,
                o.return_after_24h_pct,
                o.mfe_pct,
                o.mae_pct,
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
              AND s.candle_timestamp != ?

            ORDER BY s.id DESC
            LIMIT 500
            """,
            (
                opportunity.symbol,
                opportunity.timeframe,
                current_timestamp,
            ),
        ).fetchall()

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
            "confidence_value": row["confidence_value"] or 0,
        }

        similarity = _similarity_from_distance(_distance(current, historical))

        if similarity >= min_similarity:
            matches.append(
                SimilarSnapshot(
                    similarity=similarity,
                    candle_timestamp=row["candle_timestamp"],
                    side=row["side"],
                    score=row["score"],
                    confidence_value=row["confidence_value"],
                    actionability=row["actionability"],
                    regime_label=row["regime_label"],
                    price=float(row["price"] or 0),

                    outcome_label=row["outcome_label"] or "",
                    return_after_24h_pct=row["return_after_24h_pct"],
                    mfe_pct=row["mfe_pct"],
                    mae_pct=row["mae_pct"],
                    t1_hit=int(row["t1_hit"] or 0),
                    t2_hit=int(row["t2_hit"] or 0),
                    t3_hit=int(row["t3_hit"] or 0),
                    stop_hit=int(row["stop_hit"] or 0),
                )
            )

    matches = sorted(matches, key=lambda item: item.similarity, reverse=True)[:limit]

    if not matches:
        return SimilarityResult(
            found=0,
            average_similarity=0,
            summary=[
                "هنوز Snapshot مشابه کافی پیدا نشد.",
                "با اجرای بیشتر مانیتور، حافظه تاریخی غنی‌تر می‌شود.",
            ],
        )

    avg = int(round(sum(item.similarity for item in matches) / len(matches)))

    summary = [
        f"{len(matches)} وضعیت تاریخی مشابه پیدا شد.",
        f"میانگین شباهت: {avg}%",
    ]

    summary.extend(_summarize_outcomes(matches))

    return SimilarityResult(
        found=len(matches),
        average_similarity=avg,
        matches=matches,
        summary=summary,
    )


def format_similarity_for_console(result: SimilarityResult):
    print("\n" + "=" * 70)
    print("🧬 Historical Similarity Engine")
    print("=" * 70)

    for line in result.summary:
        print(line)

    if result.matches:
        print("\nTop Similar Snapshots:")
        for item in result.matches[:5]:
            outcome = item.outcome_label or "NO_OUTCOME"
            ret = ""
            if item.return_after_24h_pct is not None:
                ret = f" | 24h {item.return_after_24h_pct:.2f}%"

            print(
                f"- {item.similarity}% | {item.candle_timestamp} | "
                f"{item.side} | Score {item.score} | Confidence {item.confidence_value}% | "
                f"{item.actionability} | {item.regime_label} | {outcome}{ret}"
            )

    print("=" * 70)


def format_similarity_for_telegram(result: SimilarityResult):
    lines = ["*Historical Similarity:*"]

    for line in result.summary:
        lines.append(f"- {line}")

    if result.matches:
        lines.append("- نزدیک‌ترین نمونه‌ها:")
        for item in result.matches[:3]:
            outcome = item.outcome_label or "NO_OUTCOME"
            ret = ""
            if item.return_after_24h_pct is not None:
                ret = f" | 24h {item.return_after_24h_pct:.2f}%"

            lines.append(
                f"  • `{item.similarity}%` | {item.side} | "
                f"Score {item.score} | {outcome}{ret}"
            )

    return lines