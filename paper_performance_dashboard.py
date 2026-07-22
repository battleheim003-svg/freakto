"""Compatibility wrapper for :mod:`freakto.paper.performance_report`."""

from freakto.paper.performance_report import main

__all__ = ["main"]


if __name__ == "__main__":
    raise SystemExit(main())
