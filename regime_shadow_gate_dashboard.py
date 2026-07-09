"""Freakto v6.2.1 - Focused Regime Shadow Gate dashboard.

This is a convenience CLI for operators who want to review only the new v6.1
Regime-Gate Shadow activators without scrolling through every older base gate.
It still uses the same underlying shadow ledger and safety rules.
"""

import argparse
from dataclasses import asdict

from engine.shadow_gates import (
    VERSION,
    ShadowGateReport,
    format_shadow_gate_console,
    run_shadow_gate_validation,
    save_shadow_gate_validation,
)
from telegram_notifier import send_telegram_message

REGIME_FAMILY = "regime_gate_matrix_candidate"


def _focused_report(report: ShadowGateReport) -> ShadowGateReport:
    gate_metrics = [m for m in report.gate_metrics if m.get("family") == REGIME_FAMILY]
    top_gates = [m for m in report.top_gates if m.get("family") == REGIME_FAMILY]
    recent = [r for r in report.recent_signals if str(r.get("gate_name", "")).startswith("REGIME_")]
    evaluated = sum(int(m.get("evaluated_samples", 0) or 0) for m in gate_metrics)
    pending = sum(int(m.get("pending_samples", 0) or 0) for m in gate_metrics)
    confirmed = sum(1 for m in gate_metrics if m.get("verdict") == "SHADOW_CONFIRMED_CANDIDATE")
    building = sum(1 for m in gate_metrics if m.get("verdict") == "SHADOW_BUILDING")
    rejected = sum(1 for m in gate_metrics if m.get("verdict") == "SHADOW_REJECT_NEGATIVE_FORWARD")
    total_signals = sum(int(m.get("total_signals", 0) or 0) for m in gate_metrics)
    blockers = list(report.blockers)
    if total_signals == 0:
        blockers = ["هنوز هیچ Regime Shadow signal در Forward ثبت نشده است."]
    recommendations = [
        "این نمای focused فقط gateهای Regime-Gate Matrix v6.1 را نشان می‌دهد.",
        "برای تأیید هر Regime gate حداقل 30 نمونه Forward کامل لازم است.",
    ] + [r for r in report.recommendations if "Regime" in r or "Forward" in r]
    return ShadowGateReport(
        run_id=report.run_id,
        generated_utc=report.generated_utc,
        status="REGIME_SHADOW_FOCUSED_" + report.status,
        horizon=report.horizon,
        min_samples=report.min_samples,
        decisions=report.decisions,
        directional_decisions=report.directional_decisions,
        shadow_signals=total_signals,
        evaluated_shadow_samples=evaluated,
        pending_shadow_samples=pending,
        gates_tracked=len(gate_metrics),
        confirmed_candidates=confirmed,
        building_candidates=building,
        rejected_candidates=rejected,
        top_gates=top_gates or gate_metrics[:10],
        gate_metrics=gate_metrics,
        recent_signals=recent,
        blockers=blockers,
        recommendations=recommendations,
        warnings=report.warnings,
    )


def build_parser():
    p = argparse.ArgumentParser(description=f"Freakto Focused Regime Shadow Gate Dashboard {VERSION}")
    p.add_argument("--horizon", choices=["4h", "12h", "24h"], default="24h")
    p.add_argument("--min-samples", type=int, default=30)
    p.add_argument("--compact", action="store_true")
    p.add_argument("--no-save", action="store_true")
    p.add_argument("--send", action="store_true")
    return p


def main():
    args = build_parser().parse_args()
    full = run_shadow_gate_validation(horizon=args.horizon, min_samples=args.min_samples)
    focused = _focused_report(full)
    text = format_shadow_gate_console(focused, detail=not args.compact, top=10)
    print(text)
    if not args.no_save:
        # Save the full underlying ledger so no base-gate information is lost.
        json_path, report_path, metrics_csv, signals_csv = save_shadow_gate_validation(full)
        print(f"🧬 Regime shadow view saved via full shadow ledger: {json_path}")
        print(f"📝 Full shadow report ذخیره شد: {report_path}")
        print(f"📊 Full shadow metrics ذخیره شد: {metrics_csv}")
        print(f"🧾 Full shadow signals ذخیره شد: {signals_csv}")
    if args.send:
        send_telegram_message(text)


if __name__ == "__main__":
    main()
