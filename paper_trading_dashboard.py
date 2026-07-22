"""Compatibility wrapper for :mod:`freakto.paper.dashboard`."""

from freakto.paper.dashboard import *  # noqa: F403
from freakto.paper.dashboard import main


if __name__ == "__main__":
    raise SystemExit(main())
