"""Compatibility wrapper for :mod:`freakto.paper.orchestrator`."""

from freakto.paper.orchestrator import *  # noqa: F403
from freakto.paper.orchestrator import main


if __name__ == "__main__":
    raise SystemExit(main())
