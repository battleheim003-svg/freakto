"""Read-only data and report helpers for the live Shadow/Paper dashboard."""
from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from engine.live_paper_runtime import RuntimeStore, load_runtime_config, shadow_gate_status


@dataclass(frozen=True)
class DashboardData:
    mode: str
    root: Path
    state: dict[str, Any]
    gate: dict[str, Any]
    account: dict[str, Any]
    intents: pd.DataFrame
    fills: pd.DataFrame
    events: pd.DataFrame


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError):
        return pd.DataFrame()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def load_dashboard_data(mode: str, config_path: str | Path = "live_paper_config.json") -> DashboardData:
    mode = mode.lower()
    if mode not in {"shadow", "paper"}:
        raise ValueError("mode must be shadow or paper")
    config = load_runtime_config(config_path)
    root = Path(config.state_roots[mode])
    store = RuntimeStore(root)
    gate = shadow_gate_status(RuntimeStore(config.state_roots["shadow"]), config)
    return DashboardData(
        mode=mode,
        root=root,
        state=store.state,
        gate=gate,
        account=_read_json(root / "account_state.json"),
        intents=_read_csv(root / "intents.csv"),
        fills=_read_csv(root / "fills.csv"),
        events=_read_csv(root / "events.csv"),
    )


def equity_curve(data: DashboardData) -> pd.DataFrame:
    if data.fills.empty or not {"timestamp_utc", "equity_usdt"}.issubset(data.fills.columns):
        return pd.DataFrame(columns=["timestamp_utc", "equity_usdt", "drawdown_pct"])
    curve = data.fills[["timestamp_utc", "equity_usdt"]].copy()
    curve["timestamp_utc"] = pd.to_datetime(curve["timestamp_utc"], utc=True, errors="coerce")
    curve["equity_usdt"] = pd.to_numeric(curve["equity_usdt"], errors="coerce")
    curve = curve.dropna().sort_values("timestamp_utc")
    peak = curve["equity_usdt"].cummax()
    curve["drawdown_pct"] = ((curve["equity_usdt"] / peak) - 1.0) * 100.0
    return curve


def regime_heatmap(data: DashboardData) -> pd.DataFrame:
    if data.intents.empty or not {"regime", "status"}.issubset(data.intents.columns):
        return pd.DataFrame()
    return pd.crosstab(data.intents["regime"].fillna("UNKNOWN"), data.intents["status"].fillna("UNKNOWN"))


def performance_attribution(data: DashboardData) -> pd.DataFrame:
    if data.fills.empty or "symbol" not in data.fills.columns:
        return pd.DataFrame(columns=["symbol", "fills", "buy_notional", "sell_notional", "fees", "net_cash_flow"])
    fills = data.fills.copy()
    for column in ("notional_usdt", "fee_usdt"):
        fills[column] = pd.to_numeric(fills.get(column, 0), errors="coerce").fillna(0.0)
    fills["buy_notional"] = fills["notional_usdt"].where(fills["side"].eq("BUY"), 0.0)
    fills["sell_notional"] = fills["notional_usdt"].where(fills["side"].eq("SELL"), 0.0)
    result = fills.groupby("symbol", as_index=False).agg(
        fills=("symbol", "size"), buy_notional=("buy_notional", "sum"),
        sell_notional=("sell_notional", "sum"), fees=("fee_usdt", "sum"),
    )
    result["net_cash_flow"] = result["sell_notional"] - result["buy_notional"] - result["fees"]
    return result.sort_values("net_cash_flow", ascending=False)


def excel_report(data: DashboardData) -> bytes:
    output = io.BytesIO()
    curve = equity_curve(data).copy()
    if not curve.empty:
        curve["timestamp_utc"] = curve["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([{
            "passed": data.gate.get("passed", False),
            "days": data.gate.get("days", 0),
            "provider_freshness_pct": data.gate.get("provider_freshness_pct", 0),
        }]).to_excel(writer, sheet_name="gate_summary", index=False)
        pd.DataFrame([
            {"check": name, "passed": passed}
            for name, passed in data.gate.get("checks", {}).items()
        ]).to_excel(writer, sheet_name="gate_checks", index=False)
        pd.DataFrame([data.state.get("metrics", {})]).to_excel(writer, sheet_name="metrics", index=False)
        data.intents.to_excel(writer, sheet_name="intents", index=False)
        data.fills.to_excel(writer, sheet_name="fills", index=False)
        data.events.to_excel(writer, sheet_name="events", index=False)
        curve.to_excel(writer, sheet_name="equity_curve", index=False)
        performance_attribution(data).to_excel(writer, sheet_name="attribution", index=False)
        regime_heatmap(data).to_excel(writer, sheet_name="regime_heatmap")
    return output.getvalue()


def pdf_report(data: DashboardData) -> bytes:
    output = io.BytesIO()
    curve = equity_curve(data)
    attribution = performance_attribution(data)
    with PdfPages(output) as pdf:
        figure, axis = plt.subplots(figsize=(11.69, 8.27))
        axis.axis("off")
        metrics = data.state.get("metrics", {})
        lines = [
            f"Freakto {data.mode.upper()} report", f"Gate passed: {data.gate.get('passed', False)}",
            f"Elapsed days: {data.gate.get('days', 0)}", f"Provider freshness: {data.gate.get('provider_freshness_pct', 0)}%",
            f"Unique decisions: {metrics.get('unique_decisions', 0)}", f"Complete 4h candles: {metrics.get('complete_4h_candles', 0)}",
            f"Handled symbol failures: {metrics.get('handled_symbol_failures', 0)}",
            f"Unhandled crashes: {metrics.get('unhandled_crashes', 0)}", f"Fills: {len(data.fills)}",
        ]
        axis.text(0.05, 0.95, "\n".join(lines), va="top", fontsize=14, linespacing=1.6)
        pdf.savefig(figure, bbox_inches="tight")
        plt.close(figure)
        if not curve.empty:
            figure, axis = plt.subplots(figsize=(11.69, 8.27))
            axis.plot(curve["timestamp_utc"], curve["equity_usdt"], color="#00a86b")
            axis.set_title("Virtual equity curve")
            axis.set_ylabel("USDT")
            axis.grid(alpha=0.25)
            figure.autofmt_xdate()
            pdf.savefig(figure, bbox_inches="tight")
            plt.close(figure)
        if not attribution.empty:
            figure, axis = plt.subplots(figsize=(11.69, 8.27))
            axis.bar(attribution["symbol"], attribution["net_cash_flow"], color="#4c78a8")
            axis.set_title("Cash-flow attribution by symbol")
            axis.set_ylabel("USDT")
            axis.tick_params(axis="x", rotation=45)
            axis.grid(axis="y", alpha=0.25)
            pdf.savefig(figure, bbox_inches="tight")
            plt.close(figure)
    return output.getvalue()
