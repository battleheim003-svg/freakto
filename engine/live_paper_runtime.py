"""Fail-closed Decision-to-Execution runtime for Freakto shadow/paper testing."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from engine.live_demo import MarketSnapshot, MockBroker
from engine.live_demo_universe import UniverseConfig
from engine.paper_trading import _parse_targets, _parse_zone_midpoint, _safe_float


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except Exception as exc:
        raise RuntimeError(f"state unreadable: {path}: {type(exc).__name__}") from exc


def _append_csv(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row), extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


@dataclass(frozen=True)
class RuntimeConfig:
    initial_balance_usdt: float
    timeframe: str
    data_dir: str
    state_roots: dict[str, str]
    risk: dict[str, float]
    execution: dict[str, Any]
    rollout: dict[str, str]
    shadow_gate: dict[str, float]
    notifications: dict[str, Any]


def load_runtime_config(path: str | Path = "live_paper_config.json") -> RuntimeConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported live paper config schema")
    return RuntimeConfig(**{key: payload[key] for key in RuntimeConfig.__dataclass_fields__})


def symbol_group(symbol: str, universe: UniverseConfig) -> str:
    for name, symbols in universe.groups.items():
        if symbol in symbols:
            return name
    return "unknown"


@dataclass(frozen=True)
class Eligibility:
    eligible: bool
    status: str
    blockers: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    spread_bps: float = 0.0
    history_status: str = "MISSING"


def evaluate_eligibility(symbol: str, snapshot: MarketSnapshot, config: RuntimeConfig) -> Eligibility:
    blockers: list[str] = []
    warnings: list[str] = []
    spread_bps = ((snapshot.ask - snapshot.bid) / snapshot.last * 10_000.0) if snapshot.last > 0 else math.inf
    if spread_bps < 0 or spread_bps > float(config.execution["maximum_spread_bps"]):
        blockers.append(f"spread {spread_bps:.2f}bps exceeds limit")
    manifest = Path(config.data_dir) / config.timeframe / f"{symbol.replace('/', '_').upper()}.manifest.json"
    history_status = "MISSING"
    if manifest.exists():
        payload = _read_json(manifest, {})
        quality = (((payload.get("result") or {}).get("quality") or {}))
        history_status = str(quality.get("readiness_status", "MISSING"))
    if history_status not in {"REPLAY_READY", "REPLAY_READY_WITH_WARNINGS"}:
        blockers.append(f"history status={history_status}")
    if snapshot.provider == "unknown":
        warnings.append("provider identity unavailable")
    try:
        observed = _parse_utc(snapshot.timestamp_utc)
        age_seconds = (_utc_now() - observed.astimezone(timezone.utc)).total_seconds()
        if age_seconds < -30 or age_seconds > 180:
            blockers.append(f"stale ticker age={age_seconds:.0f}s")
    except Exception:
        blockers.append("invalid ticker timestamp")
    return Eligibility(not blockers, "ELIGIBLE" if not blockers else "BLOCKED", tuple(blockers), tuple(warnings), spread_bps, history_status)


@dataclass(frozen=True)
class TradeIntent:
    decision_id: str
    timestamp_utc: str
    candle_timestamp: str
    symbol: str
    group: str
    action: str
    entry: float
    stop: float
    targets: tuple[float, ...]
    score: int
    confidence: int
    recommendation: str
    first_rr: float
    regime: str
    mtf_direction: str
    mtf_consensus: int
    expected_r: float
    calibration_status: str
    evidence: dict[str, Any] = field(default_factory=dict)


def intent_from_portfolio_item(item: Any, group: str) -> TradeIntent:
    entry = _parse_zone_midpoint(getattr(item, "entry_zone", "")) or _safe_float(getattr(item, "price", 0))
    stop = _safe_float(getattr(item, "stop_zone", ""))
    targets = tuple(_parse_targets(getattr(item, "targets", ())))
    candle = str(getattr(item, "decision_timestamp", ""))
    raw = "|".join([str(item.symbol), str(item.timeframe), candle, str(item.side), str(entry), str(stop)])
    decision_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    action = "BUY" if getattr(item, "side", "") == "LONG" else "HOLD"
    return TradeIntent(
        decision_id, _utc_now().isoformat(), candle, str(item.symbol), group, action,
        float(entry or 0), float(stop or 0), targets, int(item.score), int(item.confidence),
        str(item.recommendation), float(item.first_rr), str(item.regime), str(item.mtf_direction),
        int(item.mtf_consensus), float(item.expected_r), str(item.calibration_status),
        {"opportunity_score": item.opportunity_score, "trade_quality": item.trade_quality_grade, "notes": list(item.notes)},
    )


def validate_intent(intent: TradeIntent, config: RuntimeConfig, eligibility: Eligibility) -> tuple[bool, list[str]]:
    blockers = list(eligibility.blockers)
    if intent.action != "BUY": blockers.append("spot-long runtime accepts LONG entries only")
    if intent.recommendation not in config.execution["allowed_recommendations"]: blockers.append("recommendation not allowed")
    if intent.confidence < int(config.execution["minimum_confidence"]): blockers.append("confidence below minimum")
    if intent.first_rr < float(config.execution["minimum_rr"]): blockers.append("RR below minimum")
    if intent.entry <= 0 or intent.stop <= 0 or intent.stop >= intent.entry: blockers.append("invalid long geometry")
    if not intent.targets or intent.targets[0] <= intent.entry: blockers.append("invalid targets")
    if intent.mtf_direction != "LONG": blockers.append("MTF does not confirm LONG")
    return not blockers, blockers


def position_size(equity: float, intent: TradeIntent, group: str, config: RuntimeConfig) -> tuple[float, dict]:
    risk_pct = float(config.risk[f"{group}_risk_pct"])
    risk_usdt = equity * risk_pct / 100.0
    unit_risk = intent.entry - intent.stop
    amount = risk_usdt / unit_risk if unit_risk > 0 else 0.0
    max_notional = equity * float(config.risk["maximum_symbol_exposure_pct"]) / 100.0
    amount = min(amount, max_notional / intent.entry)
    return max(0.0, amount), {"risk_pct": risk_pct, "risk_usdt": risk_usdt, "max_notional": max_notional}


class RuntimeStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.state_file = self.root / "runtime_state.json"
        self.intents_file = self.root / "intents.csv"
        self.events_file = self.root / "events.csv"
        self.evidence_dir = self.root / "evidence"
        self.state = _read_json(self.state_file, {"started_at_utc": _utc_now().isoformat(), "processed_decisions": [], "observed_candles": [], "managed_positions": {}, "daily": {"date": _utc_now().date().isoformat(), "start_equity": 10000.0}, "metrics": {"unique_decisions": 0, "duplicate_executions": 0, "open_candle_decisions": 0, "complete_4h_candles": 0, "state_corruptions": 0, "unhandled_crashes": 0, "provider_checks": 0, "provider_fresh": 0, "closed_trades": 0, "core_closed_trades": 0}})

    def save(self) -> None:
        _atomic_json(self.state_file, self.state)

    def seen(self, decision_id: str) -> bool:
        return decision_id in set(self.state["processed_decisions"])

    def record_intent(self, intent: TradeIntent, status: str, blockers: Iterable[str]) -> None:
        _append_csv(self.intents_file, {**asdict(intent), "targets": json.dumps(intent.targets), "evidence": json.dumps(intent.evidence, ensure_ascii=False), "status": status, "blockers": " | ".join(blockers)})
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        _atomic_json(self.evidence_dir / f"{intent.decision_id}.json", asdict(intent))
        if not self.seen(intent.decision_id):
            self.state["processed_decisions"].append(intent.decision_id)
            self.state["metrics"]["unique_decisions"] += 1
        self.save()


class RuntimeLock:
    """Single-process lock; stale locks can be removed only with explicit CLI recovery."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.acquired = False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"runtime lock already exists: {self.path}") from exc
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps({"pid": os.getpid(), "created_at_utc": _utc_now().isoformat()}))
        self.acquired = True
        return self

    def __exit__(self, *_args):
        if self.acquired:
            try: self.path.unlink()
            except FileNotFoundError: pass
        self.acquired = False


