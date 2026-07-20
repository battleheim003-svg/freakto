# Freakto Shadow / Paper Web Dashboard

The dashboard is a local visibility and reporting layer. It cannot submit real exchange orders. Its only process controls start, stop, or restart the local **Shadow** worker; all trading state remains in the existing, separate Shadow and Paper roots.

## Install and start

```bat
python -m pip install -r requirements.txt
python -X utf8 paper_trading_dashboard.py --web
```

Streamlit prints a local URL, normally `http://localhost:8501`. Keep the dashboard terminal open while using the web page.

## Shadow controls

- **Start** launches `live_paper.py --mode shadow --groups core --loop --interval 300` as a detached worker.
- **Stop** terminates only the validated Shadow PID and preserves all state/log files.
- **Restart** stops and starts the worker without resetting the seven-day clock or observations.
- Closing the browser tab does not stop Shadow. Shutting down the laptop does; press **Start** after the next boot to continue from the same state.
- The single-process runtime lock still prevents a second Shadow worker. If Shadow was already started manually, stop it with `Ctrl+C` before using the dashboard Start button.

Do not delete `logs/live_demo_shadow/runtime_state.json`; it carries the gate history. Starting, stopping, or restarting from the dashboard never deletes it.

## Views and exports

- Shadow gate checks, provider freshness, complete candle count, and crash count
- Decision/fill log
- Virtual equity and drawdown data after Paper fills exist
- Regime/status heatmap
- Symbol-level cash-flow attribution
- Excel workbook and PDF snapshot downloads

Cash-flow attribution is not claimed as realized P&L while positions remain open. The virtual equity curve remains the account-level performance source.

## Failure metrics

- `handled_symbol_failures` counts provider/network failures that were contained to one symbol; these remain visible for reliability analysis but do not fail the zero-crash gate.
- `unhandled_crashes` is reserved for unexpected process-level failures and remains a strict gate blocker.
- On the first runtime start after this change, legacy values are reclassified once because the previous implementation incremented `unhandled_crashes` from inside its handled per-symbol exception block. The migration is recorded in `failure_metric_migration` and does not reset elapsed time, decisions, candles, or provider evidence.
