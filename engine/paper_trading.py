"""
engine.paper_trading

Freakto v4.7.1.0 Practical Testing Suite

Paper Trading Engine:
- records virtual trades from Portfolio Scanner candidates
- never sends real orders
- evaluates paper trades against future OHLCV candles
- stores reports in logs/paper_trading
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd

from .common import fmt_price
from .execution_model import estimate_execution_cost
from .model_contract import CURRENT_MODEL_CONTRACT
from .paper_trade_readiness import run_paper_trade_preflight

LOGS_DIR = Path("logs")
PAPER_DIR = LOGS_DIR / "paper_trading"
PAPER_TRADES_FILE = LOGS_DIR / "paper_trades.csv"
PAPER_EVALUATIONS_FILE = LOGS_DIR / "paper_trade_evaluations.csv"

PAPER_ALLOWED_RECOMMENDATIONS = {"ELITE", "ACTIONABLE", "WATCHLIST"}
DEFAULT_MIN_RR = 1.20
DEFAULT_MIN_CONFIDENCE = 50
DEFAULT_FEE_BPS_PER_SIDE = 10.0
DEFAULT_SLIPPAGE_BPS_PER_SIDE = 5.0


@dataclass
class PaperTradeCandidate:
    symbol: str
    timeframe: str
    side: str
    recommendation: str
    entry: Optional[float]
    stop: Optional[float]
    targets: List[float] = field(default_factory=list)
    score: int = 0
    confidence: int = 0
    opportunity_score: float = 0.0
    trade_quality_grade: str = ""
    trade_quality_score: int = 0
    first_rr: float = 0.0
    mtf_direction: str = ""
    mtf_consensus: int = 0
    market_mode: str = "UNKNOWN"
    risk_tone: str = "UNKNOWN"
    provider: str = ""
    source: str = "portfolio_scanner"
    notes: List[str] = field(default_factory=list)


@dataclass
class PaperRecordResult:
    attempted: int = 0
    recorded: int = 0
    skipped: int = 0
    duplicates: int = 0
    rows: List[dict] = field(default_factory=list)
    skipped_reasons: List[str] = field(default_factory=list)
    preflight_status: str = "NOT_RUN"
    blockers: List[str] = field(default_factory=list)


@dataclass
class PaperEvaluationSummary:
    total_trades: int = 0
    evaluated_rows: int = 0
    complete_rows: int = 0
    open_rows: int = 0
    win_rows: int = 0
    loss_rows: int = 0
    avg_r: float = 0.0
    expectancy_r: float = 0.0
    win_rate: float = 0.0
    best_r: float = 0.0
    worst_r: float = 0.0
    report_path: str = ""


# ---------- parsing helpers ----------

def _safe_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        text = str(value).strip().replace("`", "").replace(",", "")
        if not text or text in {"---", "-", "None", "nan", "NaN", "نامشخص"}:
            return None
        return float(text)
    except Exception:
        return None


def _parse_zone_midpoint(zone: str) -> Optional[float]:
    if not zone:
        return None
    text = str(zone).replace("`", "").replace(",", "")
    if "نامشخص" in text or text.strip() in {"---", "-"}:
        return None
    parts = [part.strip() for part in text.split("-")]
    values = [_safe_float(part) for part in parts]
    values = [value for value in values if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _parse_targets(targets) -> List[float]:
    if not targets:
        return []
    if isinstance(targets, str):
        try:
            parsed = json.loads(targets)
            targets = parsed
        except Exception:
            targets = [part.strip() for part in targets.split("|")]
    result = []
    for target in targets:
        value = _safe_float(target)
        if value is not None:
            result.append(value)
    return result


def _make_trade_id(candidate: PaperTradeCandidate, entry_time: str) -> str:
    raw = "|".join([
        str(entry_time),
        candidate.symbol,
        candidate.timeframe,
        candidate.side,
        str(candidate.entry),
        str(candidate.stop),
        ",".join(str(x) for x in candidate.targets[:3]),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def _append_rows(path: Path, rows: List[dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = _load_csv(path)
    combined = pd.concat([existing, pd.DataFrame(rows)], ignore_index=True, sort=False)
    temp = path.with_suffix(path.suffix + ".tmp")
    combined.to_csv(temp, index=False, encoding="utf-8-sig")
    temp.replace(path)


# ---------- candidate creation ----------

def candidate_from_portfolio_item(item, market_breadth=None) -> PaperTradeCandidate:
    entry = _parse_zone_midpoint(getattr(item, "entry_zone", ""))
    stop = _safe_float(getattr(item, "stop_zone", ""))
    targets = _parse_targets(getattr(item, "targets", []))
    if entry is None:
        entry = _safe_float(getattr(item, "price", None))

    return PaperTradeCandidate(
        symbol=str(getattr(item, "symbol", "")),
        timeframe=str(getattr(item, "timeframe", "")),
        side=str(getattr(item, "side", "")),
        recommendation=str(getattr(item, "recommendation", "")),
        entry=entry,
        stop=stop,
        targets=targets,
        score=int(getattr(item, "score", 0) or 0),
        confidence=int(getattr(item, "confidence", 0) or 0),
        opportunity_score=float(getattr(item, "opportunity_score", 0.0) or 0.0),
        trade_quality_grade=str(getattr(item, "trade_quality_grade", "") or ""),
        trade_quality_score=int(getattr(item, "trade_quality_score", 0) or 0),
        first_rr=float(getattr(item, "first_rr", 0.0) or 0.0),
        mtf_direction=str(getattr(item, "mtf_direction", "") or ""),
        mtf_consensus=int(getattr(item, "mtf_consensus", 0) or 0),
        market_mode=str(getattr(market_breadth, "market_mode", "UNKNOWN") or "UNKNOWN") if market_breadth else "UNKNOWN",
        risk_tone=str(getattr(market_breadth, "risk_tone", "UNKNOWN") or "UNKNOWN") if market_breadth else "UNKNOWN",
        provider=str(getattr(item, "provider", "") or ""),
        notes=list(getattr(item, "notes", []) or []),
    )


def _candidate_is_allowed(candidate: PaperTradeCandidate, min_rr: float, min_confidence: int) -> tuple[bool, str]:
    if candidate.recommendation not in PAPER_ALLOWED_RECOMMENDATIONS:
        return False, f"{candidate.symbol}: recommendation={candidate.recommendation}"
    if candidate.side not in {"LONG", "SHORT"}:
        return False, f"{candidate.symbol}: side={candidate.side}"
    if candidate.trade_quality_grade == "Avoid":
        return False, f"{candidate.symbol}: Trade Quality Avoid"
    if candidate.first_rr < min_rr:
        return False, f"{candidate.symbol}: RR {candidate.first_rr:.2f} < {min_rr:.2f}"
    if candidate.confidence < min_confidence:
        return False, f"{candidate.symbol}: Confidence {candidate.confidence}% < {min_confidence}%"
    if candidate.entry is None or candidate.stop is None:
        return False, f"{candidate.symbol}: Entry/Stop missing"
    if not candidate.targets:
        return False, f"{candidate.symbol}: Targets missing"
    return True, "OK"


def record_paper_trades_from_portfolio(
    result,
    min_rr: float = DEFAULT_MIN_RR,
    min_confidence: int = DEFAULT_MIN_CONFIDENCE,
    *,
    require_preflight: bool = True,
    fee_bps_per_side: float = DEFAULT_FEE_BPS_PER_SIDE,
    slippage_bps_per_side: float = DEFAULT_SLIPPAGE_BPS_PER_SIDE,
) -> PaperRecordResult:
    """Record paper trades from eligible PortfolioScanResult candidates.

    This is intentionally conservative. MONITOR candidates are not recorded as trades.
    """
    items = list(getattr(result, "ranked_items", []) or [])
    preflight = run_paper_trade_preflight()
    if require_preflight and not preflight.ready:
        return PaperRecordResult(
            attempted=len(items), skipped=len(items), preflight_status=preflight.status,
            blockers=list(preflight.blockers),
            skipped_reasons=["Paper trade recording blocked by research preflight."],
        )
    market_breadth = getattr(result, "market_breadth", None)
    existing = _load_csv(PAPER_TRADES_FILE)
    existing_ids = set(existing.get("paper_trade_id", [])) if not existing.empty else set()

    rows = []
    record_result = PaperRecordResult(attempted=len(items), preflight_status=preflight.status)
    now = datetime.now(timezone.utc).isoformat()

    for item in items:
        candidate = candidate_from_portfolio_item(item, market_breadth=market_breadth)
        allowed, reason = _candidate_is_allowed(candidate, min_rr=min_rr, min_confidence=min_confidence)
        if not allowed:
            record_result.skipped += 1
            if len(record_result.skipped_reasons) < 12:
                record_result.skipped_reasons.append(reason)
            continue

        entry_time = str(getattr(item, "decision_timestamp", "") or now)
        trade_id = _make_trade_id(candidate, entry_time=entry_time)
        if trade_id in existing_ids:
            record_result.duplicates += 1
            continue

        target_1 = candidate.targets[0] if len(candidate.targets) >= 1 else None
        target_2 = candidate.targets[1] if len(candidate.targets) >= 2 else None
        target_3 = candidate.targets[2] if len(candidate.targets) >= 3 else None

        row = {
            "paper_trade_id": trade_id,
            "created_at_utc": now,
            "entry_time": entry_time,
            "symbol": candidate.symbol,
            "timeframe": candidate.timeframe,
            "side": candidate.side,
            "entry": candidate.entry,
            "stop": candidate.stop,
            "target_1": target_1,
            "target_2": target_2,
            "target_3": target_3,
            "score": candidate.score,
            "confidence": candidate.confidence,
            "opportunity_score": candidate.opportunity_score,
            "recommendation": candidate.recommendation,
            "trade_quality_grade": candidate.trade_quality_grade,
            "trade_quality_score": candidate.trade_quality_score,
            "first_rr": candidate.first_rr,
            "mtf_direction": candidate.mtf_direction,
            "mtf_consensus": candidate.mtf_consensus,
            "market_mode": candidate.market_mode,
            "risk_tone": candidate.risk_tone,
            "provider": candidate.provider,
            **CURRENT_MODEL_CONTRACT.as_dict(),
            "fee_bps_per_side": float(fee_bps_per_side),
            "base_slippage_bps_per_side": float(slippage_bps_per_side),
            "dynamic_execution_costs": True,
            "status": "OPEN",
            "source": candidate.source,
            "notes": " | ".join(str(x) for x in candidate.notes[:8]),
        }
        rows.append(row)
        existing_ids.add(trade_id)

    _append_rows(PAPER_TRADES_FILE, rows)
    record_result.recorded = len(rows)
    record_result.rows = rows
    return record_result


# ---------- evaluation ----------

def _normalize_market_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    market = df.copy()
    if "timestamp" in market.columns:
        market["timestamp"] = pd.to_datetime(market["timestamp"], errors="coerce")
        market = market.dropna(subset=["timestamp"])
        market = market.set_index("timestamp")
    market = market.sort_index()
    return market


def _find_entry_index(market_df: pd.DataFrame, entry_time) -> Optional[int]:
    ts = pd.to_datetime(entry_time, errors="coerce")
    if pd.isna(ts):
        return None
    matches = market_df.index[market_df.index == ts]
    if len(matches) > 0:
        return int(market_df.index.get_loc(matches[0]))
    # fallback: first candle after timestamp
    later = market_df.index[market_df.index >= ts]
    if len(later) > 0:
        return int(market_df.index.get_loc(later[0]))
    return None


def _evaluate_one_trade(trade: dict, market_df: pd.DataFrame) -> dict:
    entry_idx = _find_entry_index(market_df, trade.get("entry_time"))
    now = datetime.now(timezone.utc).isoformat()

    base = {
        "paper_trade_id": trade.get("paper_trade_id", ""),
        "evaluated_at_utc": now,
        "entry_time": trade.get("entry_time", ""),
        "symbol": trade.get("symbol", ""),
        "timeframe": trade.get("timeframe", ""),
        "side": trade.get("side", ""),
        "entry": _safe_float(trade.get("entry")),
        "stop": _safe_float(trade.get("stop")),
        "target_1": _safe_float(trade.get("target_1")),
        "status": "OPEN",
        "result": "OPEN",
        "available_future_candles": 0,
        "exit_time": "",
        "exit_price": None,
        "r_multiple": 0.0,
        "gross_r_multiple": 0.0,
        "net_r_multiple": 0.0,
        "round_trip_cost_pct": 0.0,
        "cost_r": 0.0,
        "effective_slippage_bps_per_side": 0.0,
        "mfe_r": 0.0,
        "mae_r": 0.0,
        "latest_unrealized_r": 0.0,
        "reason": "",
    }

    if entry_idx is None:
        base["status"] = "PENDING"
        base["result"] = "PENDING"
        base["reason"] = "Entry candle not found yet."
        return base

    future = market_df.iloc[entry_idx + 1:]
    base["available_future_candles"] = len(future)
    if future.empty:
        base["reason"] = "No future candle yet."
        return base

    entry = base["entry"]
    stop = base["stop"]
    target = base["target_1"]
    side = base["side"]
    if entry is None or stop is None or target is None or entry <= 0:
        base["status"] = "INVALID"
        base["result"] = "INVALID"
        base["reason"] = "Entry/Stop/Target invalid."
        return base

    risk_abs = abs(entry - stop)
    if risk_abs <= 0:
        base["status"] = "INVALID"
        base["result"] = "INVALID"
        base["reason"] = "Risk distance invalid."
        return base

    highs = future["high"].astype(float)
    lows = future["low"].astype(float)
    closes = future["close"].astype(float)

    if side == "LONG":
        mfe = (highs.max() - entry) / risk_abs
        mae = (lows.min() - entry) / risk_abs
        latest_r = (closes.iloc[-1] - entry) / risk_abs
        for idx, candle in future.iterrows():
            # Conservative: if both stop and target are inside same candle, count stop first.
            if float(candle["low"]) <= stop:
                base.update({"status": "CLOSED", "result": "LOSS", "exit_time": str(idx), "exit_price": stop, "r_multiple": -1.0, "reason": "Stop hit."})
                break
            if float(candle["high"]) >= target:
                reward_r = abs(target - entry) / risk_abs
                base.update({"status": "CLOSED", "result": "WIN", "exit_time": str(idx), "exit_price": target, "r_multiple": round(reward_r, 4), "reason": "Target 1 hit."})
                break
    elif side == "SHORT":
        mfe = (entry - lows.min()) / risk_abs
        mae = (entry - highs.max()) / risk_abs
        latest_r = (entry - closes.iloc[-1]) / risk_abs
        for idx, candle in future.iterrows():
            if float(candle["high"]) >= stop:
                base.update({"status": "CLOSED", "result": "LOSS", "exit_time": str(idx), "exit_price": stop, "r_multiple": -1.0, "reason": "Stop hit."})
                break
            if float(candle["low"]) <= target:
                reward_r = abs(entry - target) / risk_abs
                base.update({"status": "CLOSED", "result": "WIN", "exit_time": str(idx), "exit_price": target, "r_multiple": round(reward_r, 4), "reason": "Target 1 hit."})
                break
    else:
        mfe = 0.0
        mae = 0.0
        latest_r = 0.0
        base["status"] = "INVALID"
        base["result"] = "INVALID"
        base["reason"] = "Side is not directional."

    base["mfe_r"] = round(float(mfe), 4)
    base["mae_r"] = round(float(mae), 4)
    base["latest_unrealized_r"] = round(float(latest_r), 4)

    if base["status"] == "OPEN":
        base["r_multiple"] = round(float(latest_r), 4)
        base["reason"] = "Trade still open; mark-to-market R shown."

    entry_candle = future.iloc[0]
    entry_open = _safe_float(entry_candle.get("open")) or entry
    candle_range_pct = abs(float(entry_candle.get("high", entry_open)) - float(entry_candle.get("low", entry_open))) / max(entry_open, 1e-12)
    cost = estimate_execution_cost(
        {"atr_pct": candle_range_pct, "cross_exchange_volume_ratio": 1.0},
        fee_bps_per_side=_safe_float(trade.get("fee_bps_per_side")) or DEFAULT_FEE_BPS_PER_SIDE,
        base_slippage_bps_per_side=_safe_float(trade.get("base_slippage_bps_per_side")) or DEFAULT_SLIPPAGE_BPS_PER_SIDE,
        dynamic=str(trade.get("dynamic_execution_costs", "true")).lower() in {"true", "1", "yes"},
    )
    risk_pct = risk_abs / entry * 100.0
    cost_r = cost.round_trip_cost_pct / max(risk_pct, 1e-12)
    gross_r = float(base["r_multiple"])
    net_r = gross_r - cost_r if side in {"LONG", "SHORT"} else gross_r
    base["gross_r_multiple"] = round(gross_r, 4)
    base["net_r_multiple"] = round(net_r, 4)
    base["r_multiple"] = round(net_r, 4)
    base["round_trip_cost_pct"] = cost.round_trip_cost_pct
    base["cost_r"] = round(cost_r, 4)
    base["effective_slippage_bps_per_side"] = cost.slippage_bps_per_side

    return base


def evaluate_paper_trades(fetcher, limit: int = 500) -> PaperEvaluationSummary:
    trades = _load_csv(PAPER_TRADES_FILE)
    if trades.empty:
        PAPER_DIR.mkdir(parents=True, exist_ok=True)
        report_path = PAPER_DIR / f"paper_evaluation_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
        report_path.write_text("# Paper Trading Evaluation\n\nNo paper trades found.\n", encoding="utf-8")
        return PaperEvaluationSummary(report_path=str(report_path))

    rows = []
    for _, trade in trades.iterrows():
        symbol = str(trade.get("symbol", ""))
        timeframe = str(trade.get("timeframe", "4h") or "4h")
        try:
            raw = fetcher(symbol=symbol, timeframe=timeframe, limit=limit)
            market = _normalize_market_df(raw)
            if market.empty:
                row = {
                    "paper_trade_id": trade.get("paper_trade_id", ""),
                    "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
                    "entry_time": trade.get("entry_time", ""),
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "side": trade.get("side", ""),
                    "entry": _safe_float(trade.get("entry")),
                    "stop": _safe_float(trade.get("stop")),
                    "target_1": _safe_float(trade.get("target_1")),
                    "status": "PENDING",
                    "result": "PENDING",
                    "available_future_candles": 0,
                    "exit_time": "",
                    "exit_price": None,
                    "r_multiple": 0.0,
                    "mfe_r": 0.0,
                    "mae_r": 0.0,
                    "latest_unrealized_r": 0.0,
                    "reason": "Market data unavailable.",
                }
            else:
                row = _evaluate_one_trade(trade.to_dict(), market)
        except Exception as error:
            row = {
                "paper_trade_id": trade.get("paper_trade_id", ""),
                "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
                "entry_time": trade.get("entry_time", ""),
                "symbol": symbol,
                "timeframe": timeframe,
                "side": trade.get("side", ""),
                "entry": _safe_float(trade.get("entry")),
                "stop": _safe_float(trade.get("stop")),
                "target_1": _safe_float(trade.get("target_1")),
                "status": "ERROR",
                "result": "ERROR",
                "available_future_candles": 0,
                "exit_time": "",
                "exit_price": None,
                "r_multiple": 0.0,
                "mfe_r": 0.0,
                "mae_r": 0.0,
                "latest_unrealized_r": 0.0,
                "reason": f"{type(error).__name__}: {error}",
            }
        rows.append(row)

    PAPER_EVALUATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp = PAPER_EVALUATIONS_FILE.with_suffix(PAPER_EVALUATIONS_FILE.suffix + ".tmp")
    pd.DataFrame(rows).to_csv(temp, index=False, encoding="utf-8-sig")
    temp.replace(PAPER_EVALUATIONS_FILE)

    summary = summarize_paper_evaluations(pd.DataFrame(rows))
    report = format_paper_evaluation_report(summary, rows)
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    path = PAPER_DIR / f"paper_evaluation_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(report, encoding="utf-8")
    summary.report_path = str(path)
    return summary


def summarize_paper_evaluations(evals: Optional[pd.DataFrame] = None) -> PaperEvaluationSummary:
    if evals is None:
        evals = _load_csv(PAPER_EVALUATIONS_FILE)
    trades = _load_csv(PAPER_TRADES_FILE)
    if evals is None or evals.empty:
        return PaperEvaluationSummary(total_trades=0 if trades.empty else len(trades))

    complete = evals[evals["status"].astype(str) == "CLOSED"].copy()
    open_rows = evals[evals["status"].astype(str) == "OPEN"]
    win_rows = complete[complete["result"].astype(str) == "WIN"]
    loss_rows = complete[complete["result"].astype(str) == "LOSS"]
    r_values = pd.to_numeric(complete.get("r_multiple", pd.Series(dtype=float)), errors="coerce").dropna()

    complete_count = len(complete)
    win_rate = (len(win_rows) / complete_count * 100) if complete_count else 0.0
    avg_r = float(r_values.mean()) if not r_values.empty else 0.0
    best_r = float(r_values.max()) if not r_values.empty else 0.0
    worst_r = float(r_values.min()) if not r_values.empty else 0.0

    return PaperEvaluationSummary(
        total_trades=0 if trades.empty else len(trades),
        evaluated_rows=len(evals),
        complete_rows=complete_count,
        open_rows=len(open_rows),
        win_rows=len(win_rows),
        loss_rows=len(loss_rows),
        avg_r=round(avg_r, 4),
        expectancy_r=round(avg_r, 4),
        win_rate=round(win_rate, 2),
        best_r=round(best_r, 4),
        worst_r=round(worst_r, 4),
    )


def format_paper_record_result(result: PaperRecordResult) -> str:
    lines = []
    lines.append("=" * 110)
    lines.append("🧪 Freakto Paper Trading Recorder v4.7.1")
    lines.append("=" * 110)
    lines.append(f"Attempted candidates : {result.attempted}")
    lines.append(f"Recorded trades      : {result.recorded}")
    lines.append(f"Skipped candidates   : {result.skipped}")
    lines.append(f"Duplicate trades     : {result.duplicates}")
    lines.append(f"Preflight status     : {result.preflight_status}")
    if result.blockers:
        lines.append("Blockers:")
        lines.extend(f"- {item}" for item in result.blockers)
    if result.rows:
        lines.append("")
        lines.append("Recorded:")
        for row in result.rows[:10]:
            lines.append(
                f"- {row['symbol']} {row['side']} | Entry {fmt_price(row['entry'])} | "
                f"Stop {fmt_price(row['stop'])} | T1 {fmt_price(row['target_1'])} | "
                f"RR {row['first_rr']} | Rec {row['recommendation']}"
            )
    if result.skipped_reasons:
        lines.append("")
        lines.append("Skipped examples:")
        for reason in result.skipped_reasons[:8]:
            lines.append(f"- {reason}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_paper_evaluation_summary(summary: PaperEvaluationSummary) -> str:
    lines = []
    lines.append("=" * 110)
    lines.append("📊 Freakto Paper Trade Evaluator v4.7.1")
    lines.append("=" * 110)
    lines.append(f"Total paper trades : {summary.total_trades}")
    lines.append(f"Evaluated rows     : {summary.evaluated_rows}")
    lines.append(f"Closed trades      : {summary.complete_rows}")
    lines.append(f"Open trades        : {summary.open_rows}")
    lines.append(f"Wins / Losses      : {summary.win_rows} / {summary.loss_rows}")
    lines.append(f"Paper Trade Win   : {summary.win_rate:.2f}%")
    lines.append(f"Expectancy         : {summary.expectancy_r:.3f}R")
    lines.append(f"Best / Worst       : {summary.best_r:.3f}R / {summary.worst_r:.3f}R")
    if summary.report_path:
        lines.append(f"Report saved       : {summary.report_path}")
    lines.append("=" * 110)
    return "\n".join(lines)


def format_paper_evaluation_report(summary: PaperEvaluationSummary, rows: List[dict]) -> str:
    lines = []
    lines.append("# Freakto Paper Trade Evaluation v4.7.1")
    lines.append("")
    lines.append(f"Created UTC: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total paper trades: {summary.total_trades}")
    lines.append(f"- Closed trades: {summary.complete_rows}")
    lines.append(f"- Open trades: {summary.open_rows}")
    lines.append(f"- Paper Trade Win Rate: {summary.win_rate:.2f}%")
    lines.append(f"- Expectancy: {summary.expectancy_r:.3f}R")
    lines.append(f"- Best/Worst: {summary.best_r:.3f}R / {summary.worst_r:.3f}R")
    lines.append("")
    lines.append("## Recent Rows")
    for row in rows[-20:]:
        lines.append(
            f"- {row.get('symbol')} {row.get('side')} | {row.get('status')}/{row.get('result')} | "
            f"R={row.get('r_multiple')} | MFE={row.get('mfe_r')} | MAE={row.get('mae_r')} | {row.get('reason')}"
        )
    return "\n".join(lines)
