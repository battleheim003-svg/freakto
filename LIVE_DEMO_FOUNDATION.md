# Freakto Live Demo Foundation

This module is a public-market-data, long-only spot simulator. It cannot place
real orders and does not accept exchange credentials.

## Install

From the Freakto project root on Windows:

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

CCXT is already pinned in `requirements.txt`; no new dependency is required.

## Safe first run

Fetch one public snapshot and exit:

```bat
python -X utf8 live_demo.py --once
```

Run continuously every 15 seconds:

```bat
python -X utf8 live_demo.py --symbol BTC/USDT --exchange auto --interval 15
```

Stop with `Ctrl+C`. The default `should_execute_trade()` always returns `HOLD`,
so these commands do not create simulated orders until a validated Freakto
decision adapter is added.

`--exchange auto` tries the project's public-provider order: KuCoin, Kraken,
Bybit, then OKX. If a specific primary is supplied (for example `--exchange
okx`), it is tried first and the remaining providers are retained as fallbacks.
When all providers fail, the warning includes each provider's original CCXT
error so DNS, timeout, geo-blocking, and symbol errors can be distinguished.

## Files

- Account state: `logs/live_demo/account_state.json`
- Append-only fills: `logs/live_demo/trades.csv`

`amount` always means base-asset quantity. For `BTC/USDT`, an amount of `0.01`
means `0.01 BTC`, not `0.01 USDT`.

## Integration boundary for the next iteration

Edit or replace `should_execute_trade(market_data, broker)` in `live_demo.py`.
It must return one of:

```python
("BUY", 0.01)
("SELL", 0.01)
("HOLD", 0.0)
```

Do not connect raw research scores directly. The next iteration should add a
small adapter that accepts only time-consistent, readiness-approved Freakto
decisions and assigns position size under an explicit risk policy.
