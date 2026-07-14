==============================================================================================================
🧭 Freakto Forward Test Status v9.0.0
==============================================================================================================
Status          : FORWARD_TEST_COLLECTING
Progress Score  : 56/100
Readiness Level : RESEARCH_ONLY
Paper Ready     : False
Live Ready      : False

Data Progress:
- Complete evaluations : 64/100
- Closed paper trades  : 0/30
- Open paper trades    : 0
- Total paper trades   : 0
- Regime-labeled       : 61/30
- Unknown regime       : 3
- Symbols evaluated    : 1
- Symbols scanned      : 6
- Forward runs         : 37/39 successful
- Forward days         : 10/30
- First run UTC        : 2026-07-05T17:39:28.376869+00:00
- Last run UTC         : 2026-07-14T07:26:51.170741+00:00

Notes:
✓ Regime-labeled samples برای تحلیل اولیه کافی است.

Blockers:
⛔ Complete evaluations کمتر از 100 است: 64
⛔ Closed paper trades کمتر از 30 است: 0
⛔ روزهای Forward Test کمتر از 30 است: 10

Next Actions:
→ اجرای منظم decision_evaluator.py بعد از ثبت تصمیم‌های جدید.
→ اجرای portfolio_scanner.py --paper تا فقط فرصت‌های مجاز Paper ثبت شوند.
→ این چرخه را روزانه یا هر کندل 4h اجرا کن تا حداقل 30 روز داده Forward جمع شود.

Safe cycle command:
python forward_test_dashboard.py --cycle --validate

Windows scheduled-task/batch friendly command:
python forward_test_dashboard.py --cycle --validate --continue-on-error
==============================================================================================================