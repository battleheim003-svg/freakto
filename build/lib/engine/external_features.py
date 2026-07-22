"""Score optional external market features.

All inputs are treated as additive context. Missing external data does not
penalize a setup because those feeds are optional and may be disabled locally.
"""

from __future__ import annotations

from engine.common import ScoreComponent, safe_float


def score_external_context(row, side: str) -> ScoreComponent:
    reasons: list[str] = []
    warnings: list[str] = []
    points = 0

    volume_ratio = safe_float(row.get("cross_exchange_volume_ratio"), 1.0) or 1.0
    provider_count = int(safe_float(row.get("cross_exchange_provider_count"), 0) or 0)
    sentiment = safe_float(row.get("news_sentiment_score"), 0.0) or 0.0
    onchain = safe_float(row.get("onchain_signal_score"), 0.0) or 0.0

    if provider_count >= 2:
        if volume_ratio >= 1.35:
            points += 4
            reasons.append(f"Cross-exchange volume is elevated ({volume_ratio:.2f}x across {provider_count} venues).")
        elif volume_ratio <= 0.70:
            points -= 2
            warnings.append(f"Cross-exchange volume is weak ({volume_ratio:.2f}x across {provider_count} venues).")

    if side == "LONG":
        if sentiment >= 0.25:
            points += 2
            reasons.append(f"News sentiment supports LONG context ({sentiment:.2f}).")
        elif sentiment <= -0.35:
            points -= 3
            warnings.append(f"News sentiment conflicts with LONG context ({sentiment:.2f}).")

        if onchain >= 0.10:
            points += 2
            reasons.append(f"On-chain activity is expanding ({onchain:.2f}).")
        elif onchain <= -0.15:
            points -= 2
            warnings.append(f"On-chain activity is contracting ({onchain:.2f}).")

    elif side == "SHORT":
        if sentiment <= -0.25:
            points += 2
            reasons.append(f"News sentiment supports SHORT context ({sentiment:.2f}).")
        elif sentiment >= 0.35:
            points -= 3
            warnings.append(f"News sentiment conflicts with SHORT context ({sentiment:.2f}).")

        if onchain <= -0.10:
            points += 2
            reasons.append(f"On-chain activity is contracting ({onchain:.2f}).")
        elif onchain >= 0.15:
            points -= 2
            warnings.append(f"On-chain activity is expanding against SHORT context ({onchain:.2f}).")

    return ScoreComponent(
        name="External Context",
        points=max(-8, min(8, points)),
        max_points=8,
        reasons=reasons,
        warnings=warnings,
    )