def shadow_gate_status(store: RuntimeStore, config: RuntimeConfig) -> dict:
    metrics = store.state["metrics"]
    started = _parse_utc(store.state["started_at_utc"])
    days = max(0.0, (_utc_now() - started).total_seconds() / 86400.0)
    provider_checks = int(metrics["provider_checks"])
    freshness = (int(metrics["provider_fresh"]) / provider_checks * 100.0) if provider_checks else 0.0
    gate = config.shadow_gate
    checks = {
        "minimum_days": days >= float(gate["minimum_days"]),
        "minimum_unique_decisions": int(metrics["unique_decisions"]) >= int(gate["minimum_unique_decisions"]),
        "minimum_complete_4h_candles": int(metrics.get("complete_4h_candles", 0)) >= int(gate["minimum_complete_4h_candles"]),
        "duplicates": int(metrics["duplicate_executions"]) <= int(gate["maximum_duplicate_executions"]),
        "open_candles": int(metrics["open_candle_decisions"]) <= int(gate["maximum_open_candle_decisions"]),
        "state": int(metrics["state_corruptions"]) <= int(gate["maximum_state_corruptions"]),
        "crashes": int(metrics["unhandled_crashes"]) <= int(gate["maximum_unhandled_crashes"]),
        "provider_freshness": freshness >= float(gate["minimum_provider_freshness_pct"]),
    }
    return {"passed": all(checks.values()), "days": round(days, 3), "provider_freshness_pct": round(freshness, 2), "checks": checks, "metrics": metrics}


