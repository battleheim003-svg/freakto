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

Scan the complete structured universe, including the meme sleeve:

```bat
python -X utf8 live_demo.py --groups all --exchange kucoin --interval 60
```

Scan only meme assets:

```bat
python -X utf8 live_demo.py --groups meme --exchange kucoin --interval 60
```

Use an explicit list:

```bat
python -X utf8 live_demo.py --symbols BTC/USDT,ETH/USDT,DOGE/USDT --exchange kucoin --interval 30
```

The interval applies after a complete universe cycle, not after each symbol.
An unavailable symbol is isolated and does not abort the remaining scan.

## Three-year history readiness

Read-only audit of all configured datasets:

```bat
python -X utf8 live_demo_history.py --groups all --status
```

Build or incrementally update the replay-safe 4h archive:

```bat
python -X utf8 live_demo_history.py --groups all --build
```

Newer assets may not have three years of trading history. Listing-boundary
discovery records that honestly; it never fabricates pre-listing candles.

## Sentiment and Freakto integration status

The main Freakto Decision Engine can score `news_sentiment_score` through its
External Context component when `ENABLE_NEWS_SENTIMENT=true`. Fear & Greed is
available as lower-tier causal context and must not create a signal alone.
The foundational `live_demo.py` still defaults to `HOLD`: it does not yet call
the Decision Engine, MTF, root-cause, sentiment, or evidence graph. The next
safe integration is a time-consistent adapter, not a direct raw-score hook.

Stop with `Ctrl+C`. The default `should_execute_trade()` always returns `HOLD`,
so these commands do not create simulated orders until a validated Freakto
decision adapter is added.

`--exchange auto` tries the project's public-provider order: KuCoin, Kraken,
Bybit, then OKX. If a specific primary is supplied (for example `--exchange
okx`), it is tried first and the remaining providers are retained as fallbacks.
When all providers fail, the warning includes each provider's original CCXT
error so DNS, timeout, geo-blocking, and symbol errors can be distinguished.
Provider-specific order-book constraints are normalized by the adapter (for
example, KuCoin uses its supported depth of 20). Large HTML block pages are
reduced to a short `403 Forbidden` regional-access diagnostic.

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
