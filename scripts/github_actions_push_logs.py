#!/usr/bin/env python3
"""
Push Freakto runtime logs to a separate GitHub branch (`data-logs` by default).

Security model:
- Only whitelisted runtime data paths are copied.
- .env, keys, Python code, and repository source files are not copied.
- The data branch is separate from main so project code stays clean.

Used by: .github/workflows/freakto-forward-test.yml
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_BRANCH = os.getenv("FREAKTO_LOG_BRANCH", "data-logs")
WORKTREE = ROOT / ".gha_data_worktree"

ALLOWED_DIRS = ["logs", "history"]
ALLOWED_SUFFIXES = {
    ".csv",
    ".json",
    ".md",
    ".txt",
    ".log",
    ".db",
    ".sqlite",
    ".sqlite3",
}
BLOCKED_NAMES = {
    ".env",
    ".env.local",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}


def run(cmd: list[str], *, cwd: Path = ROOT, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, check=check)


def print_step(message: str) -> None:
    print(f"[freakto-push-logs] {message}")


def safe_copy_file(src: Path, dst: Path) -> bool:
    if src.name in BLOCKED_NAMES:
        return False
    if src.suffix.lower() not in ALLOWED_SUFFIXES:
        return False
    # Extra guard: never copy token/key-looking files.
    lower = src.name.lower()
    if "secret" in lower or "token" in lower or "key" in lower and src.suffix.lower() not in {".md", ".txt"}:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def prepare_worktree() -> None:
    if WORKTREE.exists():
        shutil.rmtree(WORKTREE, ignore_errors=True)

    run(["git", "fetch", "origin", DATA_BRANCH], check=False)
    remote_check = run(["git", "rev-parse", "--verify", f"origin/{DATA_BRANCH}"], check=False)

    if remote_check.returncode == 0:
        run(["git", "worktree", "add", "-B", DATA_BRANCH, str(WORKTREE), f"origin/{DATA_BRANCH}"], check=True)
    else:
        # Create an orphan data branch in a detached worktree.
        run(["git", "worktree", "add", "--detach", str(WORKTREE), "HEAD"], check=True)
        run(["git", "switch", "--orphan", DATA_BRANCH], cwd=WORKTREE, check=True)
        # Remove source files from the orphan branch checkout.
        for child in WORKTREE.iterdir():
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)


def clean_data_branch_files() -> None:
    for child in WORKTREE.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


def copy_runtime_data() -> int:
    copied = 0
    for rel_dir in ALLOWED_DIRS:
        src_dir = ROOT / rel_dir
        if not src_dir.exists():
            continue
        for src in src_dir.rglob("*"):
            if not src.is_file():
                continue
            rel = src.relative_to(ROOT)
            dst = WORKTREE / rel
            if safe_copy_file(src, dst):
                copied += 1
    return copied


def write_branch_readme(copied_count: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    text = f"""# Freakto Runtime Data Branch

This branch is managed automatically by GitHub Actions.

It stores non-secret Freakto runtime outputs only:

- `logs/**/*.csv`
- `logs/**/*.json`
- `logs/**/*.md`
- `logs/**/*.txt`
- `history/*.db`

Do not manually add `.env`, API keys, Telegram tokens, private keys, or source-code changes here.

Last update UTC: `{now}`
Copied files: `{copied_count}`
"""
    (WORKTREE / "README_DATA_LOGS.md").write_text(text, encoding="utf-8")


def commit_and_push() -> None:
    run(["git", "config", "user.name", "github-actions[bot]"], cwd=WORKTREE, check=True)
    run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=WORKTREE, check=True)
    run(["git", "add", "-A"], cwd=WORKTREE, check=True)

    status = run(["git", "status", "--porcelain"], cwd=WORKTREE, check=True)
    if not status.stdout.strip():
        print_step("No log changes to commit.")
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    run(["git", "commit", "-m", f"Update Freakto runtime logs - {now}"], cwd=WORKTREE, check=True)
    run(["git", "push", "origin", f"HEAD:{DATA_BRANCH}"], cwd=WORKTREE, check=True)
    print_step(f"Pushed logs to branch '{DATA_BRANCH}'.")


def cleanup() -> None:
    # Remove worktree registration safely.
    run(["git", "worktree", "remove", "--force", str(WORKTREE)], check=False)
    if WORKTREE.exists():
        shutil.rmtree(WORKTREE, ignore_errors=True)


def main() -> None:
    print_step(f"root={ROOT}")
    print_step(f"branch={DATA_BRANCH}")
    try:
        prepare_worktree()
        clean_data_branch_files()
        copied = copy_runtime_data()
        write_branch_readme(copied)
        print_step(f"Copied {copied} runtime files into data branch worktree.")
        commit_and_push()
    finally:
        cleanup()


if __name__ == "__main__":
    main()
