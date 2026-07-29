"""Compatibility wrapper for :mod:`freakto.paper.cloud_runner`."""

from freakto.paper.cloud_runner import *  # noqa: F403
from freakto.paper.cloud_runner import main


if __name__ == "__main__":
    raise SystemExit(main())
