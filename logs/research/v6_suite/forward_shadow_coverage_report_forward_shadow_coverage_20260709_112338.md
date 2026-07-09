==============================================================================================================
🔎 Freakto Forward Shadow Coverage & Bull Regime Probe v6.3.0
==============================================================================================================
Status                 : FORWARD_SHADOW_COVERAGE_READY
Run ID                 : forward_shadow_coverage_20260709_112338
Horizon                : 24h
Decision Rows          : 49
Directional Decisions  : 28
Evaluation Rows        : 46
Complete Evaluations   : 0
Shadow Signals         : 16
Evaluated Shadow       : 16

Forward Regime Coverage:
- TRENDING_BULL: rows=43 | directional=27 | share=87.76% | direct=0 | proxy/text=0
- TRENDING_BEAR: rows=6 | directional=1 | share=12.24% | direct=0 | proxy/text=0

Shadow Gate Coverage:
- STRUCTURE_SCORE_GE_10: signals=14 | eval=14 | avg=0.8834% | win=100.0% | dominant_regime=TRENDING_BULL
- HISTORICAL_EDGE_SCORE_GE_1: signals=2 | eval=2 | avg=-3.0511% | win=0.0% | dominant_regime=TRENDING_BULL

Bull Regime Probes:
- BULL_STRUCTURE_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=0 | bt_net=0.0%
- BULL_STRUCTURE_SCORE_GE_10_LONG: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=0 | bt_net=0.0%
- BULL_VOLUME_SCORE_GE_10: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=0 | bt_net=0.0%
- BULL_RISK_MEDIUM: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=0 | bt_net=0.0%
- BULL_SCORE_GE_80: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=0 | bt_net=0.0%
- BULL_BNB_LONG_SCORE_GE_60: NO_FORWARD_SAMPLE | fwd_n=0 | fwd_avg=0.0% | fwd_win=0.0% | bt_n=0 | bt_net=0.0%

Bear Regime Zero-Signal Diagnostics:
- REGIME_TRENDING_BEAR__RISK_MEDIUM: cause=TRENDING_BEAR_EXISTS_BUT_NO_RISK_MEDIUM | matches=0 | bear_decisions=1
- REGIME_TRENDING_BEAR__RISK_MEDIUM__SHORT: cause=TRENDING_BEAR_EXISTS_BUT_NO_RISK_MEDIUM | matches=0 | bear_decisions=1
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10: cause=TRENDING_BEAR_EXISTS_BUT_STRUCTURE_LT_10 | matches=0 | bear_decisions=1
- REGIME_TRENDING_BEAR__STRUCTURE_SCORE_GE_10__SHORT: cause=TRENDING_BEAR_EXISTS_BUT_STRUCTURE_LT_10 | matches=0 | bear_decisions=1

Blockers:
⛔ Shadow evaluated samples کمتر از 30 است: 16

Recommendations:
→ برای تصمیم‌گیری بعدی، STRUCTURE_SCORE_GE_10 را جداگانه به تفکیک regime در Forward دنبال کن.

Warnings:
⚠️ این ماژول فقط coverage و probe تحقیقاتی می‌سازد؛ هیچ Paper/Live فعال نمی‌کند.
⚠️ Bull probeها کاندید قطعی نیستند؛ تضاد Forward کم‌نمونه با Backtest باید جدی گرفته شود.
⚠️ برچسب‌های legacy/proxy regime برای تحقیق‌اند؛ Forward جدید DIRECT_ENGINE ارزش بیشتری دارد.
==============================================================================================================