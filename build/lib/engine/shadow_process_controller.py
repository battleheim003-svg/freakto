"""Safe lifecycle controller for the local Freakto shadow worker."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


@dataclass(frozen=True)
class ShadowProcessStatus:
    running: bool
    pid: int | None
    started_at_utc: str | None
    stopped_at_utc: str | None
    groups: str
    interval_seconds: float
    message: str


class ShadowProcessController:
    """Start and stop only the validated local ``live_paper.py`` shadow worker."""

    def __init__(self, project_root: str | Path, state_root: str | Path):
        self.project_root = Path(project_root).resolve()
        root = Path(state_root)
        self.state_root = (self.project_root / root).resolve() if not root.is_absolute() else root.resolve()
        self.metadata_file = self.state_root / "shadow_process.json"
        self.log_file = self.state_root / "shadow_worker.log"
        self.script = (self.project_root / "live_paper.py").resolve()

    def _metadata(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.metadata_file.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _process_command(self, pid: int) -> str:
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command", f"(Get-CimInstance Win32_Process -Filter \"ProcessId = {pid}\").CommandLine"],
                    capture_output=True, text=True, timeout=5, check=False,
                )
                return result.stdout.strip()
            payload = Path(f"/proc/{pid}/cmdline").read_bytes()
            return payload.replace(b"\x00", b" ").decode("utf-8", errors="replace")
        except (OSError, subprocess.SubprocessError):
            return ""

    def _validated_process(self, pid: int | None) -> int | None:
        if not pid or pid <= 0:
            return None
        command = self._process_command(pid).lower().replace("\\", "/")
        expected = str(self.script).lower().replace("\\", "/")
        if expected not in command or "--mode shadow" not in command:
            return None
        return pid

    def status(self) -> ShadowProcessStatus:
        metadata = self._metadata()
        pid = int(metadata.get("pid", 0) or 0)
        running = self._validated_process(pid) is not None
        message = "Shadow worker is running" if running else "Shadow worker is stopped"
        return ShadowProcessStatus(
            running=running,
            pid=pid or None,
            started_at_utc=metadata.get("started_at_utc"),
            stopped_at_utc=metadata.get("stopped_at_utc"),
            groups=str(metadata.get("groups", "core")),
            interval_seconds=float(metadata.get("interval_seconds", 300.0)),
            message=message,
        )

    def start(self, *, groups: str = "core", interval_seconds: float = 300.0) -> ShadowProcessStatus:
        if not self.script.exists():
            raise FileNotFoundError(f"shadow worker script not found: {self.script}")
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        current = self.status()
        if current.running:
            return current
        self.state_root.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable, "-X", "utf8", str(self.script), "--mode", "shadow",
            "--groups", groups, "--loop", "--interval", str(float(interval_seconds)),
        ]
        creationflags = 0
        popen_kwargs: dict[str, Any] = {}
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        else:
            popen_kwargs["start_new_session"] = True
        with self.log_file.open("a", encoding="utf-8") as output:
            process = subprocess.Popen(
                command,
                cwd=str(self.project_root),
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                creationflags=creationflags,
                close_fds=True,
                **popen_kwargs,
            )
        metadata = {
            "schema_version": 1,
            "pid": process.pid,
            "started_at_utc": _utc_now(),
            "stopped_at_utc": None,
            "groups": groups,
            "interval_seconds": float(interval_seconds),
            "command": command,
        }
        _atomic_json(self.metadata_file, metadata)
        return ShadowProcessStatus(True, process.pid, metadata["started_at_utc"], None, groups, float(interval_seconds), "Shadow worker started")

    def stop(self, timeout_seconds: float = 10.0) -> ShadowProcessStatus:
        metadata = self._metadata()
        pid = self._validated_process(int(metadata.get("pid", 0) or 0))
        if pid is not None:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(pid), "/T"], capture_output=True, timeout=timeout_seconds, check=False)
                if self._validated_process(pid) is not None:
                    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=5, check=False)
            else:
                try:
                    os.killpg(os.getpgid(pid), 15)
                except (ProcessLookupError, PermissionError):
                    pass
                deadline = time.monotonic() + timeout_seconds
                while self._validated_process(pid) is not None and time.monotonic() < deadline:
                    time.sleep(0.1)
                if self._validated_process(pid) is not None:
                    try:
                        os.killpg(os.getpgid(pid), 9)
                    except (ProcessLookupError, PermissionError):
                        pass
        metadata["stopped_at_utc"] = _utc_now()
        metadata["pid"] = None
        _atomic_json(self.metadata_file, metadata)
        current = self.status()
        return ShadowProcessStatus(False, None, current.started_at_utc, metadata["stopped_at_utc"], current.groups, current.interval_seconds, "Shadow worker stopped safely")

    def restart(self, *, groups: str = "core", interval_seconds: float = 300.0) -> ShadowProcessStatus:
        self.stop()
        return self.start(groups=groups, interval_seconds=interval_seconds)

    def diagnostics(self) -> dict[str, Any]:
        return {**asdict(self.status()), "log_file": str(self.log_file), "metadata_file": str(self.metadata_file)}
