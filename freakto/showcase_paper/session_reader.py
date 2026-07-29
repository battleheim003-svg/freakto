"""Bounded, read-only access to the Showcase Paper session JSON."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from math import ceil
from pathlib import Path
from typing import Any, Callable, TextIO

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200
DEFAULT_ANALYTICS_LIMIT = 200
MAX_VALUE_CHARS = 2 * 1024 * 1024
CHUNK_SIZE = 64 * 1024


class SessionReadError(ValueError):
    """The session file could not be decoded safely."""


@dataclass(frozen=True)
class SessionView:
    metadata: dict[str, Any] = field(default_factory=dict)
    trades: list[dict[str, Any]] = field(default_factory=list)
    analysis_trades: list[dict[str, Any]] = field(default_factory=list)
    total_trades: int = 0
    open_trades: int = 0
    closed_trades: int = 0
    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE
    total_pages: int = 1
    warning: str | None = None
    degraded: bool = False


class _JsonReader:
    def __init__(self, stream: TextIO):
        self.stream = stream
        self.buffer = ""
        self.position = 0
        self.eof = False
        self.decoder = json.JSONDecoder()

    def _read_more(self) -> bool:
        if self.eof:
            return False
        chunk = self.stream.read(CHUNK_SIZE)
        if chunk:
            self.buffer += chunk
            return True
        self.eof = True
        return False

    def _available(self) -> bool:
        while self.position >= len(self.buffer):
            self.buffer = ""
            self.position = 0
            if not self._read_more():
                return False
        return True

    def _skip_whitespace(self) -> None:
        while self._available():
            if not self.buffer[self.position].isspace():
                return
            self.position += 1

    def peek(self) -> str | None:
        self._skip_whitespace()
        return self.buffer[self.position] if self._available() else None

    def expect(self, token: str) -> None:
        actual = self.peek()
        if actual != token:
            raise SessionReadError(f"Expected {token!r}, found {actual!r}.")
        self.position += 1

    def decode_value(self, *, max_chars: int = MAX_VALUE_CHARS) -> Any:
        self._skip_whitespace()
        if not self._available():
            raise SessionReadError("Unexpected end of JSON input.")

        # Discard already-consumed input before growing a possibly incomplete
        # token. This bounds the buffer to one JSON value plus one file chunk.
        self.buffer = self.buffer[self.position :]
        self.position = 0
        while True:
            try:
                value, end = self.decoder.raw_decode(self.buffer)
            except json.JSONDecodeError as exc:
                if self.eof:
                    raise SessionReadError("Session JSON is incomplete or malformed.") from exc
                if len(self.buffer) > max_chars:
                    raise SessionReadError("A session JSON value exceeds the safety limit.")
                self._read_more()
                continue
            self.buffer = self.buffer[end:]
            self.position = 0
            return value


def _parse_array(
    reader: _JsonReader,
    on_item: Callable[[int, Any], None] | None,
) -> int:
    reader.expect("[")
    count = 0
    if reader.peek() == "]":
        reader.expect("]")
        return count
    while True:
        item = reader.decode_value()
        if on_item is not None:
            on_item(count, item)
        count += 1
        delimiter = reader.peek()
        if delimiter == ",":
            reader.expect(",")
            continue
        if delimiter == "]":
            reader.expect("]")
            return count
        raise SessionReadError("Session array has an invalid delimiter.")


def _scan(
    path: Path,
    *,
    keep_trade: Callable[[int, dict[str, Any]], None] | None = None,
) -> tuple[dict[str, Any], int, dict[str, int]]:
    metadata: dict[str, Any] = {}
    trade_count = 0
    status_counts: dict[str, int] = {}
    with path.open("r", encoding="utf-8") as stream:
        reader = _JsonReader(stream)
        reader.expect("{")
        if reader.peek() == "}":
            reader.expect("}")
            return metadata, trade_count, status_counts
        while True:
            key = reader.decode_value()
            if not isinstance(key, str):
                raise SessionReadError("Session object key is not a string.")
            reader.expect(":")
            if key == "trades":
                def collect(index: int, item: Any) -> None:
                    if isinstance(item, dict):
                        status = str(item.get("status", "UNKNOWN"))
                        status_counts[status] = status_counts.get(status, 0) + 1
                        if keep_trade is not None:
                            keep_trade(index, item)

                trade_count = _parse_array(reader, collect)
            elif key == "seen_decisions":
                # This list can grow with the trade history, but the dashboard
                # does not consume it. Validate and discard it item by item.
                _parse_array(reader, None)
            else:
                metadata[key] = reader.decode_value()
            delimiter = reader.peek()
            if delimiter == ",":
                reader.expect(",")
                continue
            if delimiter == "}":
                reader.expect("}")
                if reader.peek() is not None:
                    raise SessionReadError("Unexpected data after the session object.")
                return metadata, trade_count, status_counts
            raise SessionReadError("Session object has an invalid delimiter.")


def _signature(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_mtime_ns, stat.st_size


def _warning_view(message: str, *, page: int, page_size: int) -> SessionView:
    return SessionView(
        page=max(1, int(page)),
        page_size=page_size,
        warning=message,
        degraded=True,
    )


def read_session_view(
    path: str | Path,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    analytics_limit: int = DEFAULT_ANALYTICS_LIMIT,
) -> SessionView:
    """Return one newest-first page plus a bounded recent analytics window.

    The file is scanned twice. The first pass obtains an exact record count and
    small top-level metadata. The second pass retains only the requested page
    and the newest bounded analytics window; the complete trade array is never
    materialized.
    """

    source = Path(path)
    safe_page_size = max(1, min(MAX_PAGE_SIZE, int(page_size)))
    safe_analytics_limit = max(0, min(MAX_PAGE_SIZE, int(analytics_limit)))
    requested_page = max(1, int(page))
    if not source.exists():
        return _warning_view(
            "Showcase session is not available yet.",
            page=requested_page,
            page_size=safe_page_size,
        )
    try:
        if source.stat().st_size == 0:
            return _warning_view(
                "Showcase session is empty.",
                page=requested_page,
                page_size=safe_page_size,
            )
        for attempt in range(2):
            before = _signature(source)
            metadata, total, status_counts = _scan(source)
            total_pages = max(1, ceil(total / safe_page_size))
            selected_page = min(requested_page, total_pages)
            newest_offset = (selected_page - 1) * safe_page_size
            newest_stop = min(total, newest_offset + safe_page_size)
            page_start = max(0, total - newest_stop)
            page_stop = max(0, total - newest_offset)
            analytics_start = max(0, total - safe_analytics_limit)
            page_rows: list[dict[str, Any]] = []
            analytics_rows: list[dict[str, Any]] = []

            def collect(index: int, trade: dict[str, Any]) -> None:
                if page_start <= index < page_stop:
                    page_rows.append(trade)
                if index >= analytics_start:
                    analytics_rows.append(trade)

            _, verified_total, _ = _scan(source, keep_trade=collect)
            after = _signature(source)
            if before == after and verified_total == total:
                page_rows.reverse()
                limited = total > safe_analytics_limit
                warning = None
                if limited:
                    warning = (
                        f"Showcase analytics use the newest {safe_analytics_limit} "
                        f"of {total} trades to keep dashboard memory bounded."
                    )
                return SessionView(
                    metadata=metadata,
                    trades=page_rows,
                    analysis_trades=analytics_rows,
                    total_trades=total,
                    open_trades=status_counts.get("OPEN", 0),
                    closed_trades=status_counts.get("CLOSED", 0),
                    page=selected_page,
                    page_size=safe_page_size,
                    total_pages=total_pages,
                    warning=warning,
                    degraded=limited,
                )
            if attempt == 0:
                continue
            raise SessionReadError("Session changed repeatedly while it was being read.")
    except MemoryError:
        return _warning_view(
            "Showcase session could not be loaded within the memory safety limit.",
            page=requested_page,
            page_size=safe_page_size,
        )
    except (OSError, SessionReadError):
        return _warning_view(
            "Showcase session is incomplete or temporarily unavailable.",
            page=requested_page,
            page_size=safe_page_size,
        )
