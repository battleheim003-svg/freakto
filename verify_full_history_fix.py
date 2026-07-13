"""Local file-level verification for the Freakto full-history bootstrap fix."""
from __future__ import annotations

import re
from pathlib import Path


def extract_version(path: Path, pattern: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(pattern, text)
    return match.group(1) if match else "MISSING"


def main() -> int:
    root = Path(__file__).resolve().parent
    historical_path = root / "engine" / "historical_data_store.py"
    archive_path = root / "engine" / "multi_cycle_archive.py"
    cli_path = root / "multi_cycle_archive_analysis.py"
    test_path = root / "tests" / "test_historical_full_history_bootstrap.py"

    historical_version = extract_version(historical_path, r'VERSION\s*=\s*"([^"]+)"')
    archive_version = extract_version(archive_path, r'VERSION\s*=\s*"([^"]+)"')
    cli_text = cli_path.read_text(encoding="utf-8") if cli_path.exists() else ""
    required_options = (
        "--listing-probe-days",
        "--max-listing-probes",
        "--no-full-discovery",
    )
    missing = [option for option in required_options if option not in cli_text]

    print("Historical Data Store version:", historical_version)
    print("Multi-Cycle Archive version:", archive_version)
    print("CLI file:", cli_path)
    print("New regression test exists:", test_path.exists())
    print("Required CLI options present:", not missing)
    if missing:
        print("Missing CLI options:", missing)

    ok = (
        historical_version == "v10.0.2"
        and archive_version == "2.1.0"
        and test_path.exists()
        and not missing
    )
    print("Verification:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
