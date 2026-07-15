# Freakto Cloud Runner Fix

This patch fixes the first GitHub Actions run by:

1. using `python -m pytest` instead of the console-script entrypoint;
2. exporting the repository root through `PYTHONPATH`;
3. validating all required cloud files before tests;
4. adding the missing `paper_research_orchestrator.py` and its tests.

The workflow remains paper-only and keeps real/live trading disabled.
