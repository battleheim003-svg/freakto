"""Plan or apply migration of mutable Freakto state out of the source tree."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from typing import Iterable


@dataclass(frozen=True)
class MigrationItem:
    category: str
    source: str
    destination: str
    files: int
    bytes: int
    action: str


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _inventory(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    files = [item for item in path.rglob("*") if item.is_file()]
    return len(files), sum(item.stat().st_size for item in files)


def build_plan(root: Path, destination: Path, include_market_cache: bool = False) -> list[MigrationItem]:
    root = root.resolve()
    destination = destination.resolve()
    if destination == root or _inside(destination, root / "logs") or _inside(destination, root / "history"):
        raise ValueError("Runtime destination must not be a source runtime directory")
    sources = [
        ("runtime_logs", root / "logs", destination / "logs"),
        ("mutable_history", root / "history", destination / "history"),
        ("cloud_state", root / ".cloud-state", destination / "cloud-state"),
    ]
    if include_market_cache:
        sources.append(("generated_market_cache", root / "data" / "market_replay", destination / "market-cache"))
    plan = []
    for category, source, target in sources:
        files, size = _inventory(source)
        plan.append(
            MigrationItem(
                category=category,
                source=str(source),
                destination=str(target),
                files=files,
                bytes=size,
                action="SKIP_MISSING" if not source.exists() else "COPY",
            )
        )
    return plan


def apply_plan(plan: Iterable[MigrationItem], *, move: bool = False) -> list[MigrationItem]:
    completed = []
    for item in plan:
        source = Path(item.source)
        destination = Path(item.destination)
        if not source.exists():
            completed.append(item)
            continue
        if destination.exists():
            raise FileExistsError(f"Destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if move:
            shutil.move(str(source), str(destination))
            action = "MOVED"
        else:
            shutil.copytree(source, destination, copy_function=shutil.copy2)
            action = "COPIED"
        completed.append(MigrationItem(**{**asdict(item), "action": action}))
    return completed


def write_manifest(path: Path, root: Path, destination: Path, mode: str, items) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_root": str(root.resolve()),
        "runtime_root": str(destination.resolve()),
        "mode": mode,
        "items": [asdict(item) for item in items],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Migrate mutable Freakto runtime state")
    parser.add_argument("--root", default=".")
    parser.add_argument("--destination", default=".freakto-runtime")
    parser.add_argument("--manifest", default=".freakto-runtime/manifests/migration.json")
    parser.add_argument("--include-market-cache", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Copy state; default is dry-run")
    parser.add_argument("--move", action="store_true", help="Move instead of copy; requires --apply")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.move and not args.apply:
        raise SystemExit("--move requires --apply")
    root = Path(args.root)
    destination = Path(args.destination)
    plan = build_plan(root, destination, args.include_market_cache)
    result = apply_plan(plan, move=args.move) if args.apply else plan
    mode = "move" if args.move else "copy" if args.apply else "dry-run"
    write_manifest(Path(args.manifest), root, destination, mode, result)
    print(json.dumps({"mode": mode, "items": [asdict(item) for item in result]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
