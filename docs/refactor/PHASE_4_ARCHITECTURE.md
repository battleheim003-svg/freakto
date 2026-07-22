# Phase 4 architecture boundaries

Phase 4 establishes enforceable dependency direction while leaving physical
migration of the many retained root/engine implementations to phase 5.

```text
                 freakto.ui
                 /        \
        freakto.paper   freakto.research
                 \        /
               freakto.providers
                       |
                  freakto.core

freakto.cli = composition root
engine/*    = retained implementation/adapters during migration
```

## Layer ownership

- `freakto.core`: side-effect-free shared contracts and the immutable
  fail-closed safety policy.
- `freakto.providers`: provider-neutral external data protocols and failure
  values; no scoring, orchestration, or UI responsibility.
- `freakto.research`: stable data/replay/report command specifications. It
  resolves work but does not execute subprocesses.
- `freakto.paper`: Paper application service, readiness decisions, arming,
  status, dashboard output, and retained-engine integration.
- `freakto.ui`: presentation boundary. It may consume services; lower layers
  must never import it or Streamlit.
- `freakto.cli`: composition root only. It parses commands, composes services,
  executes retained scripts, and emits output. It has no direct `engine` import.

## Dependency enforcement

`tests/test_architecture_boundaries.py` parses imports with Python AST and fails
when a lower layer imports a higher layer. Core, providers, and the pure
`research.commands` boundary cannot import retained `engine` modules. Packaged
implementations that still require the retained engine live only in explicit
`paper` or `research.adapters` boundaries. No non-UI layer may import Streamlit.

## Safety and replay contracts

`SafetyPolicy` is frozen and rejects any instance that enables live orders,
real capital, or non-zero allocation. It overwrites unsafe parent environment
values before every delegated process. This replaces duplicated Boolean
dictionaries in the CLI with one tested invariant.

Research command resolution is a pure operation: it returns an immutable
command value and performs no I/O. Replay modes and resume identifiers are
mapped exactly as in phase 3, so causal replay flags and child exit codes remain
unchanged.

## Compatibility

Public `engine` lazy exports from phase 2 remain intact. Root dashboards, batch
files, and CLI spellings from phase 3 remain compatible. Phase 4 changes the
dependency ownership behind those interfaces; it deliberately does not bulk
move legacy modules, which is phase 5 work.
