"""CLI for Freakto score attribution and component ablation research."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from engine.component_ablation import AblationConfig, run_component_ablation
from engine.score_attribution import (
    AttributionConfig,
    DEFAULT_OUTPUT_DIR,
    run_score_attribution,
)


def _format_float(value: object, digits: int = 6) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "---"


def _build_markdown(
    attribution_result,
    attribution_artifacts,
    ablation_result,
    ablation_artifacts,
) -> str:
    lines = [
        "# Freakto Score Attribution & Component Ablation",
        "",
        f"- Status: **{attribution_result.status}**",
        f"- Version: `{attribution_result.version}`",
        f"- Dataset: `{attribution_result.dataset_path}`",
        f"- Selected replay run: `{attribution_result.selected_run_id or 'ALL/UNSPECIFIED'}`",
        f"- Rows usable: **{attribution_result.rows_usable}**",
        f"- Return target: `{attribution_result.return_column}`",
        "- Safety: research-only; no Paper/Live weights or gates were changed.",
        "",
        "## Key findings",
        "",
    ]
    findings = [*attribution_result.key_findings, *ablation_result.key_findings]
    for finding in findings:
        lines.append(f"- {finding}")

    overall_components = attribution_artifacts.component_summary
    overall_components = overall_components[overall_components["scope"].eq("ALL")].copy()
    if not overall_components.empty:
        overall_components = overall_components.sort_values("high_minus_low_return", ascending=False, na_position="last")
        lines.extend(
            [
                "",
                "## Overall component association",
                "",
                "| Component | Spearman vs return | High-minus-low return | Diagnosis |",
                "|---|---:|---:|---|",
            ]
        )
        for _, row in overall_components.iterrows():
            lines.append(
                f"| {row['component_label']} | {_format_float(row['spearman_return'])} | "
                f"{_format_float(row['high_minus_low_return'])} | {row['diagnosis']} |"
            )

    model = attribution_artifacts.model_attribution.copy()
    if not model.empty:
        model = model.sort_values("permutation_mse_increase", ascending=False)
        lines.extend(
            [
                "",
                "## Out-of-sample multivariate attribution",
                "",
                "| Component | Standardized coefficient | Permutation MSE increase | Holdout value |",
                "|---|---:|---:|---|",
            ]
        )
        for _, row in model.iterrows():
            lines.append(
                f"| {row['component_label']} | {_format_float(row['standardized_coefficient'], 8)} | "
                f"{_format_float(row['permutation_mse_increase'], 8)} | {row['holdout_value']} |"
            )

    economics = attribution_artifacts.economics
    economics = economics[economics["scope"].isin(["ALL", "SIDE:LONG", "SIDE:SHORT"])]
    if not economics.empty:
        lines.extend(
            [
                "",
                "## Decision economics",
                "",
                "| Scope | Samples | Win rate | Avg return | Profit factor | Break-even win rate | Actual minus break-even |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for _, row in economics.iterrows():
            lines.append(
                f"| {row['scope']} | {int(row['sample_count'])} | {_format_float(row['win_rate'])} | "
                f"{_format_float(row['avg_return'])} | {_format_float(row['profit_factor'])} | "
                f"{_format_float(row['break_even_win_rate'])} | "
                f"{_format_float(row['actual_minus_break_even_win_rate'])} |"
            )

    ablation = ablation_artifacts.summary
    ablation = ablation[ablation["scope"].eq("ALL")].copy()
    if not ablation.empty:
        ablation = ablation.sort_values("delta_fixed_expectancy_vs_full", ascending=False)
        lines.extend(
            [
                "",
                "## Fixed-gate holdout ablation (score >= 70)",
                "",
                "| Variant | Selected | Expectancy | Profit factor | Delta expectancy vs full | Diagnosis |",
                "|---|---:|---:|---:|---:|---|",
            ]
        )
        for _, row in ablation.iterrows():
            lines.append(
                f"| {row['variant']} | {int(row['fixed_sample_count'])} | "
                f"{_format_float(row['fixed_expectancy'])} | {_format_float(row['fixed_profit_factor'])} | "
                f"{_format_float(row['delta_fixed_expectancy_vs_full'])} | {row['diagnosis']} |"
            )

    lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            "- Association is not causation; correlated components can share the same market information.",
            "- Thresholds were selected on the optimization slice only; Holdout was not used for selection.",
            "- Removing a component from the recorded score is a diagnostic counterfactual, not a claim that the engine has already been safely reweighted.",
            "- Any weight change requires a fresh replay, calibration, segmented validation, and later shadow-mode verification.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze score-component attribution and chronological ablations."
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Replay evaluation CSV. Defaults to logs/market_replay/market_replay_evaluations.csv.",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--run-id", default=None, help="Analyze a specific replay run_id.")
    parser.add_argument(
        "--all-runs",
        action="store_true",
        help="Do not automatically select the latest replay run. Use carefully; overlapping runs may duplicate market history.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir)
    attribution_result, attribution_artifacts, frame = run_score_attribution(
        args.input,
        output_dir=output_dir,
        run_id=args.run_id,
        latest_run_only=not args.all_runs,
        config=AttributionConfig(),
    )

    if attribution_result.status != "COMPLETE":
        print("=" * 108)
        print("Freakto Score Attribution & Component Ablation")
        print("=" * 108)
        print(f"Status                 : {attribution_result.status}")
        for blocker in attribution_result.blockers:
            print(f"- {blocker}")
        return 2

    ablation_result, ablation_artifacts = run_component_ablation(
        frame,
        components=attribution_result.components,
        output_dir=output_dir,
        config=AblationConfig(),
    )
    markdown_path = output_dir / "score_attribution_root_cause_report.md"
    combined_path = output_dir / "score_attribution_combined_report.json"
    markdown_path.write_text(
        _build_markdown(
            attribution_result,
            attribution_artifacts,
            ablation_result,
            ablation_artifacts,
        ),
        encoding="utf-8",
    )
    combined_payload = {
        "attribution": attribution_result.to_dict(),
        "ablation": ablation_result.to_dict(),
        "safety": {
            "research_only": True,
            "paper_live_settings_changed": False,
            "automatic_weight_promotion": False,
        },
    }
    combined_path.write_text(json.dumps(combined_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    overall = attribution_artifacts.economics[
        attribution_artifacts.economics["scope"].eq("ALL")
    ].iloc[0]
    overall_ablation = ablation_artifacts.summary[
        ablation_artifacts.summary["scope"].eq("ALL")
    ]
    improves = overall_ablation[
        overall_ablation["diagnosis"].isin(["REMOVAL_RESTORES_EDGE", "REMOVAL_IMPROVES_BUT_NEGATIVE"])
    ]["component_label"].astype(str).tolist()

    print("=" * 108)
    print("Freakto Score Attribution & Component Ablation")
    print("=" * 108)
    print(f"Status                 : {attribution_result.status}")
    print(f"Selected replay run    : {attribution_result.selected_run_id or 'ALL/UNSPECIFIED'}")
    print(f"Rows loaded/usable     : {attribution_result.rows_loaded} / {attribution_result.rows_usable}")
    print(f"Components analyzed    : {len(attribution_result.components)}")
    print(f"Overall expectancy     : {_format_float(overall['avg_return'])}%")
    print(f"Overall win rate       : {_format_float(float(overall['win_rate']) * 100, 2)}%")
    print(f"Break-even win rate    : {_format_float(float(overall['break_even_win_rate']) * 100, 2)}%")
    print(f"Removal improves       : {', '.join(improves) if improves else 'NONE'}")
    print("Key findings:")
    for finding in [*attribution_result.key_findings, *ablation_result.key_findings]:
        print(f"- {finding}")
    print(f"Report                 : {markdown_path}")
    print(f"Combined JSON          : {combined_path}")
    print("Safety                 : research-only; no score weights or Paper/Live settings were changed.")
    print("=" * 108)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
