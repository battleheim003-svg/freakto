from pathlib import Path

import pytest

from freakto.cli import main
from telegram_notifier import format_paper_daily_summary, format_paper_trade_closed, format_paper_trade_open


ROOT = Path(__file__).parents[1]


def test_canonical_commands_and_windows_launchers_exist():
    for name in ("start_paper_trading.bat", "run_paper_cycle_once.bat", "stop_paper_trading.bat", "show_paper_status.bat", "show_paper_dashboard.bat"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "freakto.cli" in text
        assert "LIVE_TRADING_ENABLED=true" not in text
    assert "paper auto" in (ROOT / "start_paper_trading.bat").read_text(encoding="utf-8")


def test_strategy_command_remains_fail_closed(monkeypatch, capsys):
    class Blocked:
        strategy_paper_ready = False
        blockers = ["FRESH_OOS_MISSING"]
    monkeypatch.setattr("freakto.cli._readiness", lambda: Blocked())
    assert main(["paper", "arm-strategy"]) == 2
    assert "BLOCKED_STRATEGY_PAPER" in capsys.readouterr().out


def test_normal_telegram_open_is_short_persian_and_not_debug():
    text = format_paper_trade_open({"symbol": "BTC/USDT", "side": "LONG", "entry": 100, "stop": 98, "target": 104, "cost_pct": .18}, debug="RSI=70")
    assert "معامله آزمایشی" in text and "سرمایه واقعی: صفر" in text
    assert "RSI" not in text and len(text) < 500


@pytest.mark.parametrize("net_r,icon", [(1.35, "✅"), (-1, "❌")])
def test_closed_telegram_win_and_loss(net_r, icon):
    text = format_paper_trade_closed({"symbol": "BTC/USDT", "net_r": net_r, "net_return_pct": net_r, "close_reason": "هدف", "duration": "4 ساعت"},
        {"wins": 2, "losses": 1, "win_rate_pct": 66.7, "profit_factor": 1.5, "expectancy_r": .3, "cumulative_r": 1, "max_drawdown_r": .5})
    assert icon in text and "آزمایشی" in text and "Profit Factor" in text


def test_debug_telegram_keeps_diagnostics_and_daily_summary_is_concise():
    assert "RSI=70" in format_paper_trade_open({}, debug="RSI=70", mode="DEBUG")
    daily = format_paper_daily_summary({"total_signals": 3, "closed_trades": 2, "open_trades": 1})
    assert "خلاصه معاملات آزمایشی" in daily and "سرمایه واقعی: صفر" in daily


def test_ci_and_cloud_state_are_isolated():
    ci = (ROOT / ".github/workflows/freakto-ci.yml").read_text(encoding="utf-8")
    cloud = (ROOT / ".github/workflows/freakto-paper-cloud.yml").read_text(encoding="utf-8")
    assert "pull_request:" in ci and "python -m pytest" in ci and "compileall" in ci
    assert "paper-state" in cloud and 'LIVE_TRADING_ENABLED: "false"' in cloud
