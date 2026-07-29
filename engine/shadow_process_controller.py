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
    mode: str = "shadow"
    symbols: str = ""


class ShadowProcessController:
    """Start and stop one validated local ``live_paper.py`` virtual worker.

    The historical class name remains for compatibility. ``mode=shadow`` is the
    default; ``mode=learning`` uses an independent lock, metadata, and state root.
    """

    def __init__(
        self,
        project_root: str | Path,
        state_root: str | Path,
        *,
        mode: str = "shadow",
        operational_root: str | Path | None = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.operational_root = Path(operational_root or self.project_root).resolve()
        self.mode = str(mode).strip().lower()
        if self.mode not in {"shadow", "learning"}:
            raise ValueError("worker controller mode must be shadow or learning")
        root = Path(state_root)
        self.state_root = (self.project_root / root).resolve() if not root.is_absolute() else root.resolve()
        self.metadata_file = self.state_root / f"{self.mode}_process.json"
        self.runtime_lock = self.state_root / "runtime.lock"
        self.log_file = self.state_root / f"{self.mode}_worker.log"
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
        if expected not in command or f"--mode {self.mode}" not in command:
            return None
        return pid

    def _lock_metadata(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.runtime_lock.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {}

    def _running_pid(self, metadata: dict[str, Any] | None = None) -> int | None:
        metadata = metadata if metadata is not None else self._metadata()
        candidates = [metadata.get("pid"), self._lock_metadata().get("pid")]
        for candidate in candidates:
            try:
                pid = int(candidate or 0)
            except (TypeError, ValueError):
                continue
            validated = self._validated_process(pid)
            if validated is not None:
                return validated
        return None

    def _remove_stale_runtime_lock(self) -> None:
        if not self.runtime_lock.exists():
            return
        lock_pid = self._lock_metadata().get("pid")
        try:
            parsed_pid = int(lock_pid or 0)
        except (TypeError, ValueError):
            parsed_pid = 0
        if self._validated_process(parsed_pid) is not None:
            raise RuntimeError(f"{self.mode} worker is already running with PID {parsed_pid}")
        try:
            self.runtime_lock.unlink()
        except FileNotFoundError:
            pass

    def _log_tail(self, maximum_chars: int = 1600) -> str:
        try:
            content = self.log_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""
        return content[-maximum_chars:].strip()

    def status(self) -> ShadowProcessStatus:
        metadata = self._metadata()
        pid = self._running_pid(metadata)
        running = pid is not None
        label = self.mode.capitalize()
        message = f"{label} worker is running" if running else f"{label} worker is stopped"
        return ShadowProcessStatus(
            running=running,
            pid=pid,
            started_at_utc=metadata.get("started_at_utc"),
            stopped_at_utc=metadata.get("stopped_at_utc"),
            groups=str(metadata.get("groups", "core")),
            interval_seconds=float(metadata.get("interval_seconds", 300.0)),
            message=message,
            mode=self.mode,
            symbols=str(metadata.get("symbols", "")),
        )

    def start(
        self,
        *,
        groups: str = "core",
        symbols: str = "",
        interval_seconds: float = 300.0,
    ) -> ShadowProcessStatus:
        if not self.script.exists():
            raise FileNotFoundError(f"shadow worker script not found: {self.script}")
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        current = self.status()
        if current.running:
            return current
        self.state_root.mkdir(parents=True, exist_ok=True)
        self._remove_stale_runtime_lock()
        command = [
            sys.executable, "-X", "utf8", str(self.script), "--mode", self.mode,
            "--groups", groups, "--loop", "--interval", str(float(interval_seconds)),
            "--operational-root", str(self.operational_root),
        ]
        normalized_symbols = ",".join(
            item.strip().upper() for item in str(symbols).split(",") if item.strip()
        )
        if normalized_symbols:
            command.extend(["--symbols", normalized_symbols])
        creationflags = 0
        popen_kwargs: dict[str, Any] = {}
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        else:
            popen_kwargs["start_new_session"] = True
        with self.log_file.open("a", encoding="utf-8") as output:
            process = subprocess.Popen(
                command,
                cwd=str(self.operational_root),
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
            "symbols": normalized_symbols,
            "interval_seconds": float(interval_seconds),
            "mode": self.mode,
            "command": command,
        }
        _atomic_json(self.metadata_file, metadata)
        deadline = time.monotonic() + 8.0
        while time.monotonic() < deadline:
            poll = getattr(process, "poll", None)
            if callable(poll) and poll() is not None:
                break
            lock_pid = self._lock_metadata().get("pid")
            try:
                validated_lock_pid = self._validated_process(int(lock_pid or 0))
            except (TypeError, ValueError):
                validated_lock_pid = None
            if validated_lock_pid is not None:
                metadata["pid"] = validated_lock_pid
                _atomic_json(self.metadata_file, metadata)
                return ShadowProcessStatus(
                    True, validated_lock_pid, metadata["started_at_utc"], None,
                    groups, float(interval_seconds), f"{self.mode.capitalize()} worker started",
                    self.mode, normalized_symbols,
                )
            # Test doubles and unusually slow lock visibility can still prove
            # liveness through the exact validated command.
            if not callable(poll) and self._validated_process(process.pid) is not None:
                return ShadowProcessStatus(
                    True, process.pid, metadata["started_at_utc"], None,
                    groups, float(interval_seconds), f"{self.mode.capitalize()} worker started",
                    self.mode, normalized_symbols,
                )
            time.sleep(0.1)
        metadata["pid"] = None
        metadata["stopped_at_utc"] = _utc_now()
        _atomic_json(self.metadata_file, metadata)
        detail = self._log_tail()
        suffix = f"\n{detail}" if detail else ""
        raise RuntimeError(f"{self.mode} worker failed during startup{suffix}")

    def stop(self, timeout_seconds: float = 10.0) -> ShadowProcessStatus:
        metadata = self._metadata()
        pid = self._running_pid(metadata)
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
        # Windows termination does not reliably execute RuntimeLock.__exit__.
        # Remove the lock only after its recorded PID is no longer the exact
        # validated shadow command, so a real worker's lock is never stolen.
        self._remove_stale_runtime_lock()
        metadata["stopped_at_utc"] = _utc_now()
        metadata["pid"] = None
        _atomic_json(self.metadata_file, metadata)
        current = self.status()
        return ShadowProcessStatus(
            False, None, current.started_at_utc, metadata["stopped_at_utc"],
            current.groups, current.interval_seconds,
            f"{self.mode.capitalize()} worker stopped safely", self.mode, current.symbols,
        )

    def restart(
        self,
        *,
        groups: str = "core",
        symbols: str = "",
        interval_seconds: float = 300.0,
    ) -> ShadowProcessStatus:
        self.stop()
        return self.start(groups=groups, symbols=symbols, interval_seconds=interval_seconds)

    def diagnostics(self) -> dict[str, Any]:
        return {**asdict(self.status()), "log_file": str(self.log_file), "metadata_file": str(self.metadata_file)}
