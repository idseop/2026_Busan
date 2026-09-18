@echo off
cd /d "%~dp0"
if exist "..\..\.venv-check\Scripts\python.exe" (
  "..\..\.venv-check\Scripts\python.exe" serve.py
) else (
  python serve.py
)
pause
