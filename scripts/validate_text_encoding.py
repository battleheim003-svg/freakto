"""Validate canonical repository text as strict UTF-8 without mojibake."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {
    ".bat",
    ".cfg",
    ".cmd",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".yaml",
    ".yml",
}
SKIPPED_PARTS = {".git", ".venv", ".freakto-runtime", "history", "logs", "__pycache__"}
MOJIBAKE_MARKERS = (
    "\u00d8",
    "\u00d9",
    "\u00e2\u20ac",
    "\u00e2\u0153",
    "\u00e2\u009d",
    "\u00f0\u0178",
    "\ufffd",
)
UTF8_BOM = b"\xef\xbb\xbf"


def text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIPPED_PARTS for part in path.parts):
            continue
        yield path


def validate_file(path: Path) -> list[str]:
    data = path.read_bytes()
    failures = []
    if data.startswith(UTF8_BOM):
        failures.append("UTF-8 BOM is not allowed in canonical source text")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"invalid UTF-8: {exc}"]
    markers = sorted({marker for marker in MOJIBAKE_MARKERS if marker in text})
    if markers:
        failures.append("possible mojibake markers: " + ", ".join(markers))
    return failures


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository UTF-8 text policy")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    failures = []
    files = list(text_files(root))
    for path in files:
        failures.extend(f"{path.relative_to(root)}: {message}" for message in validate_file(path))
    if failures:
        print("\n".join(failures))
        return 1
    print(f"Validated {len(files)} strict UTF-8 text files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
