from pathlib import Path


def workflow_text() -> str:
    return Path('.github/workflows/freakto-paper-cloud.yml').read_text(encoding='utf-8')


def test_schedule_runs_six_times_per_day_after_four_hour_boundaries():
    text = workflow_text()
    assert 'cron: "9 0,4,8,12,16,20 * * *"' in text


def test_workflow_keeps_manual_dispatch_and_concurrency_lock():
    text = workflow_text()
    assert 'workflow_dispatch:' in text
    assert 'group: freakto-paper-cloud-cycle' in text
    assert 'cancel-in-progress: false' in text


def test_performance_outputs_are_uploaded_as_artifacts():
    text = workflow_text()
    assert 'logs/paper_performance/**' in text
    assert 'paper_performance_dashboard.py' in text
    assert 'engine/paper_performance_dashboard.py' in text


def test_workflow_is_paper_only():
    text = workflow_text()
    assert 'LIVE_TRADING_ENABLED: "false"' in text
    assert 'REAL_CAPITAL_ENABLED: "false"' in text
