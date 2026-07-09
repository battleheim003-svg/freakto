==============================================================================================================
🔎 Freakto Forward Shadow Coverage & Bull Regime Probe v6.3.1
==============================================================================================================
Status                 : NO_BEAR_COVERAGE_WITH_BULL_PROBE_CONFLICTS
Run ID                 : forward_shadow_coverage_20260709_115317
Horizon                : 24h
Decision Rows          : 32
Directional Decisions  : 23
Evaluation Rows        : 30
Complete Evaluations   : 14
Shadow Signals         : 14
Evaluated Shadow       : 14

Forward Regime Coverage:
- TRENDING_BULL: rows=32 | directional=23 | share=100.0% | direct=0 | proxy/text=0

Shadow Gate Coverage:
- STRUCTURE_SCORE_GE_10: signals=14 | eval=14 | avg=0.8834% | win=100.0% | dominant_regime=TRENDING_BULL

Bull Regime Probes:
- BULL_STRUCTURE_SCORE_GE_10: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=39 | bt_net=-0.5158%
- BULL_STRUCTURE_SCORE_GE_10_LONG: FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT | fwd_n=14 | fwd_avg=0.8834% | fwd_win=100.0% | src=shadow_ledger_sync | bt_n=39 | bt_net=-0.5158%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=17 | bt_net=0.4073%
- BULL_RISK_MEDIUM: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=37 | bt_net=-0.3898%
- BULL_SCORE_GE_80: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=16 | bt_net=-0.0115%
- BULL_BNB_LONG_SCORE_GE_60: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | src=decision_evaluations | bt_n=11 | bt_net=0.3533%

Bear Regime Zero-Signal Diagnostics:
- REGIME_TRENDING_BEAR__RISK_MEDIUM: cause=NO_TRENDING_BEAR_FORWARD_DECISIONS | matches=0 | bear_decisions=0
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: cause=NO_TRENDING_BEAR_FORWARD_DECISIONS | matches=0 | bear_decisions=0
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: cause=NO_TRENDING_BEAR_FORWARD_DECISIONS | matches=0 | bear_decisions=0
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: cause=NO_TRENDING_BEAR_FORWARD_DECISIONS | matches=0 | bear_decisions=0

Backtest/Forward Contradictions:
⚠️ BULL_STRUCTURE_SCORE_GE_10: Forward avg=0.8834% با n=14 اما Backtest net=-0.5158% است.
⚠️ BULL_STRUCTURE_SCORE_GE_10_LONG: Forward avg=0.8834% با n=14 اما Backtest net=-0.5158% است.

Blockers:
⛔ هیچ تصمیم Forward در TRENDING_BEAR وجود ندارد؛ Regime Bear shadow gates طبیعی است که signal نگیرند.
⛔ Shadow evaluated samples کمتر از 30 است: 14

Recommendations:
→ Regime Bear gates را فعال نگه دار، اما قضاوت را تا رخ دادن TRENDING_BEAR در Forward به تعویق بینداز.
→ فعال‌ترین Bull probe فعلی: BULL_STRUCTURE_SCORE_GE_10 | forward n=14 | avg=0.8834% | verdict=FORWARD_PROMISING_LOW_SAMPLE_BACKTEST_CONFLICT.
→ Bull probe فقط مشاهده‌ای است؛ تا وقتی Backtest/Forward هر دو robust نشوند، به Shadow Candidate ارتقا نده.
→ برای تصمیم‌گیری بعدی، STRUCTURE_SCORE_GE_10 را جداگانه به تفکیک regime در Forward دنبال کن.

Warnings:
⚠️ این ماژول فقط coverage و probe تحقیقاتی می‌سازد؛ هیچ Paper/Live فعال نمی‌کند.
⚠️ Bull probeها کاندید قطعی نیستند؛ v6.3.1 اگر لازم باشد از Shadow Ledger برای همگام‌سازی ارزیابی‌ها استفاده می‌کند.
⚠️ برچسب‌های legacy/proxy regime برای تحقیق‌اند؛ Forward جدید DIRECT_ENGINE ارزش بیشتری دارد.
==============================================================================================================