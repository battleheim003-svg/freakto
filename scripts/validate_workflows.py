"""Parse every GitHub workflow as YAML and reject malformed structures."""

from __future__ import annotations

from pathlib import Path

import yaml


def main() -> int:
    workflows = sorted(Path(".github/workflows").glob("*.yml"))
    if not workflows:
        raise SystemExit("No GitHub workflows found")
    for path in workflows:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or "jobs" not in payload:
            raise SystemExit(f"Workflow has no jobs mapping: {path}")
    print(f"Validated {len(workflows)} GitHub workflows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
