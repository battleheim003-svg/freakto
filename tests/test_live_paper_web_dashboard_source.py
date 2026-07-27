from pathlib import Path


def test_streamlit_commands_are_not_used_inside_conditional_expressions():
    source = Path("live_paper_web_dashboard.py").read_text(encoding="utf-8")
    assert " if status.running else st." not in source


def test_brand_asset_and_credit_are_present():
    source = Path("live_paper_web_dashboard.py").read_text(encoding="utf-8")
    assert Path("assets/freakto-logo.png").is_file()
    assert "POWERED BY ALAVI" in source
    assert "border-radius:50%" in source


def test_retro_theme_bilingual_toggle_and_trade_board_are_present():
    source = Path("live_paper_web_dashboard.py").read_text(encoding="utf-8")
    assert '"EN": {' in source and '"FA": {' in source
    assert "LIGHT PROTOCOL" in source
    assert "statusPulse" in source and "logoFlux" in source
    assert "LATEST EXECUTION BOARD" in source
    assert '_latest_trade_board(data.fills, t)' in source
    assert "--profit:#2ee59d" in source
    assert "--loss:#ff4778" in source


def test_learning_mode_has_dashboard_data_and_worker_controls():
    source = Path("live_paper_web_dashboard.py").read_text(encoding="utf-8")
    assert '["learning", "shadow", "paper"]' in source
    assert 'mode=mode' in source
    assert '"SPOT SYMBOLS"' in source
    assert 'FREAKTO_OPERATIONAL_ROOT' in source
    assert 'Immediate virtual fills' in source
    assert "OPEN VIRTUAL SPOT POSITIONS" in source


def test_learning_dashboard_launcher_forces_zero_capital_environment():
    source = Path("run_learning_paper_dashboard.bat").read_text(encoding="utf-8").lower()
    assert 'cd /d "%~dp0"' in source
    assert "set \"live_trading_enabled=false\"" in source
    assert "set \"real_capital_enabled=false\"" in source
    assert "-m streamlit run live_paper_web_dashboard.py" in source
