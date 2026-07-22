# GitHub Cloud State Production Persistence Fix

## Root cause

The workflow packed `cloud_state.tar.gz` and `cloud_state_manifest.json` and then copied
those files into a temporary Git repository before checking out the existing
`paper-state` branch. On the second and later runs, Git refused checkout because the
untracked files would be overwritten by tracked files from that branch.

## Production-grade fix

The persistence step now:

1. Keeps packed state files outside the temporary Git working tree.
2. Initializes and checks out the latest `paper-state` branch first.
3. Copies state files only after the branch working tree is ready.
4. Exits successfully when there is no state change.
5. Uploads artifacts before attempting state persistence.
6. Retries a rejected/non-fast-forward push up to three times by rebuilding from the
   latest remote branch.
7. Never force-pushes or rewrites branch history.
8. Preserves fail-closed behavior after all retries are exhausted.

## Safety

This patch only changes GitHub state persistence. It does not enable live trading,
real capital, order routing, or strategy promotion.
