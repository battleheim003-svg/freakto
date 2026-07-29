from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from engine.baseline_benchmarks import load_multi_cycle_replays, select_longest_replay
from engine.event_opportunity_universe import EventUniverseConfig, build_event_opportunity_universe
from engine.cost_gate_diagnostics import (
    apply_thresholds,
    derive_train_thresholds,
    distribution_summary,
    funnel_table,
)
from engine.cost_aware_label_v2 import EventMetaLabelConfig, chronological_event_split
from engine.artifact_protocols import (
    DEFAULT_ARTIFACT_SELECTOR,
    GLOBAL_UTC_SELECTOR,
    resolve_artifact_route,
    validate_global_replay_manifest,
)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Freakto Cost Gate Diagnostics & Geometry Parser Fix")
    p.add_argument("--replay-root", default="")
    p.add_argument("--output-dir", default="")
    p.add_argument("--artifact-selector", default=DEFAULT_ARTIFACT_SELECTOR)
    p.add_argument("--cutoff", default="2026-07-09T12:00:00Z")
    return p


def main() -> int:
    args = parser().parse_args()
    route = resolve_artifact_route(args.artifact_selector)
    replay_root = Path(args.replay_root) if args.replay_root else route.replay_root
    out = Path(args.output_dir) if args.output_dir else route.cost_root
    if replay_root != route.replay_root or out != route.cost_root:
        raise ValueError(
            "ARTIFACT_SELECTOR_VIOLATION: replay/output roots do not match the selected protocol"
        )
    frames = load_multi_cycle_replays(replay_root)
    upstream_manifest = None
    if route.selector == GLOBAL_UTC_SELECTOR:
        manifest_path = replay_root / "global_utc_replay_manifest.json"
        if not manifest_path.exists() or "FULL" not in frames:
            raise ValueError(
                "GLOBAL_UTC_MANIFEST_VIOLATION: v3 replay manifest or FULL replay is missing"
            )
        upstream_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_global_replay_manifest(upstream_manifest, frames["FULL"])
    out.mkdir(parents=True, exist_ok=True)
    selected_name, selected = select_longest_replay(frames)
    config = EventUniverseConfig(development_cutoff_utc=args.cutoff)
    events, diagnostics = build_event_opportunity_universe(selected, config)
    split_cfg = EventMetaLabelConfig(
        event=config,
        minimum_train_events=1,
        minimum_optimize_events=1,
        minimum_holdout_events=1,
        artifact_selector=args.artifact_selector,
        upstream_split_manifest=upstream_manifest,
    )
    if events.empty:
        report = {"status": "INSUFFICIENT_EVENT_UNIVERSE", "selected_replay_window": selected_name, "event_rows": 0}
        (out / "cost_gate_diagnostics_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report))
        return 0
    split = chronological_event_split(events, split_cfg)
    thresholds = derive_train_thresholds(split.train)
    audited = apply_thresholds(events, thresholds)
    funnel = funnel_table(events)
    train_funnel = funnel_table(audited, "train_derived_cost_gate_pass")
    distributions = distribution_summary(events)
    rejection = events.groupby(["cost_gate_rejection_reason"], dropna=False).size().reset_index(name="rows").sort_values("rows", ascending=False)
    side_family = events.groupby(["side", "primary_event", "cost_gate_rejection_reason"], dropna=False).size().reset_index(name="rows")
    events.to_csv(out / "geometry_audited_events.csv", index=False, encoding="utf-8-sig")
    funnel.to_csv(out / "cost_gate_funnel.csv", index=False, encoding="utf-8-sig")
    train_funnel.to_csv(out / "train_derived_cost_gate_funnel.csv", index=False, encoding="utf-8-sig")
    distributions.to_csv(out / "geometry_distributions.csv", index=False, encoding="utf-8-sig")
    rejection.to_csv(out / "cost_gate_rejection_reasons.csv", index=False, encoding="utf-8-sig")
    side_family.to_csv(out / "cost_gate_rejections_by_side_event.csv", index=False, encoding="utf-8-sig")
    report = {
        "status": "COMPLETE_DIAGNOSTIC_ONLY",
        "selected_replay_window": selected_name,
        "rows_loaded": int(len(selected)),
        "event_rows": int(len(events)),
        "geometry_valid_rows": int(events["geometry_valid"].sum()),
        "fixed_gate_rows": int(events["cost_gate_pass"].sum()),
        "train_derived_gate_rows": int(audited["train_derived_cost_gate_pass"].sum()),
        "train_derived_thresholds": thresholds.to_dict(),
        "schema_mode": diagnostics.schema_mode,
        "promotion_applied": False,
        "paper_live_enabled": False,
        "artifact_selector": args.artifact_selector,
        "split_protocol": route.split_protocol,
        "split_profile": route.split_profile,
    }
    (out / "cost_gate_diagnostics_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = ["# Freakto Cost Gate Diagnostics", "", f"- Status: `{report['status']}`", f"- Window: `{selected_name}`", f"- Events: `{len(events)}`", f"- Valid geometry: `{report['geometry_valid_rows']}`", f"- Fixed gate: `{report['fixed_gate_rows']}`", f"- Train-derived diagnostic gate: `{report['train_derived_gate_rows']}`", "", "No runtime threshold, Paper, or Live setting was changed."]
    (out / "cost_gate_diagnostics_report.md").write_text("\n".join(md), encoding="utf-8")
    print("=" * 112)
    print("Freakto Cost Gate Diagnostics & Geometry Parser Fix")
    print("=" * 112)
    for k in ("status", "selected_replay_window", "rows_loaded", "event_rows", "geometry_valid_rows", "fixed_gate_rows", "train_derived_gate_rows"):
        print(f"{k:28}: {report[k]}")
    print("Train-derived thresholds   : " + json.dumps(thresholds.to_dict(), ensure_ascii=False))
    print(f"Report                     : {out / 'cost_gate_diagnostics_report.md'}")
    print("Safety                     : diagnostic-only; runtime thresholds, Paper and Live are unchanged.")
    print("=" * 112)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
