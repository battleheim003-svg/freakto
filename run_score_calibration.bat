@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python -X utf8 replay_evaluation_recorder_dashboard.py --apply
if errorlevel 1 exit /b %errorlevel%
python -X utf8 replay_score_calibration_dashboard.py --compact
pause
