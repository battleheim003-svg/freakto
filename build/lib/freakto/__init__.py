"""Canonical public package for Freakto."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("freakto")
except PackageNotFoundError:  # Source tree without an installed distribution.
    __version__ = "10.3.0"

__all__ = ["__version__"]
