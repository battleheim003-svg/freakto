from __future__ import annotations

import argparse

from engine.evidence_graph import (
    format_evidence_graph_console,
    run_evidence_graph,
    save_evidence_graph_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Freakto v9 Evidence Graph dashboard")
    parser.add_argument("--min-samples", type=int, default=10)
    parser.add_argument("--research-samples", type=int, default=30)
    parser.add_argument("--candidate-samples", type=int, default=90)
    parser.add_argument("--compact", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    report = run_evidence_graph(
        min_samples=args.min_samples,
        research_samples=args.research_samples,
        candidate_samples=args.candidate_samples,
    )
    print(format_evidence_graph_console(report, compact=args.compact))
    if not args.no_save:
        json_path, md_path, nodes_csv, edges_csv, paths_csv, obs = save_evidence_graph_report(report)
        print(f"🕸️ Evidence graph JSON ذخیره شد: {json_path}")
        print(f"📝 Evidence graph report ذخیره شد: {md_path}")
        print(f"📊 Evidence graph nodes CSV ذخیره شد: {nodes_csv}")
        print(f"📊 Evidence graph edges CSV ذخیره شد: {edges_csv}")
        print(f"📄 Evidence graph paths CSV ذخیره شد: {paths_csv}")
        print(f"🧾 Evidence graph observations ledger ذخیره شد: {obs}")


if __name__ == "__main__":
    main()
