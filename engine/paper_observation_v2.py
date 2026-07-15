"""Zero-real-order research paper observation engine.

The module writes virtual observations only.  It never imports an exchange
order API and cannot place a live order.  Strategy mode is fail-closed behind a
readiness artifact; research mode always records allocation_pct=0.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from engine.event_opportunity_universe import EventUniverseConfig, build_event_opportunity_universe
from engine.paper_readiness_v2 import PaperLaunchReadiness

VERSION = "1.0.0"
DEFAULT_OUTPUT_DIR = Path("logs") / "paper_launch_v2"
DEFAULT_LEDGER = Path("logs") / "paper_trades.csv"


@dataclass(frozen=True)
class PaperRiskConfig:
    virtual_equity: float = 10_000.0
    risk_per_trade_pct: float = 0.25
    max_open_trades: int = 5
    max_open_per_symbol: int = 1
    max_total_open_risk_pct: float = 1.0
    max_signal_age_hours: float = 12.0


@dataclass
class PaperObservationResult:
    attempted: int = 0
    recorded: int = 0
    duplicates: int = 0
    skipped: int = 0
    status: str = "NOT_RUN"
    mode: str = "DISARMED"
    recorded_ids: List[str] = field(default_factory=list)
    skipped_reasons: List[str] = field(default_factory=list)
    live_orders_enabled: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    except Exception:
        try:
            return pd.read_csv(path, low_memory=False)
        except Exception:
            return pd.DataFrame()


def _atomic_append(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_csv(path)
    combined = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True, sort=False)
    temp = path.with_suffix(path.suffix + ".tmp")
    combined.to_csv(temp, index=False, encoding="utf-8-sig")
    temp.replace(path)


def _trade_id(row: pd.Series) -> str:
    raw = "|".join(
        str(row.get(name, ""))
        for name in ("decision_id", "opportunity_id", "symbol", "timeframe", "side", "__timestamp")
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _policy_mask(events: pd.DataFrame, policy: str) -> pd.Series:
    gated = events.get("cost_gate_pass", pd.Series(False, index=events.index)).astype(bool)
    if policy == "EVENT_COST_GATED":
        return gated
    if policy.startswith("EVENT_") and policy.endswith("_COST_GATED"):
        name = policy[len("EVENT_") : -len("_COST_GATED")]
        return gated & events.get("primary_event", pd.Series("", index=events.index)).astype(str).eq(name)
    return pd.Series(False, index=events.index, dtype=bool)


def arm_paper_mode(
    readiness: PaperLaunchReadiness,
    mode: str,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> Path:
    mode = str(mode).strip().upper()
    if mode not in {"RESEARCH", "STRATEGY"}:
        raise ValueError("mode must be RESEARCH or STRATEGY")
    if mode == "RESEARCH" and not readiness.research_collection_ready:
        raise PermissionError("Research paper collection is not ready")
    if mode == "STRATEGY" and not readiness.strategy_paper_ready:
        raise PermissionError("Strategy paper validation is not ready")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "arm_state.json"
    payload = {
        "armed": True,
        "mode": mode,
        "armed_at_utc": datetime.now(timezone.utc).isoformat(),
        "readiness_status": readiness.status,
        "selected_policy": readiness.selected_policy or "EVENT_COST_GATED",
        "allocation_pct": 0.0,
        "live_orders_enabled": False,
        "real_capital_enabled": False,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def disarm_paper_mode(output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> Path:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / "arm_state.json"
    payload = {
        "armed": False,
        "mode": "DISARMED",
        "disarmed_at_utc": datetime.now(timezone.utc).isoformat(),
        "allocation_pct": 0.0,
        "live_orders_enabled": False,
        "real_capital_enabled": False,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_arm_state(output_dir: str | Path = DEFAULT_OUTPUT_DIR) -> Dict[str, Any]:
    path = Path(output_dir) / "arm_state.json"
    if not path.exists():
        return {"armed": False, "mode": "DISARMED", "live_orders_enabled": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"armed": False}
    except Exception:
        return {"armed": False, "mode": "DISARMED", "live_orders_enabled": False}


def record_paper_observations(
    decision_rows: pd.DataFrame,
    readiness: PaperLaunchReadiness,
    *,
    risk: Optional[PaperRiskConfig] = None,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    ledger_path: str | Path = DEFAULT_LEDGER,
    event_config: Optional[EventUniverseConfig] = None,
) -> PaperObservationResult:
    risk = risk or PaperRiskConfig()
    state = load_arm_state(output_dir)
    result = PaperObservationResult(status="BLOCKED_DISARMED", mode=str(state.get("mode", "DISARMED")))
    if not bool(state.get("armed")):
        result.skipped_reasons.append("Paper observation mode is disarmed.")
        return result
    mode = str(state.get("mode", "")).upper()
    if mode == "STRATEGY" and not readiness.strategy_paper_ready:
        result.status = "BLOCKED_STRATEGY_NOT_READY"
        result.skipped_reasons.append("Strategy readiness no longer passes.")
        return result
    if mode == "RESEARCH" and not readiness.research_collection_ready:
        result.status = "BLOCKED_RESEARCH_NOT_READY"
        result.skipped_reasons.append("Research collection readiness no longer passes.")
        return result
    if decision_rows is None or decision_rows.empty:
        result.status = "NO_DECISIONS"
        return result

    config = event_config or EventUniverseConfig()
    events, _ = build_event_opportunity_universe(decision_rows, config, time_scope="paper")
    policy = str(state.get("selected_policy") or readiness.selected_policy or "EVENT_COST_GATED")
    selected = events[_policy_mask(events, policy)].copy() if not events.empty else events
    result.attempted = int(len(selected))
    ledger = _read_csv(Path(ledger_path))
    existing_ids = set(ledger.get("paper_trade_id", pd.Series(dtype=str)).astype(str)) if not ledger.empty else set()
    open_rows = ledger[ledger.get("status", pd.Series("", index=ledger.index)).astype(str).str.upper().isin(["OPEN", "ACTIVE", "PENDING"])] if not ledger.empty else pd.DataFrame()
    open_symbols = open_rows.get("symbol", pd.Series(dtype=str)).astype(str).value_counts().to_dict() if not open_rows.empty else {}
    open_risk_pct = float(pd.to_numeric(open_rows.get("virtual_risk_pct"), errors="coerce").fillna(0).sum()) if not open_rows.empty else 0.0
    rows: List[Dict[str, Any]] = []
    now = pd.Timestamp.now(tz="UTC")
    for _, row in selected.sort_values("__timestamp", kind="stable").iterrows():
        trade_id = _trade_id(row)
        if trade_id in existing_ids:
            result.duplicates += 1
            continue
        symbol = str(row.get("symbol", "UNKNOWN"))
        timestamp = pd.to_datetime(row.get("__timestamp"), utc=True, errors="coerce")
        age_hours = float((now - timestamp).total_seconds() / 3600.0) if pd.notna(timestamp) else float("inf")
        if age_hours > risk.max_signal_age_hours:
            result.skipped += 1
            result.skipped_reasons.append(f"{symbol}: stale signal age={age_hours:.2f}h")
            continue
        if len(open_rows) + len(rows) >= risk.max_open_trades:
            result.skipped += 1
            result.skipped_reasons.append("Maximum open paper trades reached.")
            continue
        if int(open_symbols.get(symbol, 0)) + sum(1 for item in rows if item["symbol"] == symbol) >= risk.max_open_per_symbol:
            result.skipped += 1
            result.skipped_reasons.append(f"{symbol}: maximum open trades per symbol reached.")
            continue
        if open_risk_pct + sum(float(item["virtual_risk_pct"]) for item in rows) + risk.risk_per_trade_pct > risk.max_total_open_risk_pct + 1e-12:
            result.skipped += 1
            result.skipped_reasons.append("Maximum total open virtual risk reached.")
            continue
        entry = float(row.get("entry_price_normalized"))
        stop = float(row.get("stop_price_normalized"))
        target = float(row.get("target_price_normalized"))
        virtual_risk_amount = risk.virtual_equity * risk.risk_per_trade_pct / 100.0
        record = {
            "paper_trade_id": trade_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "entry_time": pd.Timestamp(timestamp).isoformat(),
            "symbol": symbol,
            "timeframe": str(row.get("timeframe", "4h")),
            "side": str(row.get("side", "")),
            "entry": entry,
            "stop": stop,
            "target_1": target,
            "target_2": None,
            "target_3": None,
            "score": row.get("score", 0),
            "confidence": row.get("regime_confidence", 0),
            "recommendation": "RESEARCH_PAPER" if mode == "RESEARCH" else "STRATEGY_PAPER",
            "primary_event": row.get("primary_event", ""),
            "event_types": row.get("event_types", "[]"),
            "opportunity_id": row.get("opportunity_id", ""),
            "cost_gate_pass": True,
            "gross_target_to_cost": row.get("gross_target_to_cost"),
            "net_reward_risk": row.get("net_reward_risk"),
            "fee_bps_per_side": row.get("fee_bps_per_side", 10.0),
            "base_slippage_bps_per_side": row.get("slippage_bps_per_side", 5.0),
            "dynamic_execution_costs": True,
            "virtual_equity": risk.virtual_equity,
            "virtual_risk_pct": risk.risk_per_trade_pct,
            "virtual_risk_amount": virtual_risk_amount,
            "allocation_pct": 0.0,
            "real_capital_enabled": False,
            "live_orders_enabled": False,
            "paper_mode": mode,
            "frozen_policy": policy,
            "status": "OPEN",
            "source": "paper_launch_v2",
            "notes": "Zero-real-order observation; next-bar evaluation required.",
        }
        rows.append(record)
        existing_ids.add(trade_id)
        result.recorded_ids.append(trade_id)
    _atomic_append(Path(ledger_path), rows)
    result.recorded = len(rows)
    result.status = "RECORDED" if rows else "NO_ELIGIBLE_NEW_OBSERVATIONS"
    result.live_orders_enabled = False
    audit_path = Path(output_dir) / "paper_observation_last_run.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return result
