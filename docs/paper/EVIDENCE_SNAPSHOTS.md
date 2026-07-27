# Paper evidence snapshots

`freakto paper campaign-snapshot` creates a point-in-time audit package while
the 60-day Paper worker keeps running. It does not alter campaign dates,
thresholds, source evidence, Paper arming, live-order flags, or allocation.

## Contents and safety boundary

The archive uses an explicit allowlist defined in
`freakto/paper/evidence_snapshot.py`:

- frozen campaign state and Go-live policy;
- cycle history, last-cycle, orchestrator-state, and heartbeat records;
- canonical Paper trades and evaluation ledgers;
- JSON, Markdown, ledger, regime, and equity CSV performance outputs.

Missing optional files are recorded in `manifest.json`. Campaign state and the
policy are required; if either is unavailable, no archive is created. `.env`,
credentials, API keys, arbitrary log files, market-data caches, and images are
not discoverable by the snapshot function and cannot enter through directory
scanning.

## Integrity and storage

The ZIP is fully written to a temporary file and then atomically moved into
`.freakto-runtime/campaign-backups/`. Existing names are never overwritten.
`manifest.json` records the size and SHA-256 of the exact bytes stored for every
evidence file. The adjacent `.zip.sha256` file records the checksum of the final
archive.

To verify the archive in PowerShell:

```powershell
Get-FileHash .\.freakto-runtime\campaign-backups\<snapshot>.zip -Algorithm SHA256
Get-Content .\.freakto-runtime\campaign-backups\<snapshot>.zip.sha256
```

The two hashes must match. Keep a copy on separate, access-controlled storage
if workstation-loss recovery is required; copying it off-device is an operator
action and is intentionally not automated by this command.
