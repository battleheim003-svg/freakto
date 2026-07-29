"""Foundational, public-data-only live demo infrastructure.

This module deliberately cannot place exchange orders.  It contains no API-key
handling and models a long-only spot account backed by an injected market-data
source.
"""
from __future__ import annotations

import csv
import json
import math
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence


DEFAULT_PUBLIC_EXCHANGES = ("kucoin", "kraken", "bybit", "okx")
ORDER_BOOK_LIMITS = {"kucoin": 20}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _positive_number(value: float, name: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise ValueError(f"{name} must be a finite number greater than zero")
    return parsed


@dataclass(frozen=True)
class MarketSnapshot:
    timestamp_utc: str
    symbol: str
    last: float
    bid: float
    ask: float
    bid_size: float | None = None
    ask_size: float | None = None
    provider: str = "unknown"


class MarketDataSource(Protocol):
    def fetch_snapshot(self, symbol: str) -> MarketSnapshot: ...


class CcxtPublicMarketData:
    """Public CCXT ticker/order-book adapter with provider fallback."""

    def __init__(
        self,
        exchange_ids: str | Sequence[str] = DEFAULT_PUBLIC_EXCHANGES,
        retries: int = 1,
        timeout_ms: int = 10_000,
    ):
        import ccxt

        requested = [exchange_ids] if isinstance(exchange_ids, str) else list(exchange_ids)
        if not requested:
            raise ValueError("at least one exchange is required")
        self.exchanges = []
        for exchange_id in dict.fromkeys(str(item).lower().strip() for item in requested):
            exchange_class = getattr(ccxt, exchange_id, None)
            if exchange_class is None:
                raise ValueError(f"Unsupported CCXT exchange: {exchange_id}")
            options = {"enableRateLimit": True, "timeout": int(timeout_ms)}
            if exchange_id == "bybit":
                options["options"] = {"defaultType": "spot"}
            self.exchanges.append((exchange_id, exchange_class(options)))
        self.retries = max(0, int(retries))

    def fetch_snapshot(self, symbol: str) -> MarketSnapshot:
        errors: list[str] = []
        for exchange_id, exchange in self.exchanges:
            for attempt in range(self.retries + 1):
                try:
                    ticker = exchange.fetch_ticker(symbol)
                    book = exchange.fetch_order_book(symbol, limit=ORDER_BOOK_LIMITS.get(exchange_id, 5))
                    bids = book.get("bids") or []
                    asks = book.get("asks") or []
                    last = float(ticker.get("last") or ticker.get("close"))
                    bid = float(bids[0][0] if bids else ticker.get("bid") or last)
                    ask = float(asks[0][0] if asks else ticker.get("ask") or last)
                    return MarketSnapshot(
                        timestamp_utc=utc_now(),
                        symbol=symbol,
                        last=_positive_number(last, "last price"),
                        bid=_positive_number(bid, "bid price"),
                        ask=_positive_number(ask, "ask price"),
                        bid_size=float(bids[0][1]) if bids else None,
                        ask_size=float(asks[0][1]) if asks else None,
                        provider=exchange_id,
                    )
                except Exception as exc:
                    detail = " ".join(str(exc).split())
                    if "403 Forbidden" in detail:
                        detail = detail.split("403 Forbidden", 1)[0] + "403 Forbidden (provider blocked this IP/region)"
                    elif len(detail) > 320:
                        detail = detail[:317] + "..."
                    errors.append(f"{exchange_id}[{attempt + 1}]: {type(exc).__name__}: {detail}")
                    if attempt < self.retries:
                        time.sleep(min(4.0, 2.0**attempt))
        raise RuntimeError(f"market data unavailable for {symbol}; " + " | ".join(errors))


@dataclass
class Position:
    amount: float
    average_entry: float


@dataclass(frozen=True)
class SimulatedFill:
    trade_id: str
    timestamp_utc: str
    symbol: str
    side: str
    amount: float
    market_price: float
    execution_price: float
    notional_usdt: float
    fee_usdt: float
    cash_balance_usdt: float
    position_amount: float
    equity_usdt: float


class TradeLogger:
    FIELDS = tuple(SimulatedFill.__dataclass_fields__)

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, fill: SimulatedFill) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not self.path.exists() or self.path.stat().st_size == 0
        with self.path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.FIELDS)
            if needs_header:
                writer.writeheader()
            writer.writerow(asdict(fill))


