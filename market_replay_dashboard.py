"""Compatibility wrapper for the canonical packaged market replay entry."""

from freakto.research.adapters.market_replay import build_parser, main

__all__ = ["build_parser", "main"]


if __name__ == "__main__":
    main()
