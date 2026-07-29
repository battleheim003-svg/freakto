"""Compatibility wrapper for :mod:`freakto.paper.trade_launch`."""

from freakto.paper.trade_launch import *  # noqa: F403
from freakto.paper.trade_launch import main, parser

__all__ = ["main", "parser"]


if __name__ == "__main__":
    raise SystemExit(main())
