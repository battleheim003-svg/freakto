# Phase 9 regression and migration verification

## Verification result

Phase 9 completed on 2026-07-22 with the project still fail-closed for real
capital. The complete CI test partition passed:

- fast/non-slow: 320 passed, 15 deselected;
- slow: 15 passed, 320 deselected;
- Paper/non-slow: 73 passed, 262 deselected;
- Replay/non-slow: 21 passed, 314 deselected.

The fast and slow partitions together cover all 335 collected tests. Paper and
Replay were repeated independently to verify their workflow markers and safety
boundaries.

After adding 14 permanent release-contract tests, the expanded full suite
passed all 349 tests in a final regression run.

## Clean-install contract

`pip install --no-deps --no-build-isolation --target <clean-target> .` built and
installed the wheel successfully. From a temporary working directory outside
the repository, the installed package passed all of these probes:

- `import freakto` and public version `10.3.0`;
- import of the canonical CLI composition root;
- `python -m freakto.cli --version`;
- help discovery for Data, Replay, Paper, and Report command groups.

The first probe exposed a missing public `freakto.__version__`; this was fixed
and locked by a regression test. Dependencies were deliberately not downloaded
during the probe: the existing verified environment supplied runtime third-party
packages, while Freakto itself was loaded only from the clean target.

## Migration parity

Every retained root compatibility entry point now has an executable regression
assertion that its `main` object is the canonical packaged implementation. This
is stronger than comparing a single formatted sample: legacy and canonical
paths execute the same callable, preventing behavioral drift while wrappers are
retained.

The three supported Windows launchers are checked for repository-relative
startup, the local virtual-environment interpreter, canonical CLI invocation,
exit-code propagation, and explicit Paper-only safety variables where a command
can mutate state.

## Workflow and repository checks

- all six GitHub Actions workflow files parsed as YAML and contained a jobs map;
- 736 canonical text files passed strict UTF-8 validation;
- the release-specific compatibility and launcher assertions pass in pytest.

The workflow YAML parser is a required CI quality gate. Local validation used
PyYAML 6.0.2 from the system toolchain because the project virtual environment
does not currently contain optional development dependencies.

## Compatibility and rollback

Compatibility wrappers remain in place through Phase 10. If a migration issue
is discovered, operators can invoke the same retained root wrapper; because it
imports the canonical callable, no separate implementation or state migration
is involved. The clean-install version export can be rolled back independently
without changing command behavior, but doing so would break the Phase 9 release
contract and its regression test.
