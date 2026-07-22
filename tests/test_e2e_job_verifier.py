from __future__ import annotations

import pandas as pd

from engine import market_replay
from scripts.verify_e2e_job import EXPECTED_STEPS, verify_job


def passing_job():
    safety = '{"live_orders_enabled": false, "real_capital_enabled": false, "allocation_pct": 0.0}'
    return {
        "job_id": "quick-fixture",
        "status": "SUCCEEDED",
        "steps": [
            {
                "key": key,
                "exit_code": 2 if key == "go_live_check" else 0,
                "accepted": True,
                "stdout_tail": safety if key in {"paper_preflight", "arm_research", "paper_status"} else "",
            }
            for key in EXPECTED_STEPS
        ],
    }


def test_complete_safe_job_is_valid_e2e_evidence():
    passed, manifest = verify_job(passing_job())
    assert passed is True
    assert manifest["passed"] is True
    assert all(manifest["checks"].values())


def test_missing_step_fails_verification():
    job = passing_job()
    job["steps"].pop(3)
    passed, manifest = verify_job(job)
    assert passed is False
    assert manifest["checks"]["complete_ordered_pipeline"] is False


def test_live_safety_evidence_cannot_be_omitted():
    job = passing_job()
    for step in job["steps"]:
        step["stdout_tail"] = ""
    passed, manifest = verify_job(job)
    assert passed is False
    assert manifest["checks"]["live_orders_disabled"] is False
    assert manifest["checks"]["real_capital_disabled"] is False


def test_replay_status_disables_chunked_dtype_inference(monkeypatch, tmp_path):
    path = tmp_path / "replay.csv"
    path.write_text("symbol\n", encoding="utf-8")
    called = {}

    def fake_read_csv(file_path, **kwargs):
        called.update(kwargs)
        return pd.DataFrame()

    monkeypatch.setattr(market_replay.pd, "read_csv", fake_read_csv)
    market_replay.load_market_replay_status(path)
    assert called["low_memory"] is False
