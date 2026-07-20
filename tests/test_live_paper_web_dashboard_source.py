from pathlib import Path


def test_streamlit_commands_are_not_used_inside_conditional_expressions():
    source = Path("live_paper_web_dashboard.py").read_text(encoding="utf-8")
    assert " if status.running else st." not in source


def test_brand_asset_and_credit_are_present():
    source = Path("live_paper_web_dashboard.py").read_text(encoding="utf-8")
    assert Path("assets/freakto-logo.png").is_file()
    assert "POWERED BY ALAVI" in source
    assert "border-radius: 50%" in source
