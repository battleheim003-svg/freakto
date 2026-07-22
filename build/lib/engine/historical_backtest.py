"""
engine/historical_backtest.py

Freakto v5.3 - Historical Backfill & Backtest Engine

هدف:
- بازپخش تصمیم‌های Decision Engine روی کندل‌های تاریخی بدون استفاده از آینده.
- ذخیره خروجی در مسیر جدا از Forward Test تا BACKTEST با FORWARD_TEST قاطی نشود.
- ساخت گزارش آماری اولیه برای سنجش Edge قبل از Paper/Live.

نکته ایمنی:
این ماژول هیچ سفارش واقعی ارسال نمی‌کند و هیچ Paper Trade ثبت نمی‌کند.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from engine.csv_utils import read_csv_dicts_lenient
from engine.experiment_registry import ExperimentRegistry
from engine.model_contract import CURRENT_MODEL_CONTRACT, ModelContract
from engine.research_validation import dataset_fingerprint


LOG_DIR = Path("logs")
BACKTEST_DIR = LOG_DIR / "backtests"
BACKTEST_EVALUATIONS_FILE = LOG_DIR / "historical_backtest_evaluations.csv"
BACKTEST_RUNS_FILE = LOG_DIR / "historical_backtest_runs.csv"

DEFAULT_HORIZONS = {
    "4h": 1,
    "12h": 3,
    "24h": 6,
}

REQUIRED_FEATURE_COLUMNS = [
    "close",
    "sma_10",
    "sma_30",
    "ema_10",
    "rsi_14",
    "macd_diff",
    "atr_pct",
]


@dataclass
class HistoricalBacktestConfig:
    symbols: List[str]
    timeframe: str = "4h"
    limit: int = 800
    min_window: int = 120
    step: int = 6
    min_side_score: int = 50
    max_rows_per_symbol: int = 0
    include_monitor_only: bool = True
    source: str = "BACKTEST"


@dataclass
class HistoricalBacktestRun:
    run_id: str
    started_utc: str
    finished_utc: str = ""
    ok: bool = False
    symbols_requested: int = 0
    symbols_completed: int = 0
    rows_written: int = 0
    errors: List[str] = field(default_factory=list)
    output_csv: str = ""
    output_json: str = ""
    output_report: str = ""


@dataclass
class HistoricalBacktestSummary:
    run_id: str
    status: str
    symbols: int
    rows: int
    actionable_rows: int
    monitor_rows: int
    complete_rows: int
    avg_score: float
    directional_samples: int
    directional_win_rate: float
    target_1_hit_rate: float
    stop_hit_rate: float
    avg_24h_return_pct: float
    best_24h_return_pct: float
    worst_24h_return_pct: float
    by_symbol: List[Dict]
    by_actionability: List[Dict]
    by_regime: List[Dict]
    blockers: List[str]
    warnings: List[str]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id() -> str:
    return "backtest_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def parse_symbols(value: Optional[str], fallback: Sequence[str]) -> List[str]:
    if value is None:
        return [str(item).strip() for item in fallback if str(item).strip()]

    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]

    return [str(item).strip() for item in value if str(item).strip()]


def _safe_float(value, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    try:
        text = str(value).replace(",", "").strip()
        if not text or text.lower() in {"nan", "none", "null", "نامشخص"}:
            return default
        return float(text)
    except Exception:
        return default


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _parse_price_zone(value) -> Optional[float]:
    """Return a usable numeric price from a zone string.

    entry_zone may be "low - high". For backtest entry we use candle close, but
    this helper is useful for stop/targets where strings may contain commas.
    """
    if value is None:
        return None
    text = str(value).replace(",", "").strip()
    if not text or text == "نامشخص":
        return None
    if " - " in text:
        parts = [_safe_float(part) for part in text.split(" - ")]
        parts = [part for part in parts if part is not None]
        if parts:
            return sum(parts) / len(parts)
    return _safe_float(text)


def _parse_target_prices(targets: Iterable) -> List[float]:
    result = []
    for item in targets or []:
        value = _parse_price_zone(item)
        if value is not None:
            result.append(float(value))
    return result


def _provider_of(df: pd.DataFrame) -> str:
    try:
        return str(df.attrs.get("provider") or "")
    except Exception:
        return ""


def _timestamp_at(df: pd.DataFrame, idx: int):
    if "timestamp" in df.columns:
        return df.iloc[idx]["timestamp"]
    return df.index[idx]


def _side_adjusted_return(side: str, entry_price: float, future_price: float) -> Optional[float]:
    if not entry_price or not future_price:
        return None
    change = ((future_price - entry_price) / entry_price) * 100
    if side == "SHORT":
        change *= -1
    return round(change, 4)


def _evaluate_path(
    *,
    full_df: pd.DataFrame,
    signal_idx: int,
    side: str,
    entry_price: float,
    targets: List[float],
    stop_price: Optional[float],
    horizons: Dict[str, int],
) -> Dict:
    max_horizon = max(horizons.values()) if horizons else 0
    future = full_df.iloc[signal_idx + 1 : signal_idx + max_horizon + 1].copy()

    result = {
        "available_future_candles": int(len(full_df) - signal_idx - 1),
        "evaluation_status": "PARTIAL",
        "target_1_hit": None,
        "target_2_hit": None,
        "target_3_hit": None,
        "stop_hit": None,
        "mfe_pct": None,
        "mae_pct": None,
        "evaluated_candles": int(len(future)),
    }

    completed = 0
    for label, offset in horizons.items():
        column_name = f"return_after_{label}_pct"
        if len(full_df) > signal_idx + offset:
            future_close = float(full_df.iloc[signal_idx + offset]["close"])
            result[column_name] = _side_adjusted_return(side, entry_price, future_close)
            completed += 1
        else:
            result[column_name] = None

    if completed == len(horizons):
        result["evaluation_status"] = "COMPLETE"

    if future.empty:
        return result

    highs = future["high"].astype(float)
    lows = future["low"].astype(float)
    target_hits = [False, False, False]
    stop_hit = False

    if side == "LONG":
        for index, target in enumerate(targets[:3]):
            target_hits[index] = bool((highs >= target).any())
        if stop_price is not None:
            stop_hit = bool((lows <= stop_price).any())
        mfe_pct = ((highs.max() - entry_price) / entry_price) * 100
        mae_pct = ((lows.min() - entry_price) / entry_price) * 100

    elif side == "SHORT":
        for index, target in enumerate(targets[:3]):
            target_hits[index] = bool((lows <= target).any())
        if stop_price is not None:
            stop_hit = bool((highs >= stop_price).any())
        mfe_pct = ((entry_price - lows.min()) / entry_price) * 100
        mae_pct = ((entry_price - highs.max()) / entry_price) * 100

    else:
        mfe_pct = ((highs.max() - entry_price) / entry_price) * 100
        mae_pct = ((lows.min() - entry_price) / entry_price) * 100

    result.update({
        "target_1_hit": target_hits[0],
        "target_2_hit": target_hits[1],
        "target_3_hit": target_hits[2],
        "stop_hit": stop_hit,
        "mfe_pct": round(float(mfe_pct), 4),
        "mae_pct": round(float(mae_pct), 4),
    })
    return result


def _component_points(opportunity, name: str) -> int:
    for component in getattr(opportunity, "components", []) or []:
        if component.name == name:
            return int(component.points)
    return 0


def _row_from_opportunity(
    *,
    run_id: str,
    symbol: str,
    timeframe: str,
    provider: str,
    signal_idx: int,
    full_df: pd.DataFrame,
    opportunity,
    horizons: Dict[str, int],
) -> Dict:
    signal_timestamp = _timestamp_at(full_df, signal_idx)
    entry_price = float(full_df.iloc[signal_idx]["close"])
    side = str(opportunity.side)

    path = _evaluate_path(
        full_df=full_df,
        signal_idx=signal_idx,
        side=side,
        entry_price=entry_price,
        targets=_parse_target_prices(opportunity.targets),
        stop_price=_parse_price_zone(opportunity.stop_zone),
        horizons=horizons,
    )

    raw = getattr(opportunity, "raw", {}) or {}

    row = {
        "source": "BACKTEST",
        "run_id": run_id,
        "decision_id": f"{run_id}_{symbol.replace('/', '')}_{signal_idx}",
        "candle_timestamp": str(signal_timestamp),
        "symbol": symbol,
        "timeframe": timeframe,
        "provider": provider,
        "side": side,
        "score": int(opportunity.score),
        "confidence_label": opportunity.confidence_label,
        "risk_label": opportunity.risk_label,
        "actionability": opportunity.actionability_label,
        "is_actionable": bool(opportunity.is_actionable),
        "entry_price": round(entry_price, 8),
        "entry_zone": opportunity.entry_zone,
        "stop_zone": opportunity.stop_zone,
        "targets": json.dumps(opportunity.targets, ensure_ascii=False),
        "regime_label": raw.get("regime_label", ""),
        "regime_confidence": raw.get("regime_confidence", ""),
        "long_score": raw.get("long_score", ""),
        "short_score": raw.get("short_score", ""),
        "trend_score": _component_points(opportunity, "Trend"),
        "momentum_score": _component_points(opportunity, "Momentum"),
        "volume_score": _component_points(opportunity, "Volume"),
        "structure_score": _component_points(opportunity, "Structure"),
        "risk_penalty": _component_points(opportunity, "Risk Penalty"),
        "historical_edge_score": _component_points(opportunity, "Historical Edge"),
    }
    row.update(path)
    return row


def _write_csv(path: Path, rows: List[Dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _append_csv(path: Path, rows: List[Dict]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    fieldnames = list(rows[0].keys())
    with path.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def _read_backtest_rows(path: Path = BACKTEST_EVALUATIONS_FILE) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        _, rows = read_csv_dicts_lenient(path)
        return pd.DataFrame(rows)


def _bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin({"true", "1", "yes", "y"})


def _rate(numerator: int, denominator: int) -> float:
    return round((numerator / denominator * 100), 2) if denominator else 0.0


def _group_table(df: pd.DataFrame, group_col: str) -> List[Dict]:
    if df.empty or group_col not in df.columns:
        return []

    rows = []
    for key, group in df.groupby(group_col, dropna=False):
        complete = group[group.get("evaluation_status", "") == "COMPLETE"]
        directional = complete[complete["side"].isin(["LONG", "SHORT"])] if "side" in complete else pd.DataFrame()
        returns = pd.to_numeric(directional.get("return_after_24h_pct", pd.Series(dtype=float)), errors="coerce").dropna()
        t1 = _bool_series(directional.get("target_1_hit", pd.Series(dtype=str))).sum() if not directional.empty else 0
        stops = _bool_series(directional.get("stop_hit", pd.Series(dtype=str))).sum() if not directional.empty else 0
        rows.append({
            group_col: str(key),
            "rows": int(len(group)),
            "complete": int(len(complete)),
            "directional_samples": int(len(directional)),
            "directional_win_rate": _rate(int((returns > 0).sum()), int(len(returns))),
            "target_1_hit_rate": _rate(int(t1), int(len(directional))),
            "stop_hit_rate": _rate(int(stops), int(len(directional))),
            "avg_24h_return_pct": round(float(returns.mean()), 4) if len(returns) else 0.0,
        })

    return sorted(rows, key=lambda item: item.get("rows", 0), reverse=True)


def summarize_backtest(df: pd.DataFrame, run_id: str = "ALL") -> HistoricalBacktestSummary:
    if df is None or df.empty:
        return HistoricalBacktestSummary(
            run_id=run_id,
            status="NO_BACKTEST_DATA",
            symbols=0,
            rows=0,
            actionable_rows=0,
            monitor_rows=0,
            complete_rows=0,
            avg_score=0.0,
            directional_samples=0,
            directional_win_rate=0.0,
            target_1_hit_rate=0.0,
            stop_hit_rate=0.0,
            avg_24h_return_pct=0.0,
            best_24h_return_pct=0.0,
            worst_24h_return_pct=0.0,
            by_symbol=[],
            by_actionability=[],
            by_regime=[],
            blockers=["هیچ داده Backtest تاریخی وجود ندارد."],
            warnings=[],
        )

    work = df.copy()
    if "score" in work.columns:
        work["score"] = pd.to_numeric(work["score"], errors="coerce")
    if "return_after_24h_pct" in work.columns:
        work["return_after_24h_pct"] = pd.to_numeric(work["return_after_24h_pct"], errors="coerce")

    complete = work[work.get("evaluation_status", "") == "COMPLETE"]
    directional = complete[complete["side"].isin(["LONG", "SHORT"])] if "side" in complete else pd.DataFrame()
    returns = directional.get("return_after_24h_pct", pd.Series(dtype=float)).dropna()
    actionable_mask = work.get("actionability", pd.Series(dtype=str)).isin(["ACTIONABLE", "HIGH_ACTIONABILITY"])
    monitor_mask = work.get("actionability", pd.Series(dtype=str)).isin(["MONITOR_ONLY", "WATCHLIST", "NOT_ACTIONABLE"])
    t1_hits = _bool_series(directional.get("target_1_hit", pd.Series(dtype=str))).sum() if not directional.empty else 0
    stop_hits = _bool_series(directional.get("stop_hit", pd.Series(dtype=str))).sum() if not directional.empty else 0

    warnings = [
        "BACKTEST با FORWARD_TEST یکی نیست؛ خروجی تاریخی فقط برای تحقیق و اعتبارسنجی اولیه است.",
        "برای جلوگیری از اعتماد کاذب، Live/Paper جدی فقط بعد از Forward/Paper کافی مجاز است.",
    ]
    blockers = []
    if len(complete) < 100:
        blockers.append(f"Backtest complete samples کمتر از 100 است: {len(complete)}")
    if len(directional) < 30:
        blockers.append(f"Directional backtest samples کمتر از 30 است: {len(directional)}")
    if len(returns) and float(returns.mean()) <= 0:
        blockers.append("میانگین بازده 24h در Backtest مثبت نیست.")

    status = "BACKTEST_RESEARCH_READY" if not blockers else "BACKTEST_BUILDING"

    return HistoricalBacktestSummary(
        run_id=run_id,
        status=status,
        symbols=int(work.get("symbol", pd.Series(dtype=str)).nunique()) if "symbol" in work else 0,
        rows=int(len(work)),
        actionable_rows=int(actionable_mask.sum()) if len(actionable_mask) else 0,
        monitor_rows=int(monitor_mask.sum()) if len(monitor_mask) else 0,
        complete_rows=int(len(complete)),
        avg_score=round(float(work.get("score", pd.Series(dtype=float)).mean()), 2) if "score" in work and len(work) else 0.0,
        directional_samples=int(len(directional)),
        directional_win_rate=_rate(int((returns > 0).sum()), int(len(returns))),
        target_1_hit_rate=_rate(int(t1_hits), int(len(directional))),
        stop_hit_rate=_rate(int(stop_hits), int(len(directional))),
        avg_24h_return_pct=round(float(returns.mean()), 4) if len(returns) else 0.0,
        best_24h_return_pct=round(float(returns.max()), 4) if len(returns) else 0.0,
        worst_24h_return_pct=round(float(returns.min()), 4) if len(returns) else 0.0,
        by_symbol=_group_table(work, "symbol"),
        by_actionability=_group_table(work, "actionability"),
        by_regime=_group_table(work, "regime_label"),
        blockers=blockers,
        warnings=warnings,
    )


def run_historical_backtest(config: HistoricalBacktestConfig) -> Tuple[HistoricalBacktestRun, HistoricalBacktestSummary, pd.DataFrame]:
    run = HistoricalBacktestRun(
        run_id=make_run_id(),
        started_utc=utc_now_iso(),
        symbols_requested=len(config.symbols),
    )
    registry = ExperimentRegistry()
    legacy_contract = ModelContract(
        feature_set_version=CURRENT_MODEL_CONTRACT.feature_set_version,
        model_version=CURRENT_MODEL_CONTRACT.model_version,
        calibration_version=CURRENT_MODEL_CONTRACT.calibration_version,
        execution_model_version="legacy-same-close-fixed-cost-v1",
        split_protocol_version=CURRENT_MODEL_CONTRACT.split_protocol_version,
    )
    registry.start_run(
        run.run_id, "BACKTEST", hyperparameters=asdict(config), contract=legacy_contract,
        notes="Legacy backtest retained for compatibility; MarketReplay is the paper-readiness authority.",
    )
    all_rows: List[Dict] = []
    # Heavy/external imports stay inside execution path so `--status` works
    # even in CI environments where ccxt/ta are not installed yet.
    from data_fetcher import fetch_ohlcv
    from features import add_features
    from engine.decision import DecisionEngine

    engine = DecisionEngine(
        min_side_score=config.min_side_score,
        allow_learning_overrides=False,
        allow_historical_edge=False,
    )

    for symbol in config.symbols:
        try:
            print("=" * 100)
            print(f"🧪 Historical Backtest: {symbol} {config.timeframe}")
            print("=" * 100)
            raw = fetch_ohlcv(symbol=symbol, timeframe=config.timeframe, limit=config.limit)
            if raw is None or raw.empty:
                message = f"{symbol}: no market data returned"
                print(f"❌ {message}")
                run.errors.append(message)
                continue

            provider = _provider_of(raw)
            featured = add_features(raw).dropna(subset=REQUIRED_FEATURE_COLUMNS).reset_index(drop=True)
            if provider:
                featured.attrs["provider"] = provider

            max_horizon = max(DEFAULT_HORIZONS.values())
            max_signal_index = len(featured) - max_horizon - 1
            if max_signal_index <= config.min_window:
                message = f"{symbol}: insufficient candles after feature drop ({len(featured)})"
                print(f"❌ {message}")
                run.errors.append(message)
                continue

            symbol_rows: List[Dict] = []
            indices = range(config.min_window, max_signal_index + 1, max(1, config.step))
            for signal_idx in indices:
                if config.max_rows_per_symbol and len(symbol_rows) >= config.max_rows_per_symbol:
                    break

                window = featured.iloc[: signal_idx + 1].copy()
                if provider:
                    window.attrs["provider"] = provider

                try:
                    opportunity = engine.analyze(window, symbol=symbol, timeframe=config.timeframe)
                    if not config.include_monitor_only and opportunity.actionability_label == "MONITOR_ONLY":
                        continue
                    symbol_rows.append(_row_from_opportunity(
                        run_id=run.run_id,
                        symbol=symbol,
                        timeframe=config.timeframe,
                        provider=provider,
                        signal_idx=signal_idx,
                        full_df=featured,
                        opportunity=opportunity,
                        horizons=DEFAULT_HORIZONS,
                    ))
                except Exception as error:
                    run.errors.append(f"{symbol} idx={signal_idx}: {type(error).__name__}: {error}")

            print(f"✅ {symbol}: {len(symbol_rows)} ردیف Backtest ساخته شد")
            all_rows.extend(symbol_rows)
            run.symbols_completed += 1

        except Exception as error:
            run.errors.append(f"{symbol}: {type(error).__name__}: {error}")
            print(f"⚠️ {symbol}: {type(error).__name__}: {error}")

    run.finished_utc = utc_now_iso()
    run.rows_written = len(all_rows)
    run.ok = bool(all_rows) and run.symbols_completed > 0

    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)
    output_csv = BACKTEST_DIR / f"historical_backtest_{run.run_id}.csv"
    output_json = BACKTEST_DIR / f"historical_backtest_{run.run_id}.json"
    output_report = BACKTEST_DIR / f"historical_backtest_report_{run.run_id}.md"
    run.output_csv = str(output_csv)
    run.output_json = str(output_json)
    run.output_report = str(output_report)

    run_df = pd.DataFrame(all_rows)
    if all_rows:
        _write_csv(output_csv, all_rows)
        _append_csv(BACKTEST_EVALUATIONS_FILE, all_rows)

    summary = summarize_backtest(run_df, run_id=run.run_id)
    output_json.write_text(
        json.dumps({"run": asdict(run), "summary": asdict(summary)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_report.write_text(format_backtest_report(summary, run), encoding="utf-8")
    _append_csv(BACKTEST_RUNS_FILE, [{
        "run_id": run.run_id,
        "started_utc": run.started_utc,
        "finished_utc": run.finished_utc,
        "ok": run.ok,
        "symbols_requested": run.symbols_requested,
        "symbols_completed": run.symbols_completed,
        "rows_written": run.rows_written,
        "errors": " | ".join(run.errors[:10]),
        "output_csv": run.output_csv,
        "output_report": run.output_report,
    }])

    registry.update_data_provenance(
        run.run_id,
        data_start_utc=str(run_df.get("candle_timestamp", pd.Series(dtype=str)).min() or ""),
        data_end_utc=str(run_df.get("candle_timestamp", pd.Series(dtype=str)).max() or ""),
        data_fingerprint=dataset_fingerprint(run_df, ["decision_id", "candle_timestamp", "symbol", "timeframe"]),
    )
    registry.finish_run(
        run.run_id, "COMPLETED" if run.ok else "FAILED",
        {"summary": asdict(summary), "output_csv": run.output_csv, "output_report": run.output_report},
    )

    print(f"🧾 Backtest CSV ذخیره شد: {output_csv}")
    print(f"📝 Backtest report ذخیره شد: {output_report}")
    return run, summary, run_df


def format_summary_console(summary: HistoricalBacktestSummary) -> str:
    lines = []
    lines.append("=" * 110)
    lines.append("🧪 Freakto Historical Backfill & Backtest v5.3")
    lines.append("=" * 110)
    lines.append(f"Status                 : {summary.status}")
    lines.append(f"Run ID                 : {summary.run_id}")
    lines.append(f"Symbols                : {summary.symbols}")
    lines.append(f"Rows                   : {summary.rows}")
    lines.append(f"Complete Rows          : {summary.complete_rows}")
    lines.append(f"Actionable Rows        : {summary.actionable_rows}")
    lines.append(f"Monitor/Other Rows     : {summary.monitor_rows}")
    lines.append(f"Avg Score              : {summary.avg_score}")
    lines.append(f"Directional Samples    : {summary.directional_samples}")
    lines.append(f"Directional Win Rate   : {summary.directional_win_rate:.2f}%")
    lines.append(f"Target 1 Hit Rate      : {summary.target_1_hit_rate:.2f}%")
    lines.append(f"Stop Hit Rate          : {summary.stop_hit_rate:.2f}%")
    lines.append(f"Avg 24h Return         : {summary.avg_24h_return_pct:.4f}%")
    lines.append(f"Best / Worst 24h       : {summary.best_24h_return_pct:.4f}% / {summary.worst_24h_return_pct:.4f}%")

    if summary.by_symbol:
        lines.append("")
        lines.append("By Symbol:")
        for item in summary.by_symbol[:12]:
            lines.append(
                f"- {item.get('symbol')}: rows={item.get('rows')} | complete={item.get('complete')} | "
                f"dir={item.get('directional_samples')} | win={item.get('directional_win_rate')}% | "
                f"avg24h={item.get('avg_24h_return_pct')}%"
            )

    if summary.by_actionability:
        lines.append("")
        lines.append("By Actionability:")
        for item in summary.by_actionability[:12]:
            lines.append(
                f"- {item.get('actionability')}: rows={item.get('rows')} | complete={item.get('complete')} | "
                f"win={item.get('directional_win_rate')}% | avg24h={item.get('avg_24h_return_pct')}%"
            )

    if summary.blockers:
        lines.append("")
        lines.append("Research Blockers:")
        for blocker in summary.blockers:
            lines.append(f"⛔ {blocker}")

    if summary.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in summary.warnings:
            lines.append(f"⚠️ {warning}")

    lines.append("=" * 110)
    return "\n".join(lines)


def format_backtest_report(summary: HistoricalBacktestSummary, run: Optional[HistoricalBacktestRun] = None) -> str:
    lines = []
    lines.append(f"# Freakto Historical Backfill & Backtest Report v5.3")
    lines.append("")
    if run:
        lines.append("## Run")
        lines.append(f"- Run ID: `{run.run_id}`")
        lines.append(f"- Started UTC: `{run.started_utc}`")
        lines.append(f"- Finished UTC: `{run.finished_utc}`")
        lines.append(f"- OK: `{run.ok}`")
        lines.append(f"- Symbols: `{run.symbols_completed}/{run.symbols_requested}`")
        lines.append(f"- Rows written: `{run.rows_written}`")
        if run.errors:
            lines.append("- Errors:")
            for error in run.errors[:20]:
                lines.append(f"  - `{error}`")
        lines.append("")

    lines.append("## Summary")
    lines.append(f"- Status: `{summary.status}`")
    lines.append(f"- Rows: `{summary.rows}`")
    lines.append(f"- Complete rows: `{summary.complete_rows}`")
    lines.append(f"- Actionable rows: `{summary.actionable_rows}`")
    lines.append(f"- Directional samples: `{summary.directional_samples}`")
    lines.append(f"- Directional Win Rate: `{summary.directional_win_rate:.2f}%`")
    lines.append(f"- Target 1 Hit Rate: `{summary.target_1_hit_rate:.2f}%`")
    lines.append(f"- Stop Hit Rate: `{summary.stop_hit_rate:.2f}%`")
    lines.append(f"- Avg 24h Return: `{summary.avg_24h_return_pct:.4f}%`")
    lines.append("")

    lines.append("## By Symbol")
    if summary.by_symbol:
        lines.append("| Symbol | Rows | Complete | Dir Samples | Dir Win | T1 Hit | Stop | Avg 24h |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for item in summary.by_symbol:
            lines.append(
                f"| {item.get('symbol')} | {item.get('rows')} | {item.get('complete')} | "
                f"{item.get('directional_samples')} | {item.get('directional_win_rate')}% | "
                f"{item.get('target_1_hit_rate')}% | {item.get('stop_hit_rate')}% | "
                f"{item.get('avg_24h_return_pct')}% |"
            )
    else:
        lines.append("No symbol data.")
    lines.append("")

    lines.append("## By Actionability")
    if summary.by_actionability:
        lines.append("| Actionability | Rows | Complete | Dir Samples | Dir Win | T1 Hit | Stop | Avg 24h |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for item in summary.by_actionability:
            lines.append(
                f"| {item.get('actionability')} | {item.get('rows')} | {item.get('complete')} | "
                f"{item.get('directional_samples')} | {item.get('directional_win_rate')}% | "
                f"{item.get('target_1_hit_rate')}% | {item.get('stop_hit_rate')}% | "
                f"{item.get('avg_24h_return_pct')}% |"
            )
    else:
        lines.append("No actionability data.")
    lines.append("")

    lines.append("## Blockers")
    if summary.blockers:
        for blocker in summary.blockers:
            lines.append(f"- {blocker}")
    else:
        lines.append("- No backtest research blockers detected.")
    lines.append("")

    lines.append("## Safety Notes")
    for warning in summary.warnings:
        lines.append(f"- {warning}")
    return "\n".join(lines)


def load_all_backtest_summary() -> HistoricalBacktestSummary:
    df = _read_backtest_rows()
    return summarize_backtest(df, run_id="ALL_BACKTESTS")
