@echo off
cd /d "%~dp0"
where py >nul 2>&1
if not errorlevel 1 (
  py -3 serve.py
  pause
  exit /b
)
where python >nul 2>&1
if not errorlevel 1 (
  python serve.py
  pause
  exit /b
)
echo Python 3 is required. Install it from https://www.python.org/downloads/windows/
echo Then run this file again.
pause
