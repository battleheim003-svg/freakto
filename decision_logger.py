"""
decision_logger.py

ثبت خروجی‌های Decision Engine در فایل CSV.

هر تصمیم یک decision_id یکتا می‌گیرد تا بعداً بتوانیم همان تصمیم را
در فایل ارزیابی‌ها ردیابی کنیم.
"""

import csv
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

from engine.csv_utils import migrate_csv_header


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "decisions.csv"


def _safe_join(items, limit=20):
    if not items:
        return ""

    cleaned = []
    for item in items[:limit]:
        cleaned.append(str(item).replace("\n", " ").strip())

    return " | ".join(cleaned)


def _component_score(opportunity, name):
    for component in opportunity.components:
        if component.name == name:
            return component.points
    return 0


def _component_max(opportunity, name):
    for component in opportunity.components:
        if component.name == name:
            return component.max_points
    return 0


def _make_decision_id(opportunity, latest_timestamp, price):
    base = "|".join([
        str(latest_timestamp),
        str(opportunity.symbol),
        str(opportunity.timeframe),
        str(opportunity.side),
        str(opportunity.score),
        f"{float(price):.8f}",
    ])

    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def log_decision(opportunity, latest_timestamp, price, provider=None):
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    file_exists = LOG_FILE.exists()

    positive_reasons = []
    risk_warnings = []

    for component in opportunity.components:
        positive_reasons.extend(component.reasons)
        risk_warnings.extend(component.warnings)

    decision_id = _make_decision_id(
        opportunity=opportunity,
        latest_timestamp=latest_timestamp,
        price=price,
    )

    row = {
        "decision_id": decision_id,
        "logged_at_utc": datetime.now(timezone.utc).isoformat(),
        "candle_timestamp": str(latest_timestamp),
        "symbol": opportunity.symbol,
        "timeframe": opportunity.timeframe,
        "price": float(price),
        "side": opportunity.side,
        "score": int(opportunity.score),
        "confidence_label": opportunity.confidence_label,
        "risk_label": opportunity.risk_label,
        "actionability": opportunity.actionability_label,
        "is_actionable": bool(opportunity.is_actionable),
        "entry_zone": opportunity.entry_zone,
        "stop_zone": opportunity.stop_zone,
        "targets": json.dumps(opportunity.targets, ensure_ascii=False),
        "trend_score": _component_score(opportunity, "Trend"),
        "trend_max": _component_max(opportunity, "Trend"),
        "momentum_score": _component_score(opportunity, "Momentum"),
        "momentum_max": _component_max(opportunity, "Momentum"),
        "volume_score": _component_score(opportunity, "Volume"),
        "volume_max": _component_max(opportunity, "Volume"),
        "structure_score": _component_score(opportunity, "Structure"),
        "structure_max": _component_max(opportunity, "Structure"),
        "risk_penalty": _component_score(opportunity, "Risk Penalty"),
        "risk_max": _component_max(opportunity, "Risk Penalty"),
        "regime_label": getattr(opportunity, "raw", {}).get("regime_label", ""),
        "regime_confidence": getattr(opportunity, "raw", {}).get("regime_confidence", ""),
        "regime_adjustment": getattr(opportunity, "raw", {}).get("regime_adjustment", ""),
        "long_score": getattr(opportunity, "raw", {}).get("long_score", ""),
        "short_score": getattr(opportunity, "raw", {}).get("short_score", ""),
        "reasons": _safe_join(positive_reasons),
        "warnings": _safe_join(risk_warnings),
        "provider": provider or "",
    }

    fieldnames = list(row.keys())

    # Older Freakto versions wrote a shorter decisions.csv header. Appending a
    # wider v4.7+ row under that old header creates a mixed-schema CSV that
    # breaks pandas.read_csv during forward-test cycles. Normalize the header
    # before appending so long-running projects remain upgrade-safe.
    if file_exists:
        try:
            migrated = migrate_csv_header(LOG_FILE, fieldnames)
            if migrated:
                print("🛠️ decisions.csv schema migrated to current header.")
        except Exception as error:
            print(f"⚠️ decisions.csv schema migration skipped: {type(error).__name__}: {error}")

    file_exists = LOG_FILE.exists() and LOG_FILE.stat().st_size > 0

    with LOG_FILE.open("a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, extrasaction="ignore")

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)

    print(f"🧾 تصمیم ثبت شد: {LOG_FILE}")
    print(f"🆔 Decision ID: {decision_id}")