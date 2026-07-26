"""Causal outcome evaluation, attribution, and champion/challenger comparison."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable


def evaluate_decisions(records: Iterable[dict[str, object]]) -> dict[str, object]:
    rows = list(records)
    pnl = [float(row.get("pnl_pct", 0) or 0) for row in rows]
    wins = [value > 0 for value in pnl]
    family: dict[str, list[float]] = defaultdict(list)
    tools: dict[str, list[float]] = defaultdict(list)
    for row, outcome in zip(rows, pnl):
        for item in row.get("family_scores", []) or []:
            if isinstance(item, dict):
                family[str(item.get("family", "unknown"))].append(float(item.get("score", 0) or 0) * outcome)
        technical = row.get("technical_v2") or {}
        if isinstance(technical, dict):
            for item in technical.get("evidence", []) or []:
                if isinstance(item, dict):
                    tools[str(item.get("name", "unknown"))].append(float(item.get("direction", 0) or 0) * outcome)
    return {
        "samples": len(rows),
        "win_rate": round(sum(wins) / len(wins), 4) if wins else None,
        "expectancy_pct": round(sum(pnl) / len(pnl), 6) if pnl else None,
        "family_attribution": {name: round(sum(values) / len(values), 6) for name, values in sorted(family.items())},
        "tool_attribution": {name: round(sum(values) / len(values), 6) for name, values in sorted(tools.items())},
    }


def compare_challengers(champion: dict[str, object], challenger: dict[str, object], *, minimum_samples: int = 50) -> dict[str, object]:
    champion_samples = int(champion.get("samples", 0) or 0)
    challenger_samples = int(challenger.get("samples", 0) or 0)
    eligible = min(champion_samples, challenger_samples) >= minimum_samples
    delta = float(challenger.get("expectancy_pct", 0) or 0) - float(champion.get("expectancy_pct", 0) or 0)
    return {"eligible": eligible, "expectancy_delta_pct": round(delta, 6), "winner": "CHALLENGER" if eligible and delta > 0 else "CHAMPION"}
