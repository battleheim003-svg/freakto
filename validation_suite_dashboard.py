"""Freakto Validation Intelligence Suite CLI v5.0

Runs validation + risk intelligence together:
1) Metric Definitions
2) Edge Validation
3) Regime Performance Matrix
4) Portfolio Memory
5) Confidence Calibration
6) Monte Carlo Risk Lab
7) Forward Test Status
8) Historical Backtest Status
9) Backtest Diagnostics
10) Backtest Gate Simulator
11) Forward Regime Label Injection
12) Regime Shadow Gate Activator
13) Regime-Split Gate Matrix
14) Forward Shadow Coverage & Bull Probe
15) Root Cause Discovery
16) Research Robustness & Intelligence Suite
17) Replay Score Calibration & Feature Attribution
18) Advanced Live Readiness Score
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path

from engine.edge_validation import format_edge_validation_console, run_edge_validation, save_edge_validation
from engine.regime_matrix import format_regime_matrix_console, run_regime_matrix, save_regime_matrix
from engine.metric_definitions import format_metric_definitions_console, save_metric_definitions_report
from engine.portfolio_memory import build_portfolio_memory, format_portfolio_memory_console, save_portfolio_memory
from engine.confidence_calibration import run_confidence_calibration, format_confidence_calibration_console, save_confidence_calibration
from engine.monte_carlo import run_monte_carlo, format_monte_carlo_console, save_monte_carlo
from engine.live_readiness_score import (
    assess_advanced_live_readiness,
    format_advanced_readiness_console,
    save_advanced_readiness,
)
from engine.forward_test import build_forward_progress, format_forward_progress_console, save_forward_progress
from engine.historical_backtest import load_all_backtest_summary, format_summary_console as format_backtest_summary_console
from engine.backtest_diagnostics import run_backtest_diagnostics, format_diagnostics_console as format_backtest_diagnostics_console, save_backtest_diagnostics
from engine.backtest_gate_simulator import run_gate_simulation, format_gate_simulation_console, save_gate_simulation
from engine.shadow_gates import run_shadow_gate_validation, format_shadow_gate_console, save_shadow_gate_validation
from engine.research_upgrade_suite import run_full_research_suite, format_full_suite_console, save_full_suite
from engine.regime_gate_matrix import run_regime_gate_matrix, format_regime_gate_matrix_console, save_regime_gate_matrix
from engine.forward_regime_labeling import run_forward_regime_labeling, format_forward_regime_label_console, save_forward_regime_labeling
from engine.forward_shadow_coverage import run_forward_shadow_coverage, format_forward_shadow_coverage_console, save_forward_shadow_coverage
from engine.root_cause_discovery import run_root_cause_discovery, format_root_cause_console, save_root_cause_report
from engine.root_cause_forward_validation import run_root_cause_forward_validation, format_root_cause_forward_console, save_root_cause_forward_report
from engine.root_cause_sample_tracker import run_root_cause_sample_tracker, format_root_cause_sample_console, save_root_cause_sample_report
from engine.evidence_graph import run_evidence_graph, format_evidence_graph_console, save_evidence_graph_report
from engine.market_replay import load_market_replay_status, format_market_replay_console
from engine.replay_score_calibration import (
    run_replay_score_calibration,
    format_replay_score_calibration_console,
    save_replay_score_calibration,
)
from telegram_notifier import send_telegram_message

SUITE_DIR = Path("logs") / "validation_suite"


def _save_combined_report(text: str) -> Path:
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    path = SUITE_DIR / f"validation_suite_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(text, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send combined validation suite report to Telegram.")
    parser.add_argument("--iterations", type=int, default=2000)
    parser.add_argument("--trades", type=int, default=100)
    args = parser.parse_args()

    edge = run_edge_validation()
    regime = run_regime_matrix()
    memory = build_portfolio_memory()
    calibration = run_confidence_calibration()
    monte = run_monte_carlo(iterations=args.iterations, trades_per_run=args.trades)
    forward_progress = build_forward_progress()
    backtest_summary = load_all_backtest_summary()
    backtest_diag = run_backtest_diagnostics()
    gate_sim = run_gate_simulation()
    forward_regime_labeling = run_forward_regime_labeling(apply_changes=False)
    shadow_gates = run_shadow_gate_validation()
    regime_gate_matrix = run_regime_gate_matrix()
    forward_shadow_coverage = run_forward_shadow_coverage()
    root_cause = run_root_cause_discovery()
    root_cause_forward = run_root_cause_forward_validation()
    root_cause_samples = run_root_cause_sample_tracker()
    evidence_graph = run_evidence_graph()
    market_replay = load_market_replay_status()
    replay_score_calibration = run_replay_score_calibration()
    research_suite = run_full_research_suite(save=False)
    readiness = assess_advanced_live_readiness()

    metric_text = format_metric_definitions_console()
    edge_text = format_edge_validation_console(edge)
    regime_text = format_regime_matrix_console(regime)
    memory_text = format_portfolio_memory_console(memory)
    calibration_text = format_confidence_calibration_console(calibration)
    monte_text = format_monte_carlo_console(monte)
    forward_text = format_forward_progress_console(forward_progress)
    backtest_text = format_backtest_summary_console(backtest_summary)
    backtest_diag_text = format_backtest_diagnostics_console(backtest_diag, detail=False)
    gate_sim_text = format_gate_simulation_console(gate_sim, detail=False, top=8)
    forward_regime_label_text = format_forward_regime_label_console(forward_regime_labeling, compact=True)
    shadow_gate_text = format_shadow_gate_console(shadow_gates, detail=False, top=8)
    regime_gate_matrix_text = format_regime_gate_matrix_console(regime_gate_matrix, compact=True)
    forward_shadow_coverage_text = format_forward_shadow_coverage_console(forward_shadow_coverage, compact=True)
    root_cause_text = format_root_cause_console(root_cause, compact=True)
    root_cause_forward_text = format_root_cause_forward_console(root_cause_forward, compact=True)
    root_cause_samples_text = format_root_cause_sample_console(root_cause_samples, compact=True)
    evidence_graph_text = format_evidence_graph_console(evidence_graph, compact=True)
    market_replay_text = format_market_replay_console(market_replay, compact=True)
    replay_score_calibration_text = format_replay_score_calibration_console(replay_score_calibration, compact=True)
    research_suite_text = format_full_suite_console(research_suite)
    readiness_text = format_advanced_readiness_console(readiness)

    combined = "\n\n".join([metric_text, edge_text, regime_text, memory_text, calibration_text, monte_text, forward_text, backtest_text, backtest_diag_text, gate_sim_text, forward_regime_label_text, shadow_gate_text, regime_gate_matrix_text, forward_shadow_coverage_text, root_cause_text, root_cause_forward_text, root_cause_samples_text, evidence_graph_text, market_replay_text, replay_score_calibration_text, research_suite_text, readiness_text])
    print(combined)

    metric_report = save_metric_definitions_report()
    edge_json, edge_report = save_edge_validation(edge)
    regime_csv, regime_report = save_regime_matrix(regime)
    memory_json, memory_report = save_portfolio_memory(memory)
    cal_json, cal_report = save_confidence_calibration(calibration)
    mc_json, mc_report = save_monte_carlo(monte)
    forward_json, forward_report = save_forward_progress(forward_progress)
    backtest_diag_json, backtest_diag_report = save_backtest_diagnostics(backtest_diag)
    gate_sim_json, gate_sim_report, gate_sim_csv = save_gate_simulation(gate_sim)
    frl_json, frl_report = save_forward_regime_labeling(forward_regime_labeling)
    shadow_json, shadow_report, shadow_metrics_csv, shadow_signals_csv = save_shadow_gate_validation(shadow_gates)
    rgm_json, rgm_report, rgm_csv, rgm_side_csv, rgm_avoid_csv, rgm_proposals = save_regime_gate_matrix(regime_gate_matrix)
    fsc_json, fsc_report, fsc_bull_csv, fsc_gate_csv = save_forward_shadow_coverage(forward_shadow_coverage)
    root_cause_json, root_cause_report, root_cause_candidates_csv, root_cause_obs = save_root_cause_report(root_cause)
    root_cause_forward_json, root_cause_forward_report, root_cause_forward_summary_csv, root_cause_forward_rows_csv, root_cause_forward_obs = save_root_cause_forward_report(root_cause_forward)
    root_cause_samples_json, root_cause_samples_report, root_cause_samples_csv, root_cause_samples_obs = save_root_cause_sample_report(root_cause_samples)
    evidence_graph_json, evidence_graph_report, evidence_graph_nodes_csv, evidence_graph_edges_csv, evidence_graph_paths_csv, evidence_graph_obs = save_evidence_graph_report(evidence_graph)
    replay_calibration_paths = save_replay_score_calibration(replay_score_calibration)
    research_suite_json, research_suite_report = save_full_suite(research_suite)
    readiness_json, readiness_report = save_advanced_readiness(readiness)
    combined_path = _save_combined_report(combined)

    print(f"📘 Metric definitions report ذخیره شد: {metric_report}")
    print(f"📐 Edge validation JSON ذخیره شد: {edge_json}")
    print(f"📝 Edge validation report ذخیره شد: {edge_report}")
    print(f"🧬 Regime matrix CSV ذخیره شد: {regime_csv}")
    print(f"📝 Regime matrix report ذخیره شد: {regime_report}")
    print(f"🧠 Portfolio memory JSON ذخیره شد: {memory_json}")
    print(f"📝 Portfolio memory report ذخیره شد: {memory_report}")
    print(f"🎯 Confidence calibration JSON ذخیره شد: {cal_json}")
    print(f"📝 Confidence calibration report ذخیره شد: {cal_report}")
    print(f"🎲 Monte Carlo JSON ذخیره شد: {mc_json}")
    print(f"📝 Monte Carlo report ذخیره شد: {mc_report}")
    print(f"🧭 Forward status JSON ذخیره شد: {forward_json}")
    print(f"📝 Forward status report ذخیره شد: {forward_report}")
    print(f"🧪 Backtest diagnostics JSON ذخیره شد: {backtest_diag_json}")
    print(f"📝 Backtest diagnostics report ذخیره شد: {backtest_diag_report}")
    print(f"🧪 Gate simulator JSON ذخیره شد: {gate_sim_json}")
    print(f"📝 Gate simulator report ذخیره شد: {gate_sim_report}")
    print(f"📊 Gate simulator CSV ذخیره شد: {gate_sim_csv}")
    print(f"🧬 Forward regime labeling JSON ذخیره شد: {frl_json}")
    print(f"📝 Forward regime labeling report ذخیره شد: {frl_report}")
    print(f"🧪 Shadow gate JSON ذخیره شد: {shadow_json}")
    print(f"📝 Shadow gate report ذخیره شد: {shadow_report}")
    print(f"📊 Shadow gate metrics ذخیره شد: {shadow_metrics_csv}")
    print(f"🧾 Shadow gate signals ذخیره شد: {shadow_signals_csv}")
    print(f"🧬 Regime-Gate matrix JSON ذخیره شد: {rgm_json}")
    print(f"📝 Regime-Gate matrix report ذخیره شد: {rgm_report}")
    print(f"📊 Regime-Gate matrix CSV ذخیره شد: {rgm_csv}")
    print(f"📊 Regime-Gate-Side matrix CSV ذخیره شد: {rgm_side_csv}")
    print(f"🚫 Regime Avoid CSV ذخیره شد: {rgm_avoid_csv}")
    print(f"🧾 Regime Shadow proposals ذخیره شد: {rgm_proposals}")
    print(f"🔎 Forward shadow coverage JSON ذخیره شد: {fsc_json}")
    print(f"📝 Forward shadow coverage report ذخیره شد: {fsc_report}")
    print(f"📊 Forward bull probes CSV ذخیره شد: {fsc_bull_csv}")
    print(f"📊 Forward shadow gate coverage CSV ذخیره شد: {fsc_gate_csv}")
    print(f"🧬 Root cause JSON ذخیره شد: {root_cause_json}")
    print(f"📝 Root cause report ذخیره شد: {root_cause_report}")
    print(f"📊 Root cause candidates CSV ذخیره شد: {root_cause_candidates_csv}")
    print(f"🧪 Root cause forward JSON ذخیره شد: {root_cause_forward_json}")
    print(f"📝 Root cause forward report ذخیره شد: {root_cause_forward_report}")
    print(f"📊 Root cause forward summary CSV ذخیره شد: {root_cause_forward_summary_csv}")
    print(f"📄 Root cause forward rows CSV ذخیره شد: {root_cause_forward_rows_csv}")
    print(f"🧫 Root cause samples JSON ذخیره شد: {root_cause_samples_json}")
    print(f"📝 Root cause samples report ذخیره شد: {root_cause_samples_report}")
    print(f"📊 Root cause samples CSV ذخیره شد: {root_cause_samples_csv}")
    print(f"🕸️ Evidence graph JSON ذخیره شد: {evidence_graph_json}")
    print(f"📝 Evidence graph report ذخیره شد: {evidence_graph_report}")
    print(f"📊 Evidence graph nodes CSV ذخیره شد: {evidence_graph_nodes_csv}")
    print(f"📊 Evidence graph edges CSV ذخیره شد: {evidence_graph_edges_csv}")
    print(f"📄 Evidence graph paths CSV ذخیره شد: {evidence_graph_paths_csv}")
    print(f"🧬 Replay score calibration JSON ذخیره شد: {replay_calibration_paths.json_path}")
    print(f"📝 Replay score calibration report ذخیره شد: {replay_calibration_paths.report_path}")
    print(f"🧠 Research suite JSON ذخیره شد: {research_suite_json}")
    print(f"📝 Research suite report ذخیره شد: {research_suite_report}")
    print(f"🚦 Advanced readiness JSON ذخیره شد: {readiness_json}")
    print(f"📝 Advanced readiness report ذخیره شد: {readiness_report}")
    print(f"📦 Combined validation suite report ذخیره شد: {combined_path}")

    if args.send:
        send_telegram_message(combined)


if __name__ == "__main__":
    main()
