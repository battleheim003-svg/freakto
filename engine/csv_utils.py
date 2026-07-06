"""CSV compatibility helpers for Freakto log files.

These helpers are intentionally small and dependency-light. Several Freakto
logs are long-lived CSV files whose schema evolves across releases. Pandas is
strict about rows with more fields than the header, so a mixed-schema log can
break a forward-test cycle even though the underlying data is still usable.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List, Tuple


def read_csv_dicts_lenient(path: Path, *, encoding: str = "utf-8-sig") -> Tuple[List[str], List[dict]]:
    """Read a CSV with csv.DictReader and tolerate extra fields.

    Returns ``(fieldnames, rows)``. If a row has more values than the header,
    the extra values are kept under ``_extra`` by DictReader. Callers that only
    need stable early columns can still proceed safely.
    """
    if not path.exists():
        return [], []

    with path.open("r", newline="", encoding=encoding, errors="replace") as f:
        reader = csv.DictReader(f, restkey="_extra", restval="")
        fieldnames = list(reader.fieldnames or [])
        rows = []
        for row in reader:
            clean = {}
            for key, value in row.items():
                if key is None:
                    clean["_extra"] = value
                else:
                    clean[str(key).lstrip("\ufeff")] = value
            rows.append(clean)
        return [name.lstrip("\ufeff") for name in fieldnames], rows


def rewrite_csv_with_header(path: Path, fieldnames: Iterable[str], rows: Iterable[dict], *, encoding: str = "utf-8-sig") -> None:
    """Rewrite a CSV with a stable header and common-row preservation."""
    fieldnames = list(fieldnames)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
    tmp_path.replace(path)


def migrate_csv_header(path: Path, desired_fieldnames: Iterable[str]) -> bool:
    """Ensure ``path`` has exactly the desired header, preserving common fields.

    Returns True if a rewrite happened. This also repairs the common mixed-schema
    case where newer rows were appended under an older header.
    """
    desired = list(desired_fieldnames)
    if not path.exists():
        return False

    existing, rows = read_csv_dicts_lenient(path)
    if existing == desired:
        return False

    # Preserve any unknown old columns at the end so user-created data is not lost.
    merged = list(desired)
    for name in existing:
        if name and name not in merged:
            merged.append(name)

    rewrite_csv_with_header(path, merged, rows)
    return True
