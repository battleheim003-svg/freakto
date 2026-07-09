==============================================================================================================
🔎 Freakto Forward Shadow Coverage & Bull Regime Probe v6.3.0
==============================================================================================================
Status                 : NO_BEAR_FORWARD_COVERAGE_YET
Run ID                 : forward_shadow_coverage_20260709_112433
Horizon                : 24h
Decision Rows          : 32
Directional Decisions  : 23
Evaluation Rows        : 30
Complete Evaluations   : 0
Shadow Signals         : 14
Evaluated Shadow       : 14

Forward Regime Coverage:
- TRENDING_BULL: rows=32 | directional=23 | share=100.0% | direct=0 | proxy/text=0

Shadow Gate Coverage:
- STRUCTURE_SCORE_GE_10: signals=14 | eval=14 | avg=0.8834% | win=100.0% | dominant_regime=TRENDING_BULL

Bull Regime Probes:
- BULL_STRUCTURE_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=39 | bt_net=-0.5158%
- BULL_STRUCTURE_SCORE_GE_10_LONG: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=39 | bt_net=-0.5158%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=17 | bt_net=0.4073%
- BULL_RISK_MEDIUM: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=37 | bt_net=-0.3898%
- BULL_SCORE_GE_80: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=16 | bt_net=-0.0115%
- BULL_BNB_LONG_SCORE_GE_60: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=11 | bt_net=0.3533%

Bear Regime Zero-Signal Diagnostics:
- REGIME_TRENDING_BEAR__RISK_MEDIUM: cause=NO_TRENDING_BEAR_FORWARD_DECISIONS | matches=0 | bear_decisions=0
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: cause=NO_TRENDING_BEAR_FORWARD_DECISIONS | matches=0 | bear_decisions=0
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: cause=NO_TRENDING_BEAR_FORWARD_DECISIONS | matches=0 | bear_decisions=0
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: cause=NO_TRENDING_BEAR_FORWARD_DECISIONS | matches=0 | bear_decisions=0

Blockers:
⛔ هیچ تصمیم Forward در TRENDING_BEAR وجود ندارد؛ Regime Bear shadow gates طبیعی است که signal نگیرند.
⛔ Shadow evaluated samples کمتر از 30 است: 14

Recommendations:
→ Regime Bear gates را فعال نگه دار، اما قضاوت را تا رخ دادن TRENDING_BEAR در Forward به تعویق بینداز.
→ برای تصمیم‌گیری بعدی، STRUCTURE_SCORE_GE_10 را جداگانه به تفکیک regime در Forward دنبال کن.

Warnings:
⚠️ این ماژول فقط coverage و probe تحقیقاتی می‌سازد؛ هیچ Paper/Live فعال نمی‌کند.
⚠️ Bull probeها کاندید قطعی نیستند؛ تضاد Forward کم‌نمونه با Backtest باید جدی گرفته شود.
⚠️ برچسب‌های legacy/proxy regime برای تحقیق‌اند؛ Forward جدید DIRECT_ENGINE ارزش بیشتری دارد.
==============================================================================================================