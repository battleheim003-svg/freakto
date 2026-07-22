# Worktree baseline — 2026-07-22

This is the preservation boundary for the consolidation effort. It records the
state that existed before refactoring work began.

## Git baseline

- Branch: `refactor/paper-trading-consolidation`
- HEAD: `3be9b1685eaa45c11a756b871395e7e921e7abd7`
- HEAD subject: `fix: separate handled provider failures from runtime crashes`
- The worktree was already dirty. No pre-existing file was stashed, reset,
  staged, committed, deleted, renamed, or rewritten during phase 1.

## Pre-existing user-owned source work

These files form one development change-set and must be preserved together:

- `live_paper_web_dashboard.py`
  - Retro/cyberpunk dashboard redesign.
  - English/Persian UI dictionary and light-mode support.
  - Latest paper execution board and revised dashboard presentation.
- `tests/test_live_paper_web_dashboard_source.py`
  - Source-level assertions for the branding, bilingual controls, animations,
    execution board, and palette introduced by the dashboard change.

Baseline diff size for this change-set: 260 additions and 68 deletions in the
dashboard plus 12 additions and 1 deletion in its source test (as reported by
`git diff --numstat`).

Preservation rule: future phases may modify these files only intentionally and
must retain or supersede their behavior with tests. They are not generated
artifacts.

## Pre-existing mutable runtime state

These tracked files were modified by the running Shadow workflow, not treated
as source edits:

- `logs/live_demo_shadow/intents.csv`
- `logs/live_demo_shadow/runtime_state.json`
- `logs/live_demo_shadow/shadow_process.json`

At inspection time, `shadow_process.json` identified PID `12136`, start time
`2026-07-22T13:04:56.903940+00:00`, group `core`, and a 300-second interval.
The persisted state said it had not been stopped, but Windows no longer had a
process with PID `12136`. The process record was therefore stale. Phase 1 did
not stop, restart, clean up, or otherwise interfere with the worker state.

Preservation rule: these are operational observations. Do not normalize them,
use them as code-review input, or overwrite them during refactors. Their final
storage policy belongs to phase 6.

## Pre-existing untracked generated evidence

Ten untracked JSON files existed under `logs/live_demo_shadow/evidence/`:

- `0e34e409dea472b67307.json`
- `2b41db34b06c80323144.json`
- `4357f6d68ffa2b9d5609.json`
- `6002fb554a5d1f055ae4.json`
- `988b72c12e4ad09200fc.json`
- `98d5c8dbfd326861f697.json`
- `ad7bc4a7fd6dc6533c55.json`
- `b1fbfca47b046a95f82d.json`
- `e8f3f3523505c5109662.json`
- `ee010dfbf3e6bbe3c760.json`

These files remain untouched. Evidence generated after this baseline may add to
the directory while Shadow is running, so the initial list—not a later `status`
snapshot—is the preservation reference.

## Pre-existing untracked local assets

- `cc6adaf71871c6009de598596c0a6cc2.jpg` — 159,756 bytes
- `download (1).png` — 1,865,746 bytes

Their intended role was not inferable from the repository. They are classified
as user-owned local inputs: do not delete, rename, ignore globally, or commit
them without an explicit decision.

## Verification baseline

Test command:

```text
python -m pytest -q tests/test_live_paper_web_dashboard_source.py tests/test_live_paper_dashboard.py tests/test_shadow_process_controller.py
```

Result: 6 passed and 1 failed. The failure was
`test_excel_and_pdf_reports_are_downloadable_files`; Matplotlib selected its Tk
GUI backend and failed while querying the Windows foreground window. The failure
occurred inside PDF report creation and was not caused by the dashboard source
change. This environment/backend issue is recorded for phase 2 tooling rather
than silently changing unrelated code in phase 1.

Earlier focused replay/paper verification in the same worktree completed with
18 passing tests. Full collection discovered 296 tests; the complete suite did
not finish within the initial 60-second observation window.

## Recovery and review procedure

Before changing a pre-existing source file, compare it against the HEAD above
with `git diff`. Runtime files and untracked assets must remain excluded from
source commits. If concurrent Shadow execution changes runtime state, treat the
new state as operational data and do not attempt to restore it to this textual
snapshot.

Phase 1 intentionally creates documentation only. It does not create a stash or
WIP commit because either would mutate or obscure the user's active worktree.
