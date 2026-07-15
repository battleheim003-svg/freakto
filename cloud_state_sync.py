from __future__ import annotations

import argparse
import hashlib
import json
import os
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

STATE_PATHS = (
    "logs/decisions.csv",
    "history/freakto_history.db",
    "logs/paper_trading",
    "logs/paper_launch_v2",
    "logs/paper_cycle",
    "logs/fresh_oos",
    "logs/forward_test",
)

EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".lock"}
MAX_FILE_BYTES = 50 * 1024 * 1024


@dataclass(frozen=True)
class StateFile:
    relative_path: str
    size_bytes: int
    sha256: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_state_files(root: Path, configured_paths: Iterable[str] = STATE_PATHS) -> list[Path]:
    files: list[Path] = []
    for configured in configured_paths:
        target = root / configured
        if target.is_file():
            files.append(target)
            continue
        if not target.is_dir():
            continue
        for path in target.rglob("*"):
            if not path.is_file() or path.suffix.lower() in EXCLUDED_SUFFIXES:
                continue
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
            files.append(path)
    return sorted(set(files), key=lambda item: item.as_posix())


def create_state_archive(root: Path, archive_path: Path, manifest_path: Path) -> dict:
    root = root.resolve()
    files = iter_state_files(root)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    entries: list[StateFile] = []
    with tarfile.open(archive_path, "w:gz") as archive:
        for path in files:
            relative = path.resolve().relative_to(root).as_posix()
            archive.add(path, arcname=relative, recursive=False)
            entries.append(StateFile(relative, path.stat().st_size, _sha256(path)))

    manifest = {
        "schema_version": 1,
        "created_at_utc": _utc_now(),
        "archive": archive_path.name,
        "file_count": len(entries),
        "total_bytes": sum(item.size_bytes for item in entries),
        "files": [item.__dict__ for item in entries],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def _safe_member(member: tarfile.TarInfo, destination: Path) -> bool:
    resolved = (destination / member.name).resolve()
    try:
        resolved.relative_to(destination.resolve())
    except ValueError:
        return False
    return not (member.issym() or member.islnk())


def restore_state_archive(root: Path, archive_path: Path) -> dict:
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not archive_path.exists():
        return {"status": "NO_STATE_ARCHIVE", "restored_files": 0}

    restored = 0
    with tarfile.open(archive_path, "r:gz") as archive:
        members = [member for member in archive.getmembers() if _safe_member(member, root)]
        if len(members) != len(archive.getmembers()):
            raise ValueError("Unsafe path or link found in state archive")
        for member in members:
            target = root / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                continue
            with source, target.open("wb") as destination:
                while True:
                    chunk = source.read(1024 * 1024)
                    if not chunk:
                        break
                    destination.write(chunk)
            restored += 1
    return {"status": "RESTORED", "restored_files": restored}


def main() -> int:
    parser = argparse.ArgumentParser(description="Pack or restore Freakto cloud runtime state safely.")
    parser.add_argument("command", choices=("pack", "restore"))
    parser.add_argument("--root", default=".")
    parser.add_argument("--archive", default="cloud_state.tar.gz")
    parser.add_argument("--manifest", default="cloud_state_manifest.json")
    args = parser.parse_args()

    root = Path(args.root)
    archive = Path(args.archive)
    if args.command == "pack":
        result = create_state_archive(root, archive, Path(args.manifest))
    else:
        result = restore_state_archive(root, archive)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
