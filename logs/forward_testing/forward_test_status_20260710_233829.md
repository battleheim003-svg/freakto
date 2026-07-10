==============================================================================================================
🧭 Freakto Forward Test Status v9.0.0
==============================================================================================================
Status          : FORWARD_TEST_COLLECTING
Progress Score  : 50/100
Readiness Level : RESEARCH_ONLY
Paper Ready     : False
Live Ready      : False

Data Progress:
- Complete evaluations : 51/100
- Closed paper trades  : 0/30
- Open paper trades    : 0
- Total paper trades   : 0
- Regime-labeled       : 51/30
- Unknown regime       : 0
- Symbols evaluated    : 1
- Symbols scanned      : 0
- Forward runs         : 23/25 successful
- Forward days         : 6/30
- First run UTC        : 2026-07-05T17:39:28.376869+00:00
- Last run UTC         : 2026-07-10T23:37:15.913143+00:00

Notes:
✓ Regime-labeled samples برای تحلیل اولیه کافی است.

Blockers:
⛔ Complete evaluations کمتر از 100 است: 51
⛔ Closed paper trades کمتر از 30 است: 0
⛔ روزهای Forward Test کمتر از 30 است: 6

Next Actions:
→ اجرای منظم decision_evaluator.py بعد از ثبت تصمیم‌های جدید.
→ اجرای portfolio_scanner.py --paper تا فقط فرصت‌های مجاز Paper ثبت شوند.
→ این چرخه را روزانه یا هر کندل 4h اجرا کن تا حداقل 30 روز داده Forward جمع شود.

Safe cycle command:
python forward_test_dashboard.py --cycle --validate

Windows scheduled-task/batch friendly command:
python forward_test_dashboard.py --cycle --validate --continue-on-error
==============================================================================================================