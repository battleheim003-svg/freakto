"""Deprecated compatibility wrapper for the unified Control Center."""

from freakto.ui.legacy_launcher import launch_control_center


def main() -> int:
    return launch_control_center("live_paper_web_dashboard.py")


if __name__ == "__main__":
    raise SystemExit(main())
