"""Run explicitly optional operational diagnostics with visible degradation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from scripts.ci_component_runner import run_component
except ModuleNotFoundError:  # Direct `python scripts/...` execution.
    from ci_component_runner import run_component


def profile_commands(profile: str) -> list[tuple[str, list[str]]]:
    python = sys.executable
    common = [
        ("github-actions-health", [python, "-X", "utf8", "scripts/github_actions_health_summary.py"]),
        ("pipeline-health", [python, "-X", "utf8", "pipeline_health_dashboard.py"]),
        ("regime-gate-matrix", [python, "-X", "utf8", "regime_gate_matrix_dashboard.py", "--compact"]),
        ("regime-shadow-gate", [python, "-X", "utf8", "regime_shadow_gate_dashboard.py", "--compact"]),
        ("forward-shadow-coverage", [python, "-X", "utf8", "forward_shadow_coverage_dashboard.py", "--compact"]),
        ("causal-intelligence", [python, "-X", "utf8", "causal_intelligence_dashboard.py", "--compact"]),
        ("market-narrative", [python, "-X", "utf8", "market_narrative_dashboard.py", "--compact"]),
        ("narrative-decision", [python, "-X", "utf8", "narrative_decision_dashboard.py", "--compact"]),
        ("root-cause", [python, "-X", "utf8", "root_cause_dashboard.py", "--compact"]),
        ("root-cause-forward", [python, "-X", "utf8", "root_cause_forward_validation_dashboard.py", "--compact"]),
        ("root-cause-samples", [python, "-X", "utf8", "root_cause_sample_dashboard.py", "--compact"]),
        ("evidence-graph", [python, "-X", "utf8", "evidence_graph_dashboard.py", "--compact"]),
    ]
    if profile == "forward":
        additions = [
            ("forward-regime-label", [python, "-X", "utf8", "forward_regime_label_dashboard.py", "--compact"]),
            ("automatic-events", [python, "-X", "utf8", "automatic_event_collector_dashboard.py", "--compact"]),
        ]
    elif profile == "health":
        additions = [
            ("forward-regime-label", [python, "-X", "utf8", "forward_regime_label_dashboard.py", "--compact", "--dry-run"]),
            ("automatic-events", [python, "-X", "utf8", "automatic_event_collector_dashboard.py", "--compact", "--no-fetch"]),
        ]
    else:
        raise ValueError(f"Unknown advisory profile: {profile}")
    return [*common[:3], *additions, *common[3:]]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run visible optional Freakto diagnostics")
    parser.add_argument("--profile", choices=("forward", "health"), required=True)
    parser.add_argument("--report", default="logs/ci/component-results.json")
    args = parser.parse_args(argv)
    report = Path(args.report)
    for name, command in profile_commands(args.profile):
        run_component(name, "optional", command, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
