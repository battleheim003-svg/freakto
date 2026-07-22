# Phase 8 encoding and documentation

## Text contract

`.gitattributes` now makes LF canonical for source, Markdown, configuration, and
workflow files; Windows launchers use CRLF. Binary, database, compressed,
spreadsheet, image, PDF, and model files are explicitly non-text.

`.editorconfig` mirrors those rules, requires UTF-8, final newlines, trailing
whitespace cleanup, and stable indentation. Existing files are not bulk
renormalized in this phase, avoiding an unreadable repository-wide diff; future
edits and checkouts follow the contract.

`scripts/validate_text_encoding.py` scans canonical repository text with strict
UTF-8 decoding and rejects BOMs, replacement characters, and common
double-decoding/mojibake signatures. Logs, history, virtual environments,
runtime storage, Git internals, and bytecode are excluded. CI runs it as a
required quality gate.

The phase-8 inventory found 587 canonical text files, no UTF-8 BOMs, no invalid
UTF-8, and no mojibake in active source/docs. Earlier garbled terminal output
was PowerShell decoding without `-Encoding utf8`, not corrupt repository text.

## Documentation consolidation

- `docs/README.md` is the canonical documentation index.
- `docs/OPERATIONS.md` is the canonical operator command surface.
- `docs/runbooks/README.md` catalogs deeper compatibility protocols.
- `docs/paper/` remains the focused zero-capital Paper guide.
- `docs/refactor/` records consolidation contracts and verification.
- `docs/archive/` contains historical, non-operational records.

The Paper, Market Replay, and Forward runbooks now point operators to canonical
commands before presenting legacy detail.

## Historical archive

Fifty release notes moved to `docs/archive/releases/`. Twenty-five historical
implementation, validation, fix, and real-result records moved to
`docs/archive/results/`. Content was preserved through Git renames; no history
was deleted. Root Markdown count fell from 130 to 55.

Archived notes are explicitly non-canonical and link back to current operations
documentation. Active runbooks remain at their root compatibility paths so old
links continue to resolve.
