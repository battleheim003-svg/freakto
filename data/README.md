# Data policy

This directory is for intentional, reproducible inputs—not mutable runtime
state. Tracked content must belong to one of these categories:

- curated/manual input with provenance;
- small example configuration or schema template;
- frozen research archive with a manifest and stable version contract.

Generated `data/market_replay/` cache is ignored and may be migrated to external
runtime storage. Mutable databases belong under the runtime `history` path and
must not be committed here.
