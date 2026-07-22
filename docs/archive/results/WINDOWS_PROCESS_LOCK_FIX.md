# Windows Process Lock Fix

## Problem

`ProcessLock._pid_alive()` used `os.kill(pid, 0)` as a PID liveness probe. That is a Unix idiom. On Windows, calling it against the current pytest PID can generate a delayed console interrupt, so the lock test appears to pass and then pytest stops with `KeyboardInterrupt` before the next test.

## Fix

- Return immediately when the lock PID is the current process.
- On Windows, query the PID with `OpenProcess` and `GetExitCodeProcess` through `ctypes`.
- Keep `os.kill(pid, 0)` only for POSIX systems.
- Add a regression test proving current-process liveness never calls `os.kill`.

The change affects only process-lock liveness detection. Paper, Strategy, and Live permissions are unchanged.
