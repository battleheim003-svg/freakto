# Freakto Live Shadow / Paper Launch

This runtime is paper-only. It has no authenticated exchange client and cannot
place a real order.

## GapGPT settings

Put the following names in the existing local `.env` file in the project root:

```env
GAPGPT_API_KEY=your_existing_gapgpt_key
GAPGPT_BASE_URL=https://api.gapgpt.app/v1
GAPGPT_MODEL=the_exact_model_id_from_your_gapgpt_dashboard
ENABLE_NEWS_SENTIMENT=true
ENABLE_CROSS_EXCHANGE_VOLUME=true
ENABLE_ONCHAIN_FEATURES=false
LIVE_DEMO_EXECUTION_ENABLED=false
LIVE_DEMO_MODE=shadow
```

Do not paste the secret into source files. In GitHub, add the same values under
Settings > Secrets and variables > Actions > New repository secret. Model ids
are provider-specific; a display name such as "ChatGPT 4.5 mini" must not be
guessed. Run `python -X utf8 news_sentiment.py` to validate the exact id.

The old `OPENAI_API_KEY` and `OPENAI_MODEL` names remain fallback-compatible.
On GitHub, `GAPGPT_API_KEY` is read from the repository secret of the same name;
if it is not created yet, the existing `OPENAI_API_KEY` remains the compatibility
fallback. Local `.env` values never need to be committed.

## First shadow run

```bat
python -X utf8 live_paper.py --mode shadow --groups core --once
python -X utf8 live_paper.py --mode shadow --gate-status
```

Shadow records decisions and evidence but never changes virtual positions.
Keep it running at closed 4h candle boundaries for at least seven days.

For a persistent laptop Shadow process (five-minute health/exit checks; duplicate
4h decisions are ignored):

```bat
python -X utf8 live_paper.py --mode shadow --groups core --loop --interval 300
```

## Paper activation

Paper activation needs all shadow checks to pass. Then set locally:

```env
LIVE_DEMO_EXECUTION_ENABLED=true
LIVE_DEMO_MODE=paper
```

Run:

```bat
python -X utf8 live_paper.py --mode paper --groups core --once
```

Even with the flag, a failed shadow gate keeps execution blocked. Growth stays
locked until ten closed Core paper trades; Meme stays locked until twenty total
closed paper trades. WIF remains history-blocked while its dataset is partial.

## Hybrid operation

- GitHub Actions: retain `Freakto Paper Cloud Cycle` for 4h research,
  evaluation, state archives, and artifacts.
- Windows laptop: run the near-live Shadow/Paper adapter because GitHub Actions
  is not a persistent low-latency process.
- Never run two laptop instances against the same state directory.

## Optional data APIs

No unvetted repository from the broad GitHub `cryptoapi` topic is required.
CCXT/KuCoin public data and the existing RSS/official-event feeds are enough for
the first Shadow launch. CoinAnalyze, Glassnode, CoinGecko, and FRED remain
optional; absence is recorded as unavailable/neutral and never fabricated.
