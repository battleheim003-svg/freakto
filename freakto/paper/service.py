"""Paper application service isolated from CLI and UI presentation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from engine.paper_observation_v2 import arm_paper_mode, disarm_paper_mode, load_arm_state
from engine.paper_performance_dashboard import build_dashboard
from engine.paper_readiness_v2 import build_paper_launch_readiness, write_paper_readiness_outputs

from freakto.core import PAPER_SAFETY
from freakto.paper.go_live import STATUS_ELIGIBLE, evaluate_files

PAPER_COMMANDS = (
    "preflight",
    "arm-research",
    "cycle",
    "auto",
    "status",
    "dashboard",
    "disarm",
    "arm-strategy",
    "go-live-check",
)

EXIT_OK = 0
EXIT_BLOCKED = 2


def load_readiness(paper_dir: Path):
    readiness, walk = build_paper_launch_readiness()
    write_paper_readiness_outputs(readiness, walk, paper_dir)
    return readiness


class PaperService:
    def __init__(
        self,
        root: Path,
        run_script: Callable[[str, tuple[str, ...]], int],
        readiness_loader: Callable[[], Any] | None = None,
    ):
        self.root = root
        self.paper_dir = root / "logs" / "paper_launch_v2"
        self.run_script = run_script
        self.readiness_loader = readiness_loader

    def _readiness(self):
        if self.readiness_loader is not None:
            return self.readiness_loader()
        return load_readiness(self.paper_dir)

    def preflight(self) -> tuple[int, dict[str, Any]]:
        readiness = self._readiness()
        self.paper_dir.mkdir(parents=True, exist_ok=True)
        probe = self.paper_dir / ".write_probe"
        try:
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            writable = True
        except OSError:
            writable = False
        required = [
            self.root / "paper_research_orchestrator.py",
            self.root / "paper_trade_launch_dashboard.py",
            self.root / "cloud_state_sync.py",
            self.root / ".github/workflows/freakto-paper-cloud.yml",
        ]
        blockers: list[str] = []
        if not all(path.exists() for path in required):
            blockers.append("REQUIRED_FILES_MISSING")
        if not writable:
            blockers.append("PAPER_STATE_NOT_WRITABLE")
        if os.getenv("LIVE_TRADING_ENABLED", "false").lower() not in {"false", "0", ""}:
            blockers.append("LIVE_FLAG_UNSAFE")
        if os.getenv("REAL_CAPITAL_ENABLED", "false").lower() not in {"false", "0", ""}:
            blockers.append("REAL_CAPITAL_FLAG_UNSAFE")
        if not readiness.research_collection_ready:
            blockers.extend(readiness.blockers or ["RESEARCH_DATA_NOT_READY"])
        status = (
            "READY_FOR_RESEARCH_PAPER_COLLECTION" if not blockers else "BLOCKED_RESEARCH_PAPER"
        )
        return (
            EXIT_OK if not blockers else EXIT_BLOCKED,
            {
                "status": status,
                "strategy_status": (
                    "READY_FOR_STRATEGY_PAPER"
                    if readiness.strategy_paper_ready
                    else "BLOCKED_STRATEGY_PAPER"
                ),
                "blockers": blockers,
                "telegram_configured": bool(
                    os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")
                ),
                **PAPER_SAFETY.payload(),
            },
        )

    def execute(self, command: str) -> tuple[int, dict[str, Any] | None]:
        if command == "preflight":
            return self.preflight()
        if command == "arm-research":
            code, check = self.preflight()
            if code:
                return code, check
            (self.paper_dir / "operator_stop.flag").unlink(missing_ok=True)
            arm_paper_mode(self._readiness(), "RESEARCH", self.paper_dir)
            return EXIT_OK, {
                "status": "READY_FOR_RESEARCH_PAPER_COLLECTION",
                "armed": True,
                **PAPER_SAFETY.payload(),
            }
        if command == "arm-strategy":
            readiness = self._readiness()
            if not readiness.strategy_paper_ready:
                return EXIT_BLOCKED, {
                    "status": "BLOCKED_STRATEGY_PAPER",
                    "blockers": readiness.blockers,
                    **PAPER_SAFETY.payload(),
                }
            arm_paper_mode(readiness, "STRATEGY", self.paper_dir)
            return EXIT_OK, {"status": "READY_FOR_STRATEGY_PAPER", **PAPER_SAFETY.payload()}
        if command in {"cycle", "auto"}:
            argument = "--once" if command == "cycle" else "--loop"
            return self.run_script("paper_research_orchestrator.py", (argument,)), None
        if command == "dashboard":
            summary, _, _, _, outputs = build_dashboard()
            return EXIT_OK, {
                "status": summary.status,
                "summary": summary.to_dict(),
                "outputs": outputs,
                **PAPER_SAFETY.payload(),
            }
        if command == "disarm":
            self.paper_dir.mkdir(parents=True, exist_ok=True)
            (self.paper_dir / "operator_stop.flag").write_text("توقف اپراتور", encoding="utf-8")
            disarm_paper_mode(self.paper_dir)
            return EXIT_OK, {"status": "DISARMED", **PAPER_SAFETY.payload()}
        if command == "status":
            state = load_arm_state(self.paper_dir)
            return EXIT_OK, {
                "status": state.get("mode", "DISARMED"),
                "armed": bool(state.get("armed")),
                **PAPER_SAFETY.payload(),
            }
        if command == "go-live-check":
            result = evaluate_files(
                self.root / "config" / "paper_go_live_policy.json",
                self.paper_dir / "go_live_evidence.json",
            )
            return (EXIT_OK if result["status"] == STATUS_ELIGIBLE else EXIT_BLOCKED), result
        raise ValueError(f"Unsupported paper command: {command}")
