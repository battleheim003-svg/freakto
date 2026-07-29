"""Deprecated compatibility wrapper for Research / Evidence Integrity."""

from freakto.ui.legacy_launcher import launch_control_center


def main() -> int:
    return launch_control_center("evidence_integrity_dashboard.py")


if __name__ == "__main__":
    raise SystemExit(main())
