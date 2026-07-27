# Immediate learning Paper mode

Learning mode starts virtual spot execution immediately. It uses current public
market prices, simulated fees and slippage, virtual USDT, long-only positions,
stop/target exits, position sizing, daily-loss protection, and an emergency
drawdown circuit breaker. It never loads exchange credentials or sends orders.

```powershell
.\.venv\Scripts\python.exe live_paper.py `
  --mode learning `
  --symbols BTC/USDT,ETH/USDT,SOL/USDT,XRP/USDT `
  --loop `
  --interval 300
```

State, intents, fills, events, and evidence are isolated under
`logs/live_demo_learning/`. Every runtime state and entry result carries:

```text
evidence_scope=LEARNING_ONLY
official_evidence_eligible=false
live_orders_enabled=false
real_capital_enabled=false
```

Unlike official Paper mode, learning mode does not wait for the seven-day
Shadow promotion gate. Data validity, closed-candle checks, signal geometry,
spread, position limits, virtual exposure, daily loss, and drawdown protections
still apply. Those checks improve the quality of the learning sample and do not
delay it by calendar age.

Learning results may be used to diagnose and improve the system, but must never
be copied into the frozen 60-day campaign or used to claim Go-live eligibility.