class MockBroker:
    """Long-only spot simulator; amounts are base-asset quantities."""

    def __init__(
        self,
        market_data: MarketDataSource,
        *,
        initial_balance: float = 10_000.0,
        fee_bps: float = 10.0,
        slippage_bps: float = 5.0,
        state_path: str | Path = "logs/live_demo/account_state.json",
        trade_log_path: str | Path = "logs/live_demo/trades.csv",
    ):
        self.market_data = market_data
        self.initial_balance = _positive_number(initial_balance, "initial_balance")
        self.fee_bps = max(0.0, float(fee_bps))
        self.slippage_bps = max(0.0, float(slippage_bps))
        self.state_path = Path(state_path)
        self.logger = TradeLogger(trade_log_path)
        self.cash_balance = self.initial_balance
        self.positions: dict[str, Position] = {}
        self._load_state()

    def _load_state(self) -> None:
        if not self.state_path.exists():
            return
        payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.cash_balance = float(payload["cash_balance_usdt"])
        self.positions = {
            symbol: Position(float(item["amount"]), float(item["average_entry"]))
            for symbol, item in payload.get("positions", {}).items()
        }

    def _save_state(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "updated_at_utc": utc_now(),
            "initial_balance_usdt": self.initial_balance,
            "cash_balance_usdt": self.cash_balance,
            "positions": {symbol: asdict(position) for symbol, position in self.positions.items()},
            "paper_only": True,
        }
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.state_path)

    def equity(self, marks: Mapping[str, float] | None = None) -> float:
        marks = dict(marks or {})
        total = self.cash_balance
        for symbol, position in self.positions.items():
            price = marks.get(symbol)
            if price is None:
                price = self.market_data.fetch_snapshot(symbol).last
            total += position.amount * float(price)
        return total

    def buy_market(self, symbol: str, amount: float, snapshot: MarketSnapshot | None = None) -> SimulatedFill:
        amount = _positive_number(amount, "amount")
        snapshot = snapshot or self.market_data.fetch_snapshot(symbol)
        execution_price = snapshot.ask * (1.0 + self.slippage_bps / 10_000.0)
        notional = amount * execution_price
        fee = notional * self.fee_bps / 10_000.0
        if notional + fee > self.cash_balance + 1e-9:
            raise ValueError("insufficient virtual USDT balance")
        previous = self.positions.get(symbol, Position(0.0, 0.0))
        new_amount = previous.amount + amount
        average_entry = (previous.amount * previous.average_entry + notional) / new_amount
        self.cash_balance -= notional + fee
        self.positions[symbol] = Position(new_amount, average_entry)
        return self._record_fill(symbol, "BUY", amount, snapshot, execution_price, notional, fee)

    def sell_market(self, symbol: str, amount: float, snapshot: MarketSnapshot | None = None) -> SimulatedFill:
        amount = _positive_number(amount, "amount")
        position = self.positions.get(symbol)
        if position is None or amount > position.amount + 1e-12:
            raise ValueError("insufficient virtual position; short selling is disabled")
        snapshot = snapshot or self.market_data.fetch_snapshot(symbol)
        execution_price = snapshot.bid * (1.0 - self.slippage_bps / 10_000.0)
        notional = amount * execution_price
        fee = notional * self.fee_bps / 10_000.0
        self.cash_balance += notional - fee
        remaining = position.amount - amount
        if remaining <= 1e-12:
            self.positions.pop(symbol, None)
        else:
            self.positions[symbol] = Position(remaining, position.average_entry)
        return self._record_fill(symbol, "SELL", amount, snapshot, execution_price, notional, fee)

    def _record_fill(
        self,
        symbol: str,
        side: str,
        amount: float,
        snapshot: MarketSnapshot,
        execution_price: float,
        notional: float,
        fee: float,
    ) -> SimulatedFill:
        position_amount = self.positions.get(symbol, Position(0.0, 0.0)).amount
        fill = SimulatedFill(
            trade_id=uuid.uuid4().hex,
            timestamp_utc=utc_now(),
            symbol=symbol,
            side=side,
            amount=amount,
            market_price=snapshot.last,
            execution_price=execution_price,
            notional_usdt=notional,
            fee_usdt=fee,
            cash_balance_usdt=self.cash_balance,
            position_amount=position_amount,
            equity_usdt=self.equity({symbol: snapshot.last}),
        )
        self._save_state()
        self.logger.append(fill)
        return fill


