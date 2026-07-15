@echo off
cd /d %~dp0
call .venv\Scripts\activate
python -X utf8 monitor.py --once
python -X utf8 paper_trade_launch_dashboard.py --scan --decision-file logs/decisions.csv
python -X utf8 paper_trade_launch_dashboard.py --evaluate
python -X utf8 paper_trade_launch_dashboard.py --status
pause
