from datetime import datetime, timezone
import json

from freakto.ui.paper_demo import collect_paper_demo_snapshot


def test_waiting_worker_before_first_cycle_is_not_reported_as_no_data(tmp_path):
    output = tmp_path / "logs" / "paper_launch_v2"
    output.mkdir(parents=True)
    now = datetime(2026, 7, 28, 8, tzinfo=timezone.utc)
    (output / "heartbeat.json").write_text(
        json.dumps(
            {
                "pid": 42,
                "status": "WAITING_FOR_NEXT_CANDLE",
                "now_utc": now.isoformat(),
                "next_scheduled_utc": "2026-07-28T12:02:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    snapshot = collect_paper_demo_snapshot(tmp_path, now=now)
    assert snapshot["status"] == "NOT_STARTED"
    assert snapshot["worker_status"] == "WAITING_FOR_NEXT_CANDLE"
    assert snapshot["health"] == "WAITING_FOR_FIRST_SCHEDULED_CYCLE"
