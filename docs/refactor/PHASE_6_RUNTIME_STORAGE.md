# Phase 6 runtime and artifact storage

Phase 6 separates source-controlled inputs from mutable operational state.

## Classification

| Category | Examples | Git policy | Storage policy |
|---|---|---|---|
| Source | Python, workflows, docs | tracked | repository |
| Test fixture | small deterministic test input | tracked | `tests/` |
| Curated input | manual events, examples | tracked with provenance | `data/` |
| Frozen research archive | versioned OHLCV archive + manifest | tracked intentionally | `data/` or external archive |
| Generated cache | replay cache/checkpoints | ignored | runtime root or CI artifact |
| Mutable state | Paper/Shadow state, SQLite history | ignored | runtime root/state branch |
| Generated report | CSV/JSON/Markdown/plots under logs | ignored | runtime root/CI artifact |

`data/README.md` is the admission policy for future tracked datasets. Existing
versioned multi-cycle archives remain tracked; they are not silently discarded
as generated output.

## Runtime root

`freakto.core.runtime.runtime_paths()` resolves mutable storage to:

```text
FREAKTO_RUNTIME_ROOT=<explicit path>
```

or, when unset:

```text
<project>/.freakto-runtime/
```

The resolver exposes `logs`, `history`, `cloud-state`, and `manifests` paths.
Legacy adapters still accepting `logs/...` arguments remain compatible while
phase-specific callers adopt the resolver; Git no longer treats those local
directories as source.

## Git policy

- `/logs/**` and `/history/**` are ignored.
- Only `.gitkeep` placeholders are retained.
- `.freakto-runtime/`, replay cache, checkpoints, locks, temporary files, and
  serialized models are ignored.
- Paper cloud state continues to persist on the dedicated `paper-state` branch
  and as bounded-retention workflow artifacts, not on the source branch.

Removing paths from the Git index does not delete local files. Existing Paper,
Shadow, evidence, report, and database files remain on disk.

## Migration tool

Inventory-only dry run (default):

```text
python scripts/migrate_runtime_state.py
```

Copy local state and write a manifest:

```text
python scripts/migrate_runtime_state.py --apply
```

Move state only after stopping all workers and verifying the copy destination:

```text
python scripts/migrate_runtime_state.py --apply --move
```

Market replay cache is excluded unless `--include-market-cache` is explicit.
The tool refuses destination collisions, refuses unsafe nested destinations,
defaults to copy rather than move, preserves metadata, and writes a JSON
manifest. It never deletes or overwrites an existing destination.

## Phase-6 inventory

The local dry run on 2026-07-22 found:

- runtime logs: 740 files, 433,259,861 bytes;
- mutable history: 3 files, 585,729 bytes;
- local cloud-state directory: absent.

This inventory includes pre-existing user runtime state. Phase 6 did not run
`--apply` or `--move`; separation from the source branch is performed through
Git policy without disrupting the active local runtime layout.

## Verification

Storage resolver, external-root override, inventory, copy preservation,
collision failure, and dry-run manifest behavior are covered by
`tests/test_runtime_storage.py`. Cloud-state tests remain part of the suite.
