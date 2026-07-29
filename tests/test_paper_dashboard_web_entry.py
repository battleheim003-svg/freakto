import sys

import paper_trading_dashboard
from freakto.paper import dashboard


def test_web_path_redirects_to_official_control_center(monkeypatch):
    called = {}

    def fake_call(command, **kwargs):
        called["command"] = command
        called["kwargs"] = kwargs
        return 0

    monkeypatch.setattr(dashboard.subprocess, "call", fake_call)
    monkeypatch.setattr(sys, "argv", ["paper_trading_dashboard.py", "--web"])
    assert paper_trading_dashboard.main() == 0
    assert any(str(item).endswith("freakto_control_center.py") for item in called["command"])
    assert called["command"][-1] == "127.0.0.1"
    assert called["kwargs"]["env"]["LIVE_TRADING_ENABLED"] == "false"