DecisionFunction = Callable[[MarketSnapshot, MockBroker], tuple[str, float]]


def run_live_loop(
    symbol: str,
    market_data: MarketDataSource,
    broker: MockBroker,
    decision_fn: DecisionFunction,
    *,
    interval_seconds: float = 15.0,
    once: bool = False,
    sleeper: Callable[[float], None] = time.sleep,
) -> None:
    interval_seconds = _positive_number(interval_seconds, "interval_seconds")
    while True:
        try:
            snapshot = market_data.fetch_snapshot(symbol)
            action, amount = decision_fn(snapshot, broker)
            action = str(action).upper().strip()
            fill = None
            if action == "BUY":
                fill = broker.buy_market(symbol, amount, snapshot)
            elif action == "SELL":
                fill = broker.sell_market(symbol, amount, snapshot)
            elif action != "HOLD":
                raise ValueError(f"unsupported decision action: {action}")
            equity = broker.equity({symbol: snapshot.last})
            print(
                f"{snapshot.timestamp_utc} | {symbol} last={snapshot.last:.8f} "
                f"bid={snapshot.bid:.8f} ask={snapshot.ask:.8f} provider={snapshot.provider} action={action} "
                f"equity=${equity:,.2f}",
                flush=True,
            )
            if fill:
                print(f"SIMULATED {fill.side} amount={fill.amount:.8f} price={fill.execution_price:.8f}", flush=True)
        except KeyboardInterrupt:
            print("Live demo stopped safely by user.", flush=True)
            return
        except Exception as exc:
            print(f"Live demo cycle warning: {type(exc).__name__}: {exc}", flush=True)
        if once:
            return
        try:
            sleeper(interval_seconds)
        except KeyboardInterrupt:
            print("Live demo stopped safely by user.", flush=True)
            return


def run_live_universe_loop(
    symbols: Sequence[str],
    market_data: MarketDataSource,
    broker: MockBroker,
    decision_fn: DecisionFunction,
    *,
    interval_seconds: float = 15.0,
    once: bool = False,
    sleeper: Callable[[float], None] = time.sleep,
) -> None:
    """Scan every symbol once per cycle, then wait once for the next cycle."""
    interval_seconds = _positive_number(interval_seconds, "interval_seconds")
    selected = tuple(dict.fromkeys(str(symbol).upper().strip() for symbol in symbols if str(symbol).strip()))
    if not selected:
        raise ValueError("at least one symbol is required")
    while True:
        successes = 0
        for symbol in selected:
            try:
                snapshot = market_data.fetch_snapshot(symbol)
                action, amount = decision_fn(snapshot, broker)
                action = str(action).upper().strip()
                fill = None
                if action == "BUY":
                    fill = broker.buy_market(symbol, amount, snapshot)
                elif action == "SELL":
                    fill = broker.sell_market(symbol, amount, snapshot)
                elif action != "HOLD":
                    raise ValueError(f"unsupported decision action: {action}")
                equity = broker.equity({symbol: snapshot.last})
                print(
                    f"{snapshot.timestamp_utc} | {symbol} last={snapshot.last:.8f} "
                    f"bid={snapshot.bid:.8f} ask={snapshot.ask:.8f} provider={snapshot.provider} "
                    f"action={action} equity=${equity:,.2f}",
                    flush=True,
                )
                if fill:
                    print(f"SIMULATED {fill.side} amount={fill.amount:.8f} price={fill.execution_price:.8f}", flush=True)
                successes += 1
            except KeyboardInterrupt:
                print("Live demo stopped safely by user.", flush=True)
                return
            except Exception as exc:
                print(f"Live demo symbol warning [{symbol}]: {type(exc).__name__}: {exc}", flush=True)
        print(f"Universe cycle complete: {successes}/{len(selected)} symbols available", flush=True)
        if once:
            return
        try:
            sleeper(interval_seconds)
        except KeyboardInterrupt:
            print("Live demo stopped safely by user.", flush=True)
            return
