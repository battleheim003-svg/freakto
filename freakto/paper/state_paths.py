"""Canonical, crash-safe paths for Paper campaign cycle state."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


CANONICAL_RELATIVE_DIR = Path("logs") / "paper_launch_v2"
LEGACY_RELATIVE_DIR = Path("logs") / "paper_cycle"


@dataclass(frozen=True)
class ArtifactResolution:
    path: Path
    source: str
    conflict: bool = False
    warning: str | None = None


@dataclass(frozen=True)
class PaperStatePaths:
    root: Path

    @property
    def canonical_dir(self) -> Path:
        return self.root / CANONICAL_RELATIVE_DIR

    @property
    def legacy_dir(self) -> Path:
        return self.root / LEGACY_RELATIVE_DIR

    def canonical(self, name: str) -> Path:
        return self.canonical_dir / name

    def legacy(self, name: str) -> Path:
        return self.legacy_dir / name

    def resolve_for_read(self, name: str) -> ArtifactResolution:
        """Prefer canonical state and surface, rather than merge, dual copies."""
        canonical = self.canonical(name)
        legacy = self.legacy(name)
        if canonical.exists():
            conflict = legacy.exists() and not _same_file_content(canonical, legacy)
            warning = None
            if conflict:
                warning = (
                    f"Conflicting canonical and legacy Paper artifacts exist for {name}; "
                    "the canonical artifact was selected without merging."
                )
            return ArtifactResolution(canonical, "CANONICAL", conflict, warning)
        if legacy.exists():
            return ArtifactResolution(
                legacy,
                "LEGACY_FALLBACK",
                warning=f"Using legacy Paper artifact for {name}; new writes remain canonical.",
            )
        return ArtifactResolution(canonical, "MISSING")


def paper_state_paths(root: str | Path) -> PaperStatePaths:
    return PaperStatePaths(Path(root).resolve())


def _digest(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while chunk := handle.read(64 * 1024):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _same_file_content(left: Path, right: Path) -> bool:
    try:
        if left.stat().st_size != right.stat().st_size:
            return False
    except OSError:
        return False
    left_digest = _digest(left)
    return left_digest is not None and left_digest == _digest(right)


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON through an fsynced sibling temporary file and atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


__all__ = [
    "ArtifactResolution",
    "CANONICAL_RELATIVE_DIR",
    "LEGACY_RELATIVE_DIR",
    "PaperStatePaths",
    "atomic_write_json",
    "paper_state_paths",
]
