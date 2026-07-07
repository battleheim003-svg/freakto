==============================================================================================================
🧭 Freakto Forward Test Status v5.3.3
==============================================================================================================
Status          : FORWARD_TEST_COLLECTING
Progress Score  : 19/100
Readiness Level : RESEARCH_ONLY
Paper Ready     : False
Live Ready      : False

Data Progress:
- Complete evaluations : 38/100
- Closed paper trades  : 0/30
- Open paper trades    : 0
- Total paper trades   : 0
- Regime-labeled       : 0/30
- Unknown regime       : 38
- Symbols evaluated    : 1
- Symbols scanned      : 0
- Forward runs         : 12/14 successful
- Forward days         : 3/30
- First run UTC        : 2026-07-05T17:39:28.376869+00:00
- Last run UTC         : 2026-07-07T23:34:10.364226+00:00

Blockers:
⛔ Complete evaluations کمتر از 100 است: 38
⛔ Closed paper trades کمتر از 30 است: 0
⛔ Regime-labeled samples کمتر از 30 است: 0
⛔ روزهای Forward Test کمتر از 30 است: 3

Next Actions:
→ اجرای منظم decision_evaluator.py بعد از ثبت تصمیم‌های جدید.
→ اجرای portfolio_scanner.py --paper تا فقط فرصت‌های مجاز Paper ثبت شوند.
→ چند اجرای جدید monitor.py --once پس از v4.7 لازم است تا regime_label وارد لاگ‌ها شود.
→ این چرخه را روزانه یا هر کندل 4h اجرا کن تا حداقل 30 روز داده Forward جمع شود.

Safe cycle command:
python forward_test_dashboard.py --cycle --validate

Windows scheduled-task/batch friendly command:
python forward_test_dashboard.py --cycle --validate --continue-on-error
==============================================================================================================