from __future__ import annotations

import hashlib
import json
from pathlib import Path

from freakto.showcase_paper import controller
from freakto.showcase_paper import session_reader


def _write_session(path: Path, count: int) -> None:
    payload = {
        "schema_version": 1,
        "mode": "SHOWCASE_PAPER",
        "trades": [
            {
                "trade_id": f"trade-{index:04d}",
                "status": "CLOSED" if index % 2 else "OPEN",
                "opened_utc": f"2026-07-01T00:{index % 60:02d}:00+00:00",
                "padding": "x" * 128,
            }
            for index in range(count)
        ],
        "seen_decisions": [f"decision-{index:04d}" for index in range(count)],
        "errors": [],
        "settings": {"quality_mode": "WIN_RATE"},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _ids(view: session_reader.SessionView) -> list[str]:
    return [str(row["trade_id"]) for row in view.trades]


def test_small_session_preserves_metadata_and_newest_first_order(tmp_path):
    path = tmp_path / "session.json"
    _write_session(path, 3)

    view = session_reader.read_session_view(path, page_size=10)

    assert view.metadata["mode"] == "SHOWCASE_PAPER"
    assert view.total_trades == 3
    assert view.open_trades == 2
    assert view.closed_trades == 1
    assert _ids(view) == ["trade-0002", "trade-0001", "trade-0000"]
    assert view.warning is None


def test_more_than_500_trades_are_bounded(tmp_path):
    path = tmp_path / "session.json"
    _write_session(path, 525)

    view = session_reader.read_session_view(path, page_size=50, analytics_limit=200)

    assert view.total_trades == 525
    assert len(view.trades) == 50
    assert len(view.analysis_trades) == 200
    assert view.degraded is True
    assert "newest 200 of 525" in str(view.warning)


def test_large_input_is_streamed_without_path_read_text(tmp_path, monkeypatch):
    path = tmp_path / "session.json"
    _write_session(path, 501)
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("full read")),
    )

    view = session_reader.read_session_view(path, page_size=25)

    assert view.total_trades == 501
    assert len(view.trades) == 25


def test_memory_error_degrades_without_escaping(tmp_path, monkeypatch):
    path = tmp_path / "session.json"
    _write_session(path, 2)
    monkeypatch.setattr(
        session_reader,
        "_scan",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(MemoryError()),
    )

    view = session_reader.read_session_view(path)

    assert view.degraded is True
    assert view.trades == []
    assert "memory safety limit" in str(view.warning)


def test_truncated_json_degrades_safely(tmp_path):
    path = tmp_path / "session.json"
    path.write_text('{"trades": [{"trade_id": "one"}', encoding="utf-8")

    view = session_reader.read_session_view(path)

    assert view.degraded is True
    assert "incomplete" in str(view.warning)


def test_empty_file_degrades_safely(tmp_path):
    path = tmp_path / "session.json"
    path.write_text("", encoding="utf-8")

    view = session_reader.read_session_view(path)

    assert view.degraded is True
    assert "empty" in str(view.warning)


def test_missing_file_degrades_safely(tmp_path):
    view = session_reader.read_session_view(tmp_path / "missing.json")

    assert view.degraded is True
    assert "not available" in str(view.warning)


def test_first_middle_and_last_pages_are_deterministic(tmp_path):
    path = tmp_path / "session.json"
    _write_session(path, 12)

    first = session_reader.read_session_view(path, page=1, page_size=5)
    middle = session_reader.read_session_view(path, page=2, page_size=5)
    last = session_reader.read_session_view(path, page=3, page_size=5)

    assert _ids(first) == [f"trade-{index:04d}" for index in range(11, 6, -1)]
    assert _ids(middle) == [f"trade-{index:04d}" for index in range(6, 1, -1)]
    assert _ids(last) == ["trade-0001", "trade-0000"]


def test_page_out_of_range_clamps_to_last_page(tmp_path):
    path = tmp_path / "session.json"
    _write_session(path, 7)

    view = session_reader.read_session_view(path, page=99, page_size=3)

    assert view.page == 3
    assert _ids(view) == ["trade-0000"]


def test_reader_does_not_modify_source(tmp_path):
    path = tmp_path / "session.json"
    _write_session(path, 20)
    before = hashlib.sha256(path.read_bytes()).hexdigest()

    session_reader.read_session_view(path, page=2, page_size=4)

    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


def test_page_size_is_capped(tmp_path):
    path = tmp_path / "session.json"
    _write_session(path, 250)

    view = session_reader.read_session_view(path, page_size=10_000)

    assert view.page_size == session_reader.MAX_PAGE_SIZE
    assert len(view.trades) == session_reader.MAX_PAGE_SIZE


def test_control_center_keeps_only_page_number_in_session_state():
    source = (
        Path(__file__).resolve().parents[1] / "freakto" / "ui" / "control_center.py"
    ).read_text(encoding="utf-8")

    assert 'st.session_state.get("showcase_trade_page", 1)' in source
    assert 'st.session_state["showcase_trades"]' not in source
    assert "showcase_dashboard_data(page=requested_trade_page)" in source


def test_controller_preserves_status_and_list_contract_with_bounded_data(tmp_path):
    session_path = tmp_path / "logs" / "showcase_paper" / "session.json"
    session_path.parent.mkdir(parents=True)
    _write_session(session_path, 205)

    status, trades = controller.showcase_dashboard_data(
        tmp_path,
        page=2,
        page_size=25,
    )

    assert status["total_trades"] == 205
    assert status["open_trades"] == 103
    assert status["closed_trades"] == 102
    assert status["trade_page"] == 2
    assert len(trades) == 25
    assert len(status["performance"]) > 0
    assert status["session_read_degraded"] is True


def test_control_center_displays_reader_fallback_without_sensitive_details():
    source = (
        Path(__file__).resolve().parents[1] / "freakto" / "ui" / "control_center.py"
    ).read_text(encoding="utf-8")

    assert 'if showcase.get("session_read_warning"):' in source
    assert 'st.warning(str(showcase["session_read_warning"]))' in source
