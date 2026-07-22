"""Public engine API with lazy compatibility exports.

Importing any ``engine.*`` submodule must not initialize the complete decision
stack. Several legacy decision modules still import root-level compatibility
scripts, so eager imports here also made the installed ``freakto`` CLI depend on
the repository working directory. Lazy exports preserve ``from engine import``
compatibility without that package-wide side effect.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .decision import DecisionEngine
    from .score import OpportunityV2

__all__ = ["DecisionEngine", "OpportunityV2", "format_opportunity_v2_message"]


def __getattr__(name: str) -> Any:
    if name == "DecisionEngine":
        from .decision import DecisionEngine

        return DecisionEngine
    if name in {"OpportunityV2", "format_opportunity_v2_message"}:
        from .score import OpportunityV2, format_opportunity_v2_message

        return {
            "OpportunityV2": OpportunityV2,
            "format_opportunity_v2_message": format_opportunity_v2_message,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
