# Phase 5 entry-point migration

Phase 5 moves operational implementation out of root dashboard scripts. Root
filenames remain as deliberately small compatibility wrappers, while canonical
CLI and cloud execution use packaged modules with `python -m`.

## Migration manifest

| Legacy root entry | Canonical implementation |
|---|---|
| `market_replay_dashboard.py` | `freakto.research.adapters.market_replay` |
| `forward_test_dashboard.py` | `freakto.research.adapters.forward_status` |
| `freakto_research_suite_dashboard.py` | `freakto.research.adapters.suite_report` |
| `paper_performance_dashboard.py` | `freakto.paper.performance_report` |
| `paper_research_orchestrator.py` | `freakto.paper.orchestrator` |
| `paper_trading_dashboard.py` | `freakto.paper.dashboard` |
| `paper_trade_launch_dashboard.py` | `freakto.paper.trade_launch` |
| `github_cloud_runner.py` | `freakto.paper.cloud_runner` |

Every root wrapper is constrained by an architecture test to at most 15 lines.
Wrappers re-export the established public functions/classes where tests and
external scripts historically imported them.

## Canonical execution

The CLI maps migrated targets to modules and executes:

```text
python -X utf8 -m <canonical.module> ...
```

It no longer executes implementation code through root wrappers. The Paper
orchestrator also invokes packaged trade-launch, performance, and self-maintenance
modules. The scheduled GitHub cloud workflow directly runs
`freakto.paper.cloud_runner`.

## Adapter rule

Research entry implementations still depend on the large retained `engine`
surface and a few root compatibility modules. They are therefore isolated under
`freakto.research.adapters`, not presented as pure domain modules. The pure
command boundary remains `freakto.research.commands`. Tests ensure no engine
import escapes the explicit Paper/Research adapter roots.

## Compatibility and rollback

- Existing `python <legacy-name>.py ...` commands remain valid.
- Existing imports from the Paper orchestrator and cloud runner remain valid
  through re-exports.
- Batch files retain their filenames and CLI contracts.
- A rollback can point a wrapper/CLI mapping back to its legacy filename without
  changing user commands or persisted state.

No mutable logs, databases, Paper state, dashboard web customization, or market
datasets are moved by this phase.
