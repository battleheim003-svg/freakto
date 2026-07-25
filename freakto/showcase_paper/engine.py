"""Stateful, isolated multi-trade Paper showcase engine."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from freakto.showcase_paper.card import render_trade_card


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
    symbols: tuple[str, ...] = ("BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "LINK/USDT")
    daily_trade_limit: int = 6
    maximum_open_positions: int = 4
    notional_usdt: float = 250.0
    leverage: float = 1.0
    stop_loss_pct: float = 0.6
    take_profit_pct: float = 0.9
    maximum_holding_minutes: int = 60
    fee_bps_per_side: float = 10.0
    slippage_bps: float = 5.0

    def validated(self) -> "ShowcaseSettings":
        if not self.symbols:
            raise ValueError("At least one showcase symbol is required")
        if not 1 <= self.daily_trade_limit <= 30:
            raise ValueError("daily_trade_limit must be between 1 and 30")
        if not 1 <= self.maximum_open_positions <= 10:
            raise ValueError("maximum_open_positions must be between 1 and 10")
        if not 10 <= self.notional_usdt <= 10_000:
            raise ValueError("notional_usdt must be between 10 and 10,000")
        if not 1 <= self.leverage <= 5:
            raise ValueError("showcase leverage must stay between 1x and 5x")
        if self.stop_loss_pct <= 0 or self.take_profit_pct <= 0 or self.maximum_holding_minutes < 1:
            raise ValueError("stop, target, and holding duration must be positive")
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
            "schema_version": 1,
            "mode": "SHOWCASE_PAPER",
            "official_evidence_eligible": False,
            "started_utc": self.now_fn().isoformat(),
            "updated_utc": self.now_fn().isoformat(),
            "trades": [],
            "seen_decisions": [],
            "errors": [],
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

    def _signal(self, symbol: str) -> dict[str, Any] | None:
        item = self.signal_source(symbol)
        side = str(getattr(item, "side", "NEUTRAL")).upper()
        if side not in {"LONG", "SHORT"}:
            return None
        timestamp = str(getattr(item, "decision_timestamp", "") or self.now_fn().isoformat())
        identity = f"{symbol}|{side}|{timestamp}"
        decision_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
        return {
            "decision_id": decision_id,
            "side": side,
            "signal_timestamp": timestamp,
            "score": int(getattr(item, "score", 0) or 0),
            "confidence": int(getattr(item, "confidence", 0) or 0),
            "recommendation": str(getattr(item, "recommendation", "UNRATED")),
            "regime": str(getattr(item, "regime", "UNKNOWN")),
        }

    def open_available(self) -> list[dict[str, Any]]:
        opened: list[dict[str, Any]] = []
        slots = min(
            self.settings.maximum_open_positions - len(self._open_symbols()),
            self.settings.daily_trade_limit - self._today_count(),
        )
        if slots <= 0:
            return opened
        seen = set(self.state.get("seen_decisions") or [])
        open_symbols = self._open_symbols()
        for symbol in self.settings.symbols:
            if slots <= 0:
                break
            if symbol in open_symbols:
                continue
            try:
                signal = self._signal(symbol)
                if not signal or signal["decision_id"] in seen:
                    continue
                snapshot = self.market_data.fetch_snapshot(symbol)
                side = signal["side"]
                base = float(snapshot.ask if side == "LONG" else snapshot.bid)
                slip = self.settings.slippage_bps / 10_000.0
                entry = base * (1 + slip if side == "LONG" else 1 - slip)
                stop_factor = self.settings.stop_loss_pct / 100.0
                target_factor = self.settings.take_profit_pct / 100.0
                stop = entry * (1 - stop_factor if side == "LONG" else 1 + stop_factor)
                target = entry * (1 + target_factor if side == "LONG" else 1 - target_factor)
                now = self.now_fn().isoformat()
                trade_id = "showcase-" + hashlib.sha256(f"{signal['decision_id']}|{now}".encode()).hexdigest()[:12]
                trade = {
                    "trade_id": trade_id,
                    "mode": "SHOWCASE_PAPER",
                    "official_evidence_eligible": False,
                    "status": "OPEN",
                    "symbol": symbol,
                    "side": side,
                    "leverage": self.settings.leverage,
                    "notional_usdt": self.settings.notional_usdt,
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
                    **signal,
                }
                self._update_pnl(trade, float(snapshot.bid if side == "LONG" else snapshot.ask))
                trade["open_card"] = self._card(trade, "open")
                trade["latest_card"] = trade["open_card"]
                self.state["trades"].append(trade)
                self.state["seen_decisions"].append(signal["decision_id"])
                opened.append(trade)
                seen.add(signal["decision_id"])
                open_symbols.add(symbol)
                slots -= 1
                self.save()
            except Exception as exc:
                self.state["errors"].append({"timestamp_utc": self.now_fn().isoformat(), "symbol": symbol, "error": f"{type(exc).__name__}: {exc}"})
                self.state["errors"] = self.state["errors"][-50:]
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
