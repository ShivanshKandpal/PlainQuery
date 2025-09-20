@echo off
cd /d "d:\sem7\confluentia-proj - Copy"
call .venv\Scripts\activate.bat
python test_api.py
pause