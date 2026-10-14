@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
if not exist "%~dp0backend\.venv\Scripts\python.exe" (
  echo Backend environment missing. Follow backend\README.md to install it first.
  pause
  exit /b 1
)
"%~dp0backend\.venv\Scripts\python.exe" "%~dp0scripts\dev.py" start %*
if errorlevel 1 (
  pause
  exit /b 1
)
exit /b 0
