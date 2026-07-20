import sys

import paper_trading_dashboard


def test_web_path_does_not_import_telegram_or_paper_engine(monkeypatch):
    called = {}
    modules_before = set(sys.modules)

    def fake_call(command):
        called["command"] = command
        assert set(sys.modules) == modules_before
        return 0

    monkeypatch.setattr(paper_trading_dashboard.subprocess, "call", fake_call)
    monkeypatch.setattr(sys, "argv", ["paper_trading_dashboard.py", "--web"])
    assert paper_trading_dashboard.main() == 0
    assert called["command"][1:4] == ["-m", "streamlit", "run"]
