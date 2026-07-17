from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from engine.paper_observation_v2 import arm_paper_mode, disarm_paper_mode, load_arm_state
from engine.paper_readiness_v2 import build_paper_launch_readiness, write_paper_readiness_outputs
from engine.paper_performance_dashboard import build_dashboard

ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "logs" / "paper_launch_v2"


def _safety() -> dict:
    return {"live_orders_enabled": False, "real_capital_enabled": False, "allocation_pct": 0.0}


def _readiness():
    readiness, walk = build_paper_launch_readiness()
    write_paper_readiness_outputs(readiness, walk, PAPER_DIR)
    return readiness


def preflight() -> tuple[int, dict]:
    readiness = _readiness()
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    probe = PAPER_DIR / ".write_probe"
    try:
        probe.write_text("ok", encoding="utf-8"); probe.unlink()
        writable = True
    except OSError:
        writable = False
    required = [ROOT / "paper_research_orchestrator.py", ROOT / "paper_trade_launch_dashboard.py",
                ROOT / "cloud_state_sync.py", ROOT / ".github/workflows/freakto-paper-cloud.yml"]
    blockers = []
    if not all(path.exists() for path in required): blockers.append("REQUIRED_FILES_MISSING")
    if not writable: blockers.append("PAPER_STATE_NOT_WRITABLE")
    if os.getenv("LIVE_TRADING_ENABLED", "false").lower() not in {"false", "0", ""}: blockers.append("LIVE_FLAG_UNSAFE")
    if os.getenv("REAL_CAPITAL_ENABLED", "false").lower() not in {"false", "0", ""}: blockers.append("REAL_CAPITAL_FLAG_UNSAFE")
    if not readiness.research_collection_ready: blockers.extend(readiness.blockers or ["RESEARCH_DATA_NOT_READY"])
    status = "READY_FOR_RESEARCH_PAPER_COLLECTION" if not blockers else "BLOCKED_RESEARCH_PAPER"
    return (0 if not blockers else 2), {"status": status, "strategy_status": "READY_FOR_STRATEGY_PAPER" if readiness.strategy_paper_ready else "BLOCKED_STRATEGY_PAPER",
        "blockers": blockers, "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")), **_safety()}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="رابط ایمن معاملات آزمایشی Freakto")
    sub = parser.add_subparsers(dest="area", required=True); paper = sub.add_parser("paper")
    paper.add_argument("command", choices=("preflight", "arm-research", "cycle", "auto", "status", "dashboard", "disarm", "arm-strategy"))
    args = parser.parse_args(argv)
    if args.command == "preflight": code, payload = preflight()
    elif args.command == "arm-research":
        code, check = preflight()
        if code: payload = check
        else:
            (PAPER_DIR / "operator_stop.flag").unlink(missing_ok=True)
            arm_paper_mode(_readiness(), "RESEARCH", PAPER_DIR); payload = {"status": "READY_FOR_RESEARCH_PAPER_COLLECTION", "armed": True, **_safety()}
    elif args.command == "arm-strategy":
        readiness = _readiness()
        if not readiness.strategy_paper_ready: code, payload = 2, {"status": "BLOCKED_STRATEGY_PAPER", "blockers": readiness.blockers, **_safety()}
        else: arm_paper_mode(readiness, "STRATEGY", PAPER_DIR); code, payload = 0, {"status": "READY_FOR_STRATEGY_PAPER", **_safety()}
    elif args.command in {"cycle", "auto"}:
        command = [sys.executable, "-X", "utf8", str(ROOT / "paper_research_orchestrator.py"), "--once" if args.command == "cycle" else "--loop"]
        return subprocess.call(command, cwd=ROOT, env={**os.environ, "LIVE_TRADING_ENABLED": "false", "REAL_CAPITAL_ENABLED": "false"})
    elif args.command == "dashboard":
        summary, _, _, _, outputs = build_dashboard(); code, payload = 0, {"status": summary.status, "summary": summary.to_dict(), "outputs": outputs, **_safety()}
    elif args.command == "disarm":
        PAPER_DIR.mkdir(parents=True, exist_ok=True); (PAPER_DIR / "operator_stop.flag").write_text("توقف اپراتور", encoding="utf-8")
        disarm_paper_mode(PAPER_DIR); code, payload = 0, {"status": "DISARMED", **_safety()}
    else:
        state = load_arm_state(PAPER_DIR); code, payload = 0, {"status": state.get("mode", "DISARMED"), "armed": bool(state.get("armed")), **_safety()}
    print(json.dumps(payload, ensure_ascii=False, indent=2)); return code


if __name__ == "__main__": raise SystemExit(main())
