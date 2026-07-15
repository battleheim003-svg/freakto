"""Paper performance analytics for Freakto's zero-real-order research ledger."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd


@dataclass(frozen=True)
class PaperPerformanceSummary:
    generated_at_utc: str
    total_signals: int
    evaluated_trades: int
    closed_trades: int
    open_trades: int
    wins: int
    losses: int
    win_rate_pct: float
    profit_factor: float
    expectancy_r: float
    cumulative_r: float
    max_drawdown_r: float
    best_trade_r: float
    worst_trade_r: float
    regime_count: int
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _read_csv(path: str | Path) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return pd.DataFrame()
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(target, encoding=encoding, low_memory=False)
        except Exception:
            continue
    return pd.DataFrame()


def _numeric(series: pd.Series | Iterable[Any], index: Optional[pd.Index] = None) -> pd.Series:
    if isinstance(series, pd.Series):
        return pd.to_numeric(series, errors="coerce")
    return pd.to_numeric(pd.Series(series, index=index), errors="coerce")


def _first_nonempty(frame: pd.DataFrame, columns: Iterable[str], default: str = "UNKNOWN") -> pd.Series:
    result = pd.Series("", index=frame.index, dtype="object")
    for name in columns:
        if name not in frame.columns:
            continue
        values = frame[name].fillna("").astype(str).str.strip()
        result = result.mask(result.eq(""), values)
    return result.mask(result.eq(""), default)


def merge_paper_ledger(trades: pd.DataFrame, evaluations: pd.DataFrame) -> pd.DataFrame:
    trades = trades.copy() if trades is not None else pd.DataFrame()
    evaluations = evaluations.copy() if evaluations is not None else pd.DataFrame()
    if trades.empty and evaluations.empty:
        return pd.DataFrame()
    if "paper_trade_id" not in trades.columns:
        trades["paper_trade_id"] = pd.Series(dtype=str)
    if "paper_trade_id" not in evaluations.columns:
        evaluations["paper_trade_id"] = pd.Series(dtype=str)

    if not evaluations.empty:
        time_key = pd.to_datetime(evaluations.get("evaluated_at_utc"), utc=True, errors="coerce")
        evaluations = evaluations.assign(__evaluated_at=time_key)
        evaluations = evaluations.sort_values("__evaluated_at", kind="stable").drop_duplicates("paper_trade_id", keep="last")
    merged = trades.merge(evaluations, on="paper_trade_id", how="outer", suffixes=("_trade", "_eval"))

    merged["entry_time_normalized"] = pd.to_datetime(
        merged.get("entry_time_eval", merged.get("entry_time_trade", merged.get("entry_time"))),
        utc=True,
        errors="coerce",
    )
    merged["exit_time_normalized"] = pd.to_datetime(merged.get("exit_time"), utc=True, errors="coerce")
    merged["status_normalized"] = _first_nonempty(merged, ("status_eval", "status_trade", "status"), "UNKNOWN").str.upper()
    merged["result_normalized"] = _first_nonempty(merged, ("result",), "OPEN").str.upper()
    r_source = None
    for name in ("net_r_multiple", "r_multiple"):
        if name in merged.columns:
            r_source = merged[name]
            break
    merged["net_r"] = _numeric(r_source if r_source is not None else pd.Series(index=merged.index, dtype=float)).fillna(0.0)
    merged["symbol_normalized"] = _first_nonempty(merged, ("symbol_trade", "symbol_eval", "symbol"), "UNKNOWN")
    merged["side_normalized"] = _first_nonempty(merged, ("side_trade", "side_eval", "side"), "UNKNOWN").str.upper()
    merged["regime_normalized"] = _first_nonempty(
        merged,
        (
            "regime_label",
            "market_mode",
            "primary_event",
            "regime",
            "risk_tone",
        ),
        "UNKNOWN",
    ).str.upper()
    merged["closed"] = merged["status_normalized"].eq("CLOSED")
    return merged


def _profit_factor(values: pd.Series) -> float:
    gains = float(values[values > 0].sum())
    losses = abs(float(values[values < 0].sum()))
    if losses <= 1e-12:
        return float("inf") if gains > 0 else 0.0
    return gains / losses


def build_equity_curve(ledger: pd.DataFrame) -> pd.DataFrame:
    if ledger.empty:
        return pd.DataFrame(columns=["sequence", "paper_trade_id", "entry_time", "exit_time", "symbol", "side", "regime", "net_r", "cumulative_r", "running_peak_r", "drawdown_r"])
    closed = ledger[ledger["closed"]].copy()
    if closed.empty:
        return pd.DataFrame(columns=["sequence", "paper_trade_id", "entry_time", "exit_time", "symbol", "side", "regime", "net_r", "cumulative_r", "running_peak_r", "drawdown_r"])
    closed["__order_time"] = closed["exit_time_normalized"].fillna(closed["entry_time_normalized"])
    closed = closed.sort_values(["__order_time", "paper_trade_id"], kind="stable").reset_index(drop=True)
    closed["sequence"] = range(1, len(closed) + 1)
    closed["cumulative_r"] = closed["net_r"].cumsum()
    closed["running_peak_r"] = closed["cumulative_r"].cummax().clip(lower=0.0)
    closed["drawdown_r"] = closed["cumulative_r"] - closed["running_peak_r"]
    return pd.DataFrame(
        {
            "sequence": closed["sequence"],
            "paper_trade_id": closed["paper_trade_id"],
            "entry_time": closed["entry_time_normalized"].astype(str),
            "exit_time": closed["exit_time_normalized"].astype(str),
            "symbol": closed["symbol_normalized"],
            "side": closed["side_normalized"],
            "regime": closed["regime_normalized"],
            "net_r": closed["net_r"],
            "cumulative_r": closed["cumulative_r"],
            "running_peak_r": closed["running_peak_r"],
            "drawdown_r": closed["drawdown_r"],
        }
    )


def build_regime_performance(ledger: pd.DataFrame) -> pd.DataFrame:
    columns = ["regime", "signals", "closed", "open", "wins", "losses", "win_rate_pct", "profit_factor", "expectancy_r", "cumulative_r", "max_drawdown_r"]
    if ledger.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    for regime, group in ledger.groupby("regime_normalized", dropna=False, sort=True):
        closed = group[group["closed"]].copy()
        values = closed["net_r"]
        wins = int((values > 0).sum())
        losses = int((values < 0).sum())
        curve = build_equity_curve(closed)
        rows.append(
            {
                "regime": str(regime),
                "signals": int(len(group)),
                "closed": int(len(closed)),
                "open": int((~group["closed"]).sum()),
                "wins": wins,
                "losses": losses,
                "win_rate_pct": round(wins / len(closed) * 100.0, 2) if len(closed) else 0.0,
                "profit_factor": round(_profit_factor(values), 6) if len(closed) else 0.0,
                "expectancy_r": round(float(values.mean()), 6) if len(closed) else 0.0,
                "cumulative_r": round(float(values.sum()), 6) if len(closed) else 0.0,
                "max_drawdown_r": round(abs(float(curve["drawdown_r"].min())), 6) if not curve.empty else 0.0,
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(["closed", "signals"], ascending=[False, False], kind="stable")


def summarize_performance(ledger: pd.DataFrame) -> PaperPerformanceSummary:
    now = datetime.now(timezone.utc).isoformat()
    if ledger.empty:
        return PaperPerformanceSummary(now, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, "NO_PAPER_TRADES")
    closed = ledger[ledger["closed"]].copy()
    values = closed["net_r"]
    wins = int((values > 0).sum())
    losses = int((values < 0).sum())
    curve = build_equity_curve(ledger)
    return PaperPerformanceSummary(
        generated_at_utc=now,
        total_signals=int(len(ledger)),
        evaluated_trades=int(ledger["status_normalized"].isin(["CLOSED", "OPEN", "PENDING", "INVALID", "ERROR"]).sum()),
        closed_trades=int(len(closed)),
        open_trades=int((~ledger["closed"]).sum()),
        wins=wins,
        losses=losses,
        win_rate_pct=round(wins / len(closed) * 100.0, 2) if len(closed) else 0.0,
        profit_factor=round(_profit_factor(values), 6) if len(closed) else 0.0,
        expectancy_r=round(float(values.mean()), 6) if len(closed) else 0.0,
        cumulative_r=round(float(values.sum()), 6) if len(closed) else 0.0,
        max_drawdown_r=round(abs(float(curve["drawdown_r"].min())), 6) if not curve.empty else 0.0,
        best_trade_r=round(float(values.max()), 6) if len(closed) else 0.0,
        worst_trade_r=round(float(values.min()), 6) if len(closed) else 0.0,
        regime_count=int(ledger["regime_normalized"].nunique(dropna=True)),
        status="COMPLETE" if len(closed) else "COLLECTING_OPEN_TRADES",
    )


def render_markdown(summary: PaperPerformanceSummary, regimes: pd.DataFrame, equity: pd.DataFrame) -> str:
    pf = "∞" if summary.profit_factor == float("inf") else f"{summary.profit_factor:.3f}"
    lines = [
        "# Freakto Paper Performance Dashboard",
        "",
        f"Generated UTC: {summary.generated_at_utc}",
        "",
        "## Portfolio summary",
        f"- Status: **{summary.status}**",
        f"- Signals: **{summary.total_signals}**",
        f"- Closed / Open: **{summary.closed_trades} / {summary.open_trades}**",
        f"- Wins / Losses: **{summary.wins} / {summary.losses}**",
        f"- Win rate: **{summary.win_rate_pct:.2f}%**",
        f"- Profit factor: **{pf}**",
        f"- Expectancy: **{summary.expectancy_r:.4f}R**",
        f"- Cumulative return: **{summary.cumulative_r:.4f}R**",
        f"- Max drawdown: **{summary.max_drawdown_r:.4f}R**",
        f"- Best / Worst: **{summary.best_trade_r:.4f}R / {summary.worst_trade_r:.4f}R**",
        "",
        "## Regime performance",
        "",
    ]
    if regimes.empty:
        lines.append("No regime rows yet.")
    else:
        lines.append("| Regime | Signals | Closed | Win rate | PF | Expectancy R | Cumulative R | Max DD R |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for row in regimes.itertuples(index=False):
            pf_text = "∞" if row.profit_factor == float("inf") else f"{row.profit_factor:.3f}"
            lines.append(f"| {row.regime} | {row.signals} | {row.closed} | {row.win_rate_pct:.2f}% | {pf_text} | {row.expectancy_r:.4f} | {row.cumulative_r:.4f} | {row.max_drawdown_r:.4f} |")
    lines.extend(["", "## Equity curve", "", f"Closed observations on curve: **{len(equity)}**", "", "This dashboard is research-paper only. It does not enable real orders or capital allocation."])
    return "\n".join(lines)


def write_outputs(
    summary: PaperPerformanceSummary,
    ledger: pd.DataFrame,
    regimes: pd.DataFrame,
    equity: pd.DataFrame,
    output_dir: str | Path,
    *,
    make_plot: bool = True,
) -> Dict[str, str]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": output / "paper_performance_summary.json",
        "markdown": output / "paper_performance_dashboard.md",
        "ledger": output / "paper_performance_ledger.csv",
        "regimes": output / "paper_performance_by_regime.csv",
        "equity_csv": output / "paper_equity_curve.csv",
        "equity_png": output / "paper_equity_curve.png",
    }
    paths["json"].write_text(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    paths["markdown"].write_text(render_markdown(summary, regimes, equity), encoding="utf-8")
    ledger.to_csv(paths["ledger"], index=False, encoding="utf-8-sig")
    regimes.to_csv(paths["regimes"], index=False, encoding="utf-8-sig")
    equity.to_csv(paths["equity_csv"], index=False, encoding="utf-8-sig")
    if make_plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(11, 5.5))
            if equity.empty:
                ax.text(0.5, 0.5, "No closed paper trades yet", ha="center", va="center", transform=ax.transAxes)
            else:
                ax.plot(equity["sequence"], equity["cumulative_r"], marker="o", linewidth=1.5)
                ax.axhline(0.0, linewidth=0.8)
            ax.set_title("Freakto Paper Equity Curve")
            ax.set_xlabel("Closed trade sequence")
            ax.set_ylabel("Cumulative net R")
            ax.grid(True, alpha=0.25)
            fig.tight_layout()
            fig.savefig(paths["equity_png"], dpi=150)
            plt.close(fig)
        except Exception:
            pass
    return {name: str(path) for name, path in paths.items() if path.exists()}


def build_dashboard(
    trades_path: str | Path = "logs/paper_trades.csv",
    evaluations_path: str | Path = "logs/paper_trade_evaluations.csv",
    output_dir: str | Path = "logs/paper_performance",
    *,
    make_plot: bool = True,
) -> tuple[PaperPerformanceSummary, pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, str]]:
    ledger = merge_paper_ledger(_read_csv(trades_path), _read_csv(evaluations_path))
    summary = summarize_performance(ledger)
    regimes = build_regime_performance(ledger)
    equity = build_equity_curve(ledger)
    outputs = write_outputs(summary, ledger, regimes, equity, output_dir, make_plot=make_plot)
    return summary, ledger, regimes, equity, outputs
