"""Human-readable and machine-readable technical decision explanations."""

from __future__ import annotations

import json

from freakto.technical_v2.contracts import TechnicalDecision


def decision_markdown(decision: TechnicalDecision) -> str:
    top = sorted(decision.family_scores, key=lambda item: abs(item.score * item.weight), reverse=True)[:3]
    drivers = ", ".join(f"{item.family}={item.score:+.2f}" for item in top)
    warnings = ", ".join(decision.warnings) if decision.warnings else "none"
    return (
        f"**{decision.side}** · score {decision.raw_score:+.2f} · confidence {decision.confidence:.0%}\n\n"
        f"Regime: `{decision.regime.label}` · MTF agreement: {decision.timeframe_agreement:.0%}\n\n"
        f"Main drivers: {drivers}\n\n"
        f"Cost-adjusted R:R: {decision.geometry.cost_adjusted_reward_risk:.2f} · "
        f"Calibration: `{decision.calibration.status}` · Warnings: {warnings}"
    )


def decision_json(decision: TechnicalDecision) -> str:
    return json.dumps(decision.to_dict(), ensure_ascii=False, indent=2)
