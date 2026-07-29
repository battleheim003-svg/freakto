"""Runtime/artifact storage policy independent from repository source paths."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

RUNTIME_ENV = "FREAKTO_RUNTIME_ROOT"


@dataclass(frozen=True)
class RuntimePaths:
    root: Path

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def history(self) -> Path:
        return self.root / "history"

    @property
    def cloud_state(self) -> Path:
        return self.root / "cloud-state"

    @property
    def manifests(self) -> Path:
        return self.root / "manifests"

    def ensure(self) -> "RuntimePaths":
        for path in (self.logs, self.history, self.cloud_state, self.manifests):
            path.mkdir(parents=True, exist_ok=True)
        return self


def runtime_paths(project_root: str | Path = ".") -> RuntimePaths:
    project = Path(project_root).resolve()
    configured = os.getenv(RUNTIME_ENV, "").strip()
    root = Path(configured).expanduser().resolve() if configured else project / ".freakto-runtime"
    return RuntimePaths(root=root)
