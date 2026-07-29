"""Read-only view models for the unified Control Center.

Official Paper, Showcase, Research, Airdrop, and System data remain separate
namespaces.  This module never starts workers or mutates runtime state.
"""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

import pandas as pd

from freakto.research.adapters.governance import (
    FUTURE_WALK_FORWARD_CONTRACT,
    ResearchGovernanceRegistry,
)
from freakto.ui.paper_demo import collect_paper_demo_snapshot


def _read_json(path: Path) -> tuple[dict[str, Any], str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}, None
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"{path.name}: {type(exc).__name__}"
    return (value, None) if isinstance(value, dict) else ({}, f"{path.name}: invalid object")


def _read_csv(path: Path) -> tuple[pd.DataFrame, str | None]:
    if not path.is_file():
        return pd.DataFrame(), None
    try:
        return pd.read_csv(path, low_memory=False), None
    except Exception as exc:
        return pd.DataFrame(), f"{path.name}: {type(exc).__name__}"


def official_paper_view(root: Path) -> dict[str, Any]:
    """Return canonical Paper state without reading Showcase or live-demo roots."""
    root = Path(root).resolve()
    campaign = collect_paper_demo_snapshot(root)
    ledger, ledger_warning = _read_csv(
        root / "logs" / "paper_performance" / "paper_performance_ledger.csv"
    )
    if ledger.empty:
        trades, trades_warning = _read_csv(root / "logs" / "paper_trades.csv")
        evaluations, evaluations_warning = _read_csv(root / "logs" / "paper_trade_evaluations.csv")
        warnings = [item for item in (ledger_warning, trades_warning, evaluations_warning) if item]
        if not trades.empty:
            ledger = trades.copy()
            if not evaluations.empty and "paper_trade_id" in ledger and "paper_trade_id" in evaluations:
                ledger = ledger.merge(
                    evaluations.drop_duplicates("paper_trade_id", keep="last"),
                    on="paper_trade_id",
                    how="left",
                    suffixes=("_trade", "_eval"),
                )
            status = next(
                (ledger[name] for name in ("status_normalized", "status_eval", "status_trade", "status") if name in ledger),
                pd.Series("OPEN", index=ledger.index),
            )
            ledger["closed"] = status.fillna("OPEN").astype(str).str.upper().eq("CLOSED")
    else:
        warnings = [ledger_warning] if ledger_warning else []
    summary, summary_warning = _read_json(
        root / "logs" / "paper_performance" / "paper_performance_summary.json"
    )
    if summary_warning:
        warnings.append(summary_warning)
    readiness, readiness_warning = _read_json(
        root / "logs" / "paper_launch_v2" / "paper_launch_readiness.json"
    )
    if readiness_warning:
        warnings.append(readiness_warning)
    governance_warning = None
    governance: dict[str, Any] = {}
    try:
        record = ResearchGovernanceRegistry().for_selector("v3-global-utc-candidate")
        governance = record.to_dict() if record else {}
    except ValueError as exc:
        governance_warning = str(exc)
    if governance_warning:
        warnings.append(governance_warning)
    if governance and (
        bool(governance.get("terminal"))
        or governance.get("promotion_eligible") is not True
    ):
        readiness = dict(readiness)
        readiness["research_collection_ready"] = False
        readiness["strategy_paper_ready"] = False
        readiness["blockers"] = list(
            dict.fromkeys(
                [
                    *(readiness.get("blockers") or []),
                    str(governance.get("experiment_status") or "PROMOTION_NOT_ELIGIBLE"),
                    str(governance.get("research_outcome") or "PROMOTION_NOT_ELIGIBLE"),
                ]
            )
        )
    closed_mask = (
        ledger.get("closed", pd.Series(False, index=ledger.index)).fillna(False).astype(bool)
        if not ledger.empty
        else pd.Series(dtype=bool)
    )
    open_rows = ledger.loc[~closed_mask].copy() if not ledger.empty else pd.DataFrame()
    closed_rows = ledger.loc[closed_mask].copy() if not ledger.empty else pd.DataFrame()
    return {
        "mode": "official",
        "evidence_eligible": True,
        "campaign": campaign,
        "open_trades": open_rows,
        "closed_trades": closed_rows,
        "performance": summary,
        "readiness": readiness,
        "governance": governance,
        "walk_forward_contract_version": FUTURE_WALK_FORWARD_CONTRACT.version,
        "costs": {
            "basis": "net_r_multiple from canonical Paper evaluations",
            "fees_applied": any(name in ledger.columns for name in ("fee_pct", "fees_usd", "net_r")),
            "slippage_applied": any(name in ledger.columns for name in ("slippage_pct", "slippage_usd", "net_r")),
        },
        "warnings": [*campaign.get("warnings", []), *warnings],
        "source": str(root / "logs" / "paper_performance"),
    }


def showcase_view(root: Path, *, page_size: int = 500) -> dict[str, Any]:
    """Return isolated Showcase data with an explicit evidence prohibition."""
    from freakto.showcase_paper import showcase_dashboard_data

    state, trades = showcase_dashboard_data(Path(root).resolve(), page=1, page_size=page_size)
    open_rows = [row for row in trades if str(row.get("status", "")).upper() == "OPEN"]
    closed_rows = [row for row in trades if str(row.get("status", "")).upper() == "CLOSED"]
    return {
        "mode": "showcase",
        "evidence_eligible": False,
        "evidence_label": "Not official evidence",
        "campaign": state,
        "open_trades": open_rows,
        "closed_trades": closed_rows,
        "performance": dict(state.get("performance") or {}),
        "costs": {
            "basis": "isolated Showcase execution simulation",
            "fees_applied": True,
            "slippage_applied": True,
        },
        "warnings": list(state.get("recent_errors") or []),
        "source": str(Path(root).resolve() / "logs" / "showcase_paper"),
    }


def airdrop_view(root: Path) -> dict[str, Any]:
    """Inspect Airdrop storage without importing or touching Paper modules."""
    root = Path(root).resolve()
    database = root / "history" / "airdrop_outcomes.db"
    counts: dict[str, int] = {}
    warning = None
    if database.is_file():
        try:
            with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as connection:
                tables = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
                ).fetchall()
                for (name,) in tables:
                    if str(name).replace("_", "").isalnum():
                        counts[str(name)] = int(
                            connection.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
                        )
        except sqlite3.Error as exc:
            warning = f"airdrop_outcomes.db: {type(exc).__name__}"
    return {
        "database": str(database),
        "available": database.is_file(),
        "table_counts": counts,
        "warning": warning,
        "paper_state_touched": False,
    }


def research_view(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    return {
        "replay": (root / "data" / "market_replay").is_dir(),
        "forward_reports": len(list((root / "logs" / "forward_testing").glob("*.json"))),
        "fresh_oos": len(list((root / "logs").glob("fresh_oos*"))),
        "evidence": (root / "logs" / "evidence").exists(),
    }


def system_view(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    campaign = collect_paper_demo_snapshot(root)
    return {
        "network": campaign.get("health"),
        "network_skips": campaign.get("network_skipped_cycles", 0),
        "recovery": campaign.get("status"),
        "heartbeat_utc": campaign.get("heartbeat_utc"),
        "warnings": list(campaign.get("warnings") or []),
        "logs": len(list((root / "logs").rglob("*.json"))) if (root / "logs").exists() else 0,
        "live_orders_enabled": False,
        "real_capital_enabled": False,
    }


__all__ = [
    "airdrop_view",
    "official_paper_view",
    "research_view",
    "showcase_view",
    "system_view",
]
