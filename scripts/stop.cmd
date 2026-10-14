@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
if not exist "%~dp0..\backend\.venv\Scripts\python.exe" (
  echo Backend environment missing. Follow backend\README.md to install it first.
  pause
  exit /b 1
)
"%~dp0..\backend\.venv\Scripts\python.exe" "%~dp0dev.py" stop %*
if errorlevel 1 (
  pause
  exit /b 1
)
exit /b 0
