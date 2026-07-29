from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from freakto.ui.unified_state import airdrop_view, official_paper_view


ROOT = Path(__file__).parents[1]


def test_only_official_root_entry_point_is_used_by_ui_launchers():
    launchers = [
        "run_control_center.bat",
        "run_learning_paper_dashboard.bat",
        "show_paper_dashboard.bat",
        "freakto/demo_launcher.py",
        "freakto/ui/legacy_launcher.py",
        "freakto/paper/dashboard.py",
    ]
    combined = "\n".join((ROOT / path).read_text(encoding="utf-8") for path in launchers)
    assert "streamlit run live_paper_web_dashboard.py" not in combined
    assert "streamlit run evidence_integrity_dashboard.py" not in combined
    assert "freakto_control_center.py" in combined


def test_official_view_never_reads_showcase_counts(tmp_path):
    (tmp_path / "logs" / "showcase_paper").mkdir(parents=True)
    (tmp_path / "logs" / "showcase_paper" / "session.json").write_text(
        json.dumps({"trades": [{"status": "CLOSED"}] * 99}), encoding="utf-8"
    )
    view = official_paper_view(tmp_path)
    assert view["mode"] == "official"
    assert view["evidence_eligible"] is True
    assert len(view["closed_trades"]) == 0
    assert "showcase" not in view["source"].lower()


def test_airdrop_adapter_does_not_touch_paper_state(tmp_path):
    history = tmp_path / "history"
    history.mkdir()
    database = history / "airdrop_outcomes.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE outcomes (id INTEGER PRIMARY KEY)")
        connection.execute("INSERT INTO outcomes DEFAULT VALUES")
    before = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    view = airdrop_view(tmp_path)
    after = sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*"))
    assert view["table_counts"]["outcomes"] == 1
    assert view["paper_state_touched"] is False
    assert before == after


def test_missing_and_corrupt_official_state_are_fail_soft(tmp_path):
    (tmp_path / "logs" / "paper_performance").mkdir(parents=True)
    (tmp_path / "logs" / "paper_performance" / "paper_performance_summary.json").write_text(
        "{broken", encoding="utf-8"
    )
    view = official_paper_view(tmp_path)
    assert view["campaign"]["status"] == "NOT_STARTED"
    assert view["warnings"]
