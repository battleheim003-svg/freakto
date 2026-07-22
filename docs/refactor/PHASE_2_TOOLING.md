# Phase 2 tooling contract

Phase 2 establishes a standard development surface without forcing a rewrite of
the legacy research modules.

## Canonical files

- `pyproject.toml`: package metadata, build backend, console entry point, Pytest,
  Ruff, and Mypy configuration.
- `requirements.txt`: pinned runtime dependencies.
- `requirements-dev.txt`: pinned test, lint, type-check, and build tooling; it
  includes the runtime requirements for a complete developer environment.
- `tests/conftest.py`: test-only headless rendering and domain marker routing.

The old `pytest.ini` was removed so Pytest has exactly one configuration source.

## Supported commands

```text
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
python -m pytest -q
python -m pytest -m paper -q
python -m pytest -m replay -q
python -m pytest -m "not slow" -q
python -m ruff check engine/__init__.py engine/common.py engine/model_contract.py engine/market_data_contract.py freakto/__init__.py tests/conftest.py
python -m mypy
```

Lint and type-check scopes are intentionally narrow. New or consolidated code
should enter these scopes as it becomes structurally independent; legacy code
must not be hidden behind repository-wide ignores merely to claim a clean run.

## Test isolation

Tests default `MPLBACKEND` to `Agg`. This fixes PDF generation on Windows and
headless CI while leaving production/backend selection untouched. Domain
markers currently classify paper/shadow/live-demo, replay, and the measured
slow benchmark/calibration modules. Other registered markers can be applied as
test boundaries are made explicit in later phases.

## Package compatibility

The editable package exports the `freakto` console script. `engine` retains its
public `DecisionEngine`, `OpportunityV2`, and formatting exports through lazy
loading; importing an unrelated `engine.*` module no longer initializes the
entire legacy decision graph.

## Verification on 2026-07-22

- Editable build and installation succeeded locally with existing setuptools
  using `--no-build-isolation` after the external package index became
  unavailable.
- `freakto --help` succeeded on the default Windows console encoding.
- Public lazy engine imports succeeded.
- Pytest collected 296 tests from `pyproject.toml` with strict markers.
- Full suite: **296 passed** in 76.78 seconds.
- Focused dashboard/PDF/process suite: **7 passed**.
- Paper marker: 73 tests selected from the 296-test collection.
- Controlled quality targets passed Python compilation.

Ruff and Mypy could not be downloaded into the local virtual environment after
two attempts because the package-index TLS connection was terminated. Their
versions are pinned and both gates are enabled in CI, where dependency download
is part of the normal runner setup. This is an environment/network verification
limitation, not an omitted project configuration.
