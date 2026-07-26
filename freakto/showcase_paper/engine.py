"""Stateful, isolated multi-trade Paper showcase engine."""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from freakto.showcase_paper.card import render_trade_card
from freakto.showcase_paper.risk import admission_reason, risk_policy


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _read_json(path: Path, fallback: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback
    return payload if isinstance(payload, dict) else fallback


@dataclass(frozen=True)
class ShowcaseSettings:
    symbols: tuple[str, ...] = (
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "LINK/USDT",
        "DOGE/USDT", "AVAX/USDT", "DOT/USDT", "NEAR/USDT", "LTC/USDT", "BCH/USDT",
    )
    daily_trade_limit: int = 0
    maximum_open_positions: int = 4
    notional_usdt: float = 250.0
    leverage: float = 1.0
    stop_loss_pct: float = 0.6
    take_profit_pct: float = 0.9
    maximum_holding_minutes: int = 60
    fee_bps_per_side: float = 10.0
    slippage_bps: float = 5.0
    risk_level: int = 35
    analysis_depth: int = 100
    reentry_cooldown_minutes: int = 30
    market_mode: str = "LIVE_PUBLIC"

    def validated(self) -> "ShowcaseSettings":
        if not self.symbols:
            raise ValueError("At least one showcase symbol is required")
        if not 0 <= self.daily_trade_limit <= 100_000:
            raise ValueError("daily_trade_limit must be zero (unlimited) or a positive safety cap")
        if not 1 <= self.maximum_open_positions <= 30:
            raise ValueError("maximum_open_positions must be between 1 and 30")
        if not 10 <= self.notional_usdt <= 10_000:
            raise ValueError("notional_usdt must be between 10 and 10,000")
        if not 1 <= self.leverage <= 5:
            raise ValueError("showcase leverage must stay between 1x and 5x")
        if self.stop_loss_pct <= 0 or self.take_profit_pct <= 0 or self.maximum_holding_minutes < 1:
            raise ValueError("stop, target, and holding duration must be positive")
        if not 0 <= int(self.risk_level) <= 100:
            raise ValueError("risk_level must stay between 0 and 100")
        if not 0 <= int(self.analysis_depth) <= 100:
            raise ValueError("analysis_depth must stay between 0 and 100")
        if not 0 <= int(self.reentry_cooldown_minutes) <= 1440:
            raise ValueError("reentry_cooldown_minutes must stay between 0 and 1,440")
        if self.market_mode not in {"LIVE_PUBLIC", "ACCELERATED_REPLAY"}:
            raise ValueError("market_mode must be LIVE_PUBLIC or ACCELERATED_REPLAY")
        return self


class ShowcaseEngine:
    """Opens simulated positions from current directional analysis.

    State and cards live only under the supplied showcase directory. Nothing is
    written to official Paper ledgers or Go-live evidence.
    """

    def __init__(
        self,
        root: str | Path,
        settings: ShowcaseSettings,
        market_data: Any,
        signal_source: Callable[[str], Any],
        *,
        now_fn: Callable[[], datetime] = utc_now,
        logo_path: str | Path | None = None,
    ):
        self.root = Path(root)
        self.settings = settings.validated()
        self.market_data = market_data
        self.signal_source = signal_source
        self.now_fn = now_fn
        self.logo_path = Path(logo_path) if logo_path else None
        self.state_path = self.root / "session.json"
        self.cards_dir = self.root / "cards"
        self.state = _read_json(self.state_path, self._initial_state())

    def _initial_state(self) -> dict[str, Any]:
        return {
            "schema_version": 2,
            "mode": "SHOWCASE_PAPER",
            "market_mode": self.settings.market_mode,
            "official_evidence_eligible": False,
            "started_utc": self.now_fn().isoformat(),
            "updated_utc": self.now_fn().isoformat(),
            "trades": [],
            "seen_decisions": [],
            "errors": [],
            "last_scan": {},
        }

    def save(self) -> None:
        self.state["updated_utc"] = self.now_fn().isoformat()
        _atomic_json(self.state_path, self.state)

    @property
    def trades(self) -> list[dict[str, Any]]:
        return list(self.state.get("trades") or [])

    def _today_count(self) -> int:
        today = self.now_fn().date().isoformat()
        return sum(1 for trade in self.trades if str(trade.get("opened_utc", "")).startswith(today))

    def _open_symbols(self) -> set[str]:
        return {str(trade["symbol"]) for trade in self.trades if trade.get("status") == "OPEN"}

    def _card(self, trade: dict[str, Any], suffix: str) -> str:
        path = self.cards_dir / f'{trade["trade_id"]}_{suffix}.png'
        render_trade_card(trade, path, logo_path=self.logo_path)
        return str(path)

    def _signal(self, symbol: str) -> tuple[dict[str, Any] | None, str | None]:
        item = self.signal_source(symbol)
        side = str(getattr(item, "side", "NEUTRAL")).upper()
        timestamp = str(getattr(item, "decision_timestamp", "") or self.now_fn().isoformat())
        identity = f"{symbol}|{side}|{timestamp}"
        signal = {
            "source_signal_id": hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20],
            "side": side,
            "signal_timestamp": timestamp,
            "score": int(getattr(item, "score", 0) or 0),
            "confidence": int(getattr(item, "confidence", 0) or 0),
            "recommendation": str(getattr(item, "recommendation", "UNRATED")),
            "regime": str(getattr(item, "regime", "UNKNOWN")),
            "analysis_depth": str(getattr(item, "analysis_depth", risk_policy(self.settings.risk_level).analysis_depth)),
            "analysis_depth_value": int(getattr(item, "analysis_depth_value", self.settings.analysis_depth)),
            "indicators_used": list(getattr(item, "indicators_used", []) or []),
            "indicator_votes": dict(getattr(item, "indicator_votes", {}) or {}),
            "technical_long_votes": int(getattr(item, "technical_long_votes", 0) or 0),
            "technical_short_votes": int(getattr(item, "technical_short_votes", 0) or 0),
            "technical_neutral_votes": int(getattr(item, "technical_neutral_votes", 0) or 0),
            "technical_confluence_pct": getattr(item, "technical_confluence_pct", None),
            "technical_v2": dict(getattr(item, "technical_v2", {}) or {}),
            "family_scores": list(getattr(item, "family_scores", []) or []),
            "timeframe_scores": dict(getattr(item, "timeframe_scores", {}) or {}),
            "timeframe_agreement": getattr(item, "timeframe_agreement", None),
            "trade_geometry": dict(getattr(item, "trade_geometry", {}) or {}),
            "risk_assessment": dict(getattr(item, "risk_assessment", {}) or {}),
            "calibration": dict(getattr(item, "calibration", {}) or {}),
            "decision_reasons": list(getattr(item, "decision_reasons", []) or []),
            "decision_warnings": list(getattr(item, "decision_warnings", []) or []),
            "engine_version": str(getattr(item, "engine_version", "legacy-showcase")),
        }
        reason = admission_reason(signal, risk_policy(self.settings.risk_level))
        return (signal if reason is None else None), reason

    def _reentry_blocked(self, symbol: str) -> bool:
        cooldown = int(self.settings.reentry_cooldown_minutes)
        if cooldown <= 0:
            return False
        cutoff = self.now_fn().timestamp() - cooldown * 60
        for trade in reversed(self.trades):
            if trade.get("symbol") != symbol:
                continue
            timestamp = trade.get("closed_utc") or trade.get("opened_utc")
            try:
                return datetime.fromisoformat(str(timestamp)).timestamp() > cutoff
            except (TypeError, ValueError):
                return True
        return False

    def open_available(self) -> list[dict[str, Any]]:
        opened: list[dict[str, Any]] = []
        policy = risk_policy(self.settings.risk_level)
        scan = {
            "scanned_utc": self.now_fn().isoformat(),
            "risk_policy": policy.to_dict(),
            "market_mode": self.settings.market_mode,
            "analysis_depth": self.settings.analysis_depth,
            "evaluated": 0,
            "accepted": 0,
            "opened": 0,
            "rejected": {},
            "errors": [],
        }
        position_slots = self.settings.maximum_open_positions - len(self._open_symbols())
        daily_slots = (
            self.settings.daily_trade_limit - self._today_count()
            if self.settings.daily_trade_limit > 0
            else position_slots
        )
        slots = min(position_slots, daily_slots)
        if slots <= 0:
            scan["rejected"] = {"SESSION_CAPACITY_REACHED": len(self.settings.symbols)}
            self.state["last_scan"] = scan
            self.save()
            return opened
        open_symbols = self._open_symbols()
        for symbol in self.settings.symbols:
            if slots <= 0:
                break
            if symbol in open_symbols:
                scan["rejected"]["ALREADY_OPEN"] = int(scan["rejected"].get("ALREADY_OPEN", 0)) + 1
                continue
            if self._reentry_blocked(symbol):
                scan["rejected"]["REENTRY_COOLDOWN"] = int(scan["rejected"].get("REENTRY_COOLDOWN", 0)) + 1
                continue
            try:
                scan["evaluated"] += 1
                signal, rejected = self._signal(symbol)
                if not signal:
                    reason = str(rejected or "SIGNAL_REJECTED")
                    scan["rejected"][reason] = int(scan["rejected"].get(reason, 0)) + 1
                    continue
                scan["accepted"] += 1
                snapshot = self.market_data.fetch_snapshot(symbol)
                side = signal["side"]
                base = float(snapshot.ask if side == "LONG" else snapshot.bid)
                slip = self.settings.slippage_bps / 10_000.0
                entry = base * (1 + slip if side == "LONG" else 1 - slip)
                geometry = dict(signal.get("trade_geometry") or {})
                if geometry.get("stop") and geometry.get("target"):
                    source_entry = float(geometry.get("entry") or entry)
                    stop_distance = abs(source_entry - float(geometry["stop"]))
                    target_distance = abs(float(geometry["target"]) - source_entry)
                    stop = entry - stop_distance if side == "LONG" else entry + stop_distance
                    target = entry + target_distance if side == "LONG" else entry - target_distance
                else:
                    stop_factor = self.settings.stop_loss_pct / 100.0
                    target_factor = self.settings.take_profit_pct / 100.0
                    stop = entry * (1 - stop_factor if side == "LONG" else 1 + stop_factor)
                    target = entry * (1 + target_factor if side == "LONG" else 1 - target_factor)
                now = self.now_fn().isoformat()
                decision_id = hashlib.sha256(f"{signal['source_signal_id']}|{now}".encode()).hexdigest()[:20]
                trade_id = "showcase-" + hashlib.sha256(f"{decision_id}|{now}".encode()).hexdigest()[:12]
                trade = {
                    "trade_id": trade_id,
                    "mode": "SHOWCASE_PAPER",
                    "official_evidence_eligible": False,
                    "market_mode": self.settings.market_mode,
                    "risk_level": policy.level,
                    "risk_profile": policy.key,
                    "status": "OPEN",
                    "symbol": symbol,
                    "side": side,
                    "leverage": self.settings.leverage,
                    "notional_usdt": round(
                        self.settings.notional_usdt
                        * float((signal.get("risk_assessment") or {}).get("position_scale", 1.0))
                        / math.sqrt(
                            1 + sum(
                                1 for existing in self.trades
                                if existing.get("status") == "OPEN" and existing.get("side") == side
                            )
                        ),
                        2,
                    ),
                    "entry_price": entry,
                    "current_price": float(snapshot.last),
                    "exit_price": None,
                    "stop_price": stop,
                    "target_price": target,
                    "opened_utc": now,
                    "updated_utc": now,
                    "closed_utc": None,
                    "close_reason": None,
                    "pnl_pct": 0.0,
                    "pnl_usdt": 0.0,
                    "decision_id": decision_id,
                    **signal,
                }
                self._update_pnl(trade, float(snapshot.bid if side == "LONG" else snapshot.ask))
                trade["open_card"] = self._card(trade, "open")
                trade["latest_card"] = trade["open_card"]
                self.state["trades"].append(trade)
                self.state["seen_decisions"].append(signal["source_signal_id"])
                opened.append(trade)
                open_symbols.add(symbol)
                slots -= 1
                self.save()
            except Exception as exc:
                error = {"timestamp_utc": self.now_fn().isoformat(), "symbol": symbol, "error": f"{type(exc).__name__}: {exc}"}
                scan["errors"].append(error)
                self.state["errors"].append(error)
                self.state["errors"] = self.state["errors"][-50:]
                self.save()
        scan["opened"] = len(opened)
        self.state["last_scan"] = scan
        self.state["risk_policy"] = policy.to_dict()
        self.save()
        return opened

    def _update_pnl(self, trade: dict[str, Any], mark: float) -> None:
        entry = float(trade["entry_price"])
        direction = 1.0 if trade["side"] == "LONG" else -1.0
        gross_pct = direction * (mark - entry) / entry * 100.0 * float(trade["leverage"])
        estimated_fees_pct = 2.0 * self.settings.fee_bps_per_side / 100.0
        pnl_pct = gross_pct - estimated_fees_pct
        trade.update(
            current_price=mark,
            pnl_pct=round(pnl_pct, 6),
            pnl_usdt=round(float(trade["notional_usdt"]) * pnl_pct / 100.0, 6),
            updated_utc=self.now_fn().isoformat(),
        )

    def mark_and_close(self, *, close_all: bool = False) -> list[dict[str, Any]]:
        closed: list[dict[str, Any]] = []
        now = self.now_fn()
        for trade in self.state.get("trades") or []:
            if trade.get("status") != "OPEN":
                continue
            try:
                snapshot = self.market_data.fetch_snapshot(str(trade["symbol"]))
                mark = float(snapshot.bid if trade["side"] == "LONG" else snapshot.ask)
                self._update_pnl(trade, mark)
                opened = datetime.fromisoformat(str(trade["opened_utc"]))
                held_minutes = max(0.0, (now - opened).total_seconds() / 60.0)
                hit_stop = mark <= float(trade["stop_price"]) if trade["side"] == "LONG" else mark >= float(trade["stop_price"])
                hit_target = mark >= float(trade["target_price"]) if trade["side"] == "LONG" else mark <= float(trade["target_price"])
                reason = "SESSION_STOP" if close_all else "STOP" if hit_stop else "TARGET" if hit_target else "TIME_EXIT" if held_minutes >= self.settings.maximum_holding_minutes else None
                if reason:
                    trade.update(status="CLOSED", exit_price=mark, closed_utc=now.isoformat(), close_reason=reason)
                    trade["close_card"] = self._card(trade, "closed")
                    trade["latest_card"] = trade["close_card"]
                    closed.append(trade)
                else:
                    trade["latest_card"] = self._card(trade, "open")
            except Exception as exc:
                self.state["errors"].append({"timestamp_utc": now.isoformat(), "symbol": trade.get("symbol"), "error": f"{type(exc).__name__}: {exc}"})
                self.state["errors"] = self.state["errors"][-50:]
        self.save()
        return closed
