==============================================================================================================
🔎 Freakto Forward Shadow Coverage & Bull Regime Probe v6.3.1
==============================================================================================================
Status                 : FORWARD_PROMISING_BACKTEST_CONFLICTS_FOUND
Run ID                 : forward_shadow_coverage_20260711_201104
Horizon                : 24h
Decision Rows          : 58
Directional Decisions  : 34
Evaluation Rows        : 57
Complete Evaluations   : 19
Shadow Signals         : 22
Evaluated Shadow       : 19

Forward Regime Coverage:
- TRENDING_BULL: rows=49 | directional=33 | share=84.48% | direct=0 | proxy/text=0
- TRENDING_BEAR: rows=8 | directional=1 | share=13.79% | direct=0 | proxy/text=0
- SIDEWAYS: rows=1 | directional=0 | share=1.72% | direct=0 | proxy/text=0

Shadow Gate Coverage:
- STRUCTURE_SCORE_GE_10: signals=14 | eval=14 | avg=0.8834% | win=100.0% | dominant_regime=TRENDING_BULL
- HISTORICAL_EDGE_SCORE_GE_1: signals=7 | eval=4 | avg=-1.4736% | win=25.0% | dominant_regime=TRENDING_BULL
- RISK_MEDIUM: signals=1 | eval=1 | avg=0.5361% | win=100.0% | dominant_regime=TRENDING_BULL

Bull Regime Probes:
- BULL_STRUCTURE_SCORE_GE_10: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=0 | bt_net=0.0%
- BULL_STRUCTURE_SCORE_GE_10_LONG: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=0 | bt_net=0.0%
- BULL_RISK_MEDIUM: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=1 | fwd_avg=0.5361% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=0 | bt_net=0.0%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%
- BULL_SCORE_GE_80: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%
- BULL_BNB_LONG_SCORE_GE_60: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=0 | bt_net=0.0%

Bear Regime Zero-Signal Diagnostics:
- REGIME_TRENDING_BEAR__RISK_MEDIUM: cause=TRENDING_BEAR_EXISTS_BUT_NO_RISK_MEDIUM | matches=0 | bear_decisions=1
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: cause=TRENDING_BEAR_EXISTS_BUT_NO_RISK_MEDIUM | matches=0 | bear_decisions=1
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: cause=TRENDING_BEAR_EXISTS_BUT_STRUCTURE_LT_10 | matches=0 | bear_decisions=1
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: cause=TRENDING_BEAR_EXISTS_BUT_STRUCTURE_LT_10 | matches=0 | bear_decisions=1

Backtest/Forward Contradictions:
⚠️ BULL_STRUCTURE_SCORE_GE_10: Forward avg=0.8834% با n=14 اما Backtest net=0.0% است.
⚠️ BULL_STRUCTURE_SCORE_GE_10_LONG: Forward avg=0.8834% با n=14 اما Backtest net=0.0% است.
⚠️ BULL_RISK_MEDIUM: Forward avg=0.5361% با n=1 اما Backtest net=0.0% است.

Blockers:
⛔ Shadow evaluated samples کمتر از 30 است: 19

Recommendations:
→ فعال‌ترین Bull probe فعلی: BULL_STRUCTURE_SCORE_GE_10 | forward n=14 | avg=0.8834% | verdict=FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT.
→ Bull probe فقط مشاهده‌ای است؛ تا وقتی Backtest/Forward هر دو robust نشوند، به Shadow Candidate ارتقا نده.
→ برای تصمیم‌گیری بعدی، STRUCTURE_SCORE_GE_10 را جداگانه به تفکیک regime در Forward دنبال کن.

Warnings:
⚠️ این ماژول فقط coverage و probe تحقیقاتی می‌سازد؛ هیچ Paper/Live فعال نمی‌کند.
⚠️ Bull probeها کاندید قطعی نیستند؛ v6.3.1 اگر لازم باشد از Shadow Ledger برای همگام‌سازی ارزیابی‌ها استفاده می‌کند.
⚠️ برچسب‌های legacy/proxy regime برای تحقیق‌اند؛ Forward جدید DIRECT_ENGINE ارزش بیشتری دارد.
==============================================================================================================