from pathlib import Path


def test_live_paper_dashboard_is_a_thin_deprecated_wrapper():
    source = Path("live_paper_web_dashboard.py").read_text(encoding="utf-8")
    assert "[DEPRECATED]" not in source  # warning is centralized
    assert "launch_control_center" in source
    assert "streamlit" not in source
    assert len(source.splitlines()) <= 12


def test_learning_dashboard_launcher_redirects_to_control_center():
    source = Path("run_learning_paper_dashboard.bat").read_text(encoding="utf-8").lower()
    assert "[deprecated]" in source
    assert "run_control_center.bat" in source
    assert "live_paper_web_dashboard.py" not in source
