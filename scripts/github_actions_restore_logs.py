#!/usr/bin/env python3
"""
Restore Freakto runtime logs from the GitHub `data-logs` branch.

This script is intentionally conservative:
- It only restores runtime data folders such as logs/ and history/.
- It never reads or writes .env or secret files.
- It exits successfully if the data branch does not exist yet.

Used by: .github/workflows/freakto-forward-test.yml
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

DATA_BRANCH = os.getenv("FREAKTO_LOG_BRANCH", "data-logs")
RESTORE_PATHS = ["logs", "history"]

ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / ".gha_data_restore"


def run(cmd: list[str], *, check: bool = False, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=check)


def print_step(message: str) -> None:
    print(f"[freakto-restore-logs] {message}")


def branch_exists() -> bool:
    fetch = run(["git", "fetch", "origin", DATA_BRANCH, "--depth=1"], check=False)
    if fetch.returncode != 0:
        print_step(f"data branch '{DATA_BRANCH}' not found yet. Starting with empty runtime logs.")
        if fetch.stderr.strip():
            print_step(fetch.stderr.strip().splitlines()[-1])
        return False
    return True


def clean_tmp() -> None:
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR, ignore_errors=True)


def restore_from_branch() -> None:
    clean_tmp()
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    # Archive only allowed runtime paths from the remote data branch.
    archive = run([
        "git",
        "archive",
        f"origin/{DATA_BRANCH}",
        *RESTORE_PATHS,
    ], check=False)

    if archive.returncode != 0:
        print_step("No logs/history paths found in data branch yet.")
        clean_tmp()
        return

    # git archive wrote binary to stdout; rerun in binary mode for extraction.
    proc = subprocess.run(
        ["git", "archive", f"origin/{DATA_BRANCH}", *RESTORE_PATHS],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        print_step("Could not archive data branch paths; continuing with current workspace logs.")
        clean_tmp()
        return

    tar_proc = subprocess.run(
        ["tar", "-xf", "-", "-C", str(TMP_DIR)],
        input=proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if tar_proc.returncode != 0:
        print_step("Could not extract data branch archive; continuing with current workspace logs.")
        clean_tmp()
        return

    restored = []
    for rel in RESTORE_PATHS:
        src = TMP_DIR / rel
        dst = ROOT / rel
        if not src.exists():
            continue
        if dst.exists():
            shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst)
        restored.append(rel)

    clean_tmp()
    if restored:
        print_step("Restored: " + ", ".join(restored))
    else:
        print_step("No runtime paths restored.")


def ensure_dirs() -> None:
    for rel in [
        "logs/forward_testing",
        "logs/reports",
        "logs/edge_validation",
        "logs/regime_matrix",
        "logs/portfolio_memory",
        "logs/confidence_calibration",
        "logs/monte_carlo",
        "logs/readiness",
        "logs/validation_suite",
        "history",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def main() -> None:
    print_step(f"root={ROOT}")
    if branch_exists():
        restore_from_branch()
    ensure_dirs()
    print_step("done")


if __name__ == "__main__":
    main()