class LivePaperRuntime:
    def __init__(self, config: RuntimeConfig, universe: UniverseConfig, market_data, *, mode: str = "shadow", analyzer: Callable[[str], Any] | None = None, notifier: Callable[[str], bool] | None = None):
        self.config, self.universe, self.market_data = config, universe, market_data
        self.mode = mode.lower()
        if self.mode not in {"shadow", "paper"}: raise ValueError("mode must be shadow or paper")
        self.root = Path(config.state_roots[self.mode])
        self.store = RuntimeStore(self.root)
        self.broker = MockBroker(market_data, initial_balance=config.initial_balance_usdt, fee_bps=config.execution["fee_bps"], slippage_bps=config.execution["slippage_bps"], state_path=self.root / "account_state.json", trade_log_path=self.root / "fills.csv")
        self.analyzer = analyzer or self._default_analyzer
        self.notifier = notifier

    @staticmethod
    def _default_analyzer(symbol: str):
        from portfolio_scanner import analyze_symbol
        return analyze_symbol(symbol)

    def _execution_authorized(self) -> bool:
        flag = os.getenv("LIVE_DEMO_EXECUTION_ENABLED", "false").lower() in {"1", "true", "yes"}
        if self.mode != "paper" or not flag: return False
        shadow = RuntimeStore(self.config.state_roots["shadow"])
        return bool(shadow_gate_status(shadow, self.config)["passed"])

    def process_symbol(self, symbol: str) -> dict:
        snapshot = self.market_data.fetch_snapshot(symbol)
        self.store.state["metrics"]["provider_checks"] += 1
        self.store.state["metrics"]["provider_fresh"] += 1
        eligibility = evaluate_eligibility(symbol, snapshot, self.config)
        group = symbol_group(symbol, self.universe)
        item = self.analyzer(symbol)
        intent = intent_from_portfolio_item(item, group)
        try:
            candle = _parse_utc(intent.candle_timestamp)
            timeframe_hours = 4 if self.config.timeframe == "4h" else 0
            candle_key = f"{symbol}|{intent.candle_timestamp}"
            if timeframe_hours and candle.timestamp() + timeframe_hours * 3600 > _utc_now().timestamp():
                self.store.state["metrics"]["open_candle_decisions"] += 1
                eligibility = Eligibility(False, "BLOCKED_OPEN_CANDLE", ("decision uses an open candle",), eligibility.warnings, eligibility.spread_bps, eligibility.history_status)
            elif candle_key not in self.store.state["observed_candles"]:
                self.store.state["observed_candles"].append(candle_key)
                self.store.state["metrics"]["complete_4h_candles"] += 1
        except Exception:
            eligibility = Eligibility(False, "BLOCKED_INVALID_CANDLE", ("decision candle timestamp invalid",), eligibility.warnings, eligibility.spread_bps, eligibility.history_status)
        if self.store.seen(intent.decision_id):
            return {"symbol": symbol, "status": "DUPLICATE_IGNORED", "decision_id": intent.decision_id}
        valid, blockers = validate_intent(intent, self.config, eligibility)
        rollout = self.config.rollout.get(group, "LOCKED")
        if group == "growth" and self.store.state["metrics"]["core_closed_trades"] < 10: blockers.append("growth rollout locked")
        if group == "meme" and self.store.state["metrics"]["closed_trades"] < 20: blockers.append("meme rollout locked")
        valid = valid and not blockers
        status = "SHADOW_CANDIDATE" if valid else "BLOCKED"
        self.store.record_intent(intent, status, blockers)
        if not valid or not self._execution_authorized():
            return {"symbol": symbol, "status": status, "decision_id": intent.decision_id, "blockers": blockers}
        if symbol in self.broker.positions: return {"symbol": symbol, "status": "BLOCKED_POSITION_EXISTS"}
        if len(self.broker.positions) >= int(self.config.risk["maximum_concurrent_positions"]): return {"symbol": symbol, "status": "BLOCKED_MAX_POSITIONS"}
        if group == "meme" and sum(symbol_group(s, self.universe) == "meme" for s in self.broker.positions) >= int(self.config.risk["maximum_concurrent_meme_positions"]): return {"symbol": symbol, "status": "BLOCKED_MEME_LIMIT"}
        equity = self.broker.equity()
        if equity <= self.config.initial_balance_usdt * (1.0 - float(self.config.risk["emergency_drawdown_pct"]) / 100.0):
            return {"symbol": symbol, "status": "CIRCUIT_BREAKER_DRAWDOWN"}
        today = _utc_now().date().isoformat()
        if self.store.state["daily"]["date"] != today:
            self.store.state["daily"] = {"date": today, "start_equity": equity}
        if equity <= float(self.store.state["daily"]["start_equity"]) * (1.0 - float(self.config.risk["daily_loss_limit_pct"]) / 100.0):
            return {"symbol": symbol, "status": "CIRCUIT_BREAKER_DAILY_LOSS"}
        open_risk_usdt = sum(max(0.0, (float(p["entry"]) - float(p["stop"])) * float(p["amount"])) for p in self.store.state["managed_positions"].values())
        if open_risk_usdt / max(equity, 1e-9) * 100.0 >= float(self.config.risk["maximum_open_risk_pct"]):
            return {"symbol": symbol, "status": "BLOCKED_MAX_OPEN_RISK"}
        amount, sizing = position_size(self.broker.equity(), intent, group, self.config)
        fill = self.broker.buy_market(symbol, amount, snapshot)
        self.store.state["managed_positions"][symbol] = {"decision_id": intent.decision_id, "group": group, "stop": intent.stop, "targets": list(intent.targets), "next_target_index": 0, "entry": fill.execution_price, "amount": fill.amount, "opened_at_utc": fill.timestamp_utc}
        self.store.save()
        if self.notifier: self.notifier(f"Freakto PAPER ENTRY\n{symbol} amount={amount:.8f} price={fill.execution_price:.8f}\nPaper only; no real order.")
        return {"symbol": symbol, "status": "PAPER_ENTRY", "fill": asdict(fill), "sizing": sizing}

    def manage_exits(self) -> list[dict]:
        events = []
        for symbol, managed in list(self.store.state["managed_positions"].items()):
            snapshot = self.market_data.fetch_snapshot(symbol)
            reason = ""
            if snapshot.bid <= float(managed["stop"]): reason = "STOP"
            else:
                target_index = int(managed.get("next_target_index", 0))
                targets = list(managed.get("targets", []))
                if target_index < len(targets) and snapshot.bid >= float(targets[target_index]): reason = f"TARGET_{target_index + 1}"
            if not reason: continue
            position = self.broker.positions.get(symbol)
            if not position: continue
            is_stop = reason == "STOP"
            target_index = int(managed.get("next_target_index", 0))
            targets = list(managed.get("targets", []))
            final_target = not is_stop and target_index >= len(targets) - 1
            sell_amount = position.amount if is_stop or final_target else position.amount * 0.5
            fill = self.broker.sell_market(symbol, sell_amount, snapshot)
            fully_closed = symbol not in self.broker.positions
            if fully_closed:
                self.store.state["managed_positions"].pop(symbol, None)
                self.store.state["metrics"]["closed_trades"] += 1
                if managed["group"] == "core": self.store.state["metrics"]["core_closed_trades"] += 1
            else:
                managed["next_target_index"] = target_index + 1
                managed["amount"] = self.broker.positions[symbol].amount
                self.store.state["managed_positions"][symbol] = managed
            event = {"timestamp_utc": fill.timestamp_utc, "symbol": symbol, "event": reason, "exit_price": fill.execution_price, "decision_id": managed["decision_id"]}
            _append_csv(self.store.events_file, event)
            events.append(event)
            if self.notifier: self.notifier(f"Freakto PAPER {reason}\n{symbol} amount={fill.amount:.8f} price={fill.execution_price:.8f}\nfully_closed={fully_closed}")
        self.store.save()
        return events
