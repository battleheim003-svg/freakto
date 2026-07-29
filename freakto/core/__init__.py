"""Stable, side-effect-free contracts shared by every Freakto layer."""

from .safety import PAPER_SAFETY, SafetyPolicy
from .runtime import RUNTIME_ENV, RuntimePaths, runtime_paths

__all__ = [
    "PAPER_SAFETY",
    "RUNTIME_ENV",
    "RuntimePaths",
    "SafetyPolicy",
    "runtime_paths",
]
