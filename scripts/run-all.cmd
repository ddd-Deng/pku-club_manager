@echo off
setlocal
cd /d "%~dp0.."

echo ============================================================
echo  Campus Club Manager - local launcher
echo  It will open 3 windows: TUNNEL / BACKEND / FRONTEND.
echo  KEEP ALL 3 WINDOWS OPEN. Closing any one breaks the site.
echo ============================================================
echo.

rem --- window 1: SSH tunnel to shared DB ---
start "CLUB-1-TUNNEL-DO-NOT-CLOSE" cmd /k "ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L 127.0.0.1:13307:127.0.0.1:13307 -p 1021 group7@8.130.213.80"

echo Waiting for tunnel... type the SERVER PASSWORD in the TUNNEL window now.
set /a waited=0
:wait_tunnel
timeout /t 2 /nobreak >nul
set /a waited+=2
netstat -ano | findstr ":13307" | findstr "LISTENING" >nul
if not errorlevel 1 goto tunnel_ok
if %waited% GEQ 90 goto tunnel_timeout
goto wait_tunnel
:tunnel_timeout
echo WARNING: tunnel not up after 90s. Check the TUNNEL window password.
goto start_rest
:tunnel_ok
echo Tunnel OK.

:start_rest
rem --- window 2: backend ---
start "CLUB-2-BACKEND-DO-NOT-CLOSE" cmd /k "cd /d %~dp0..\backend & .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080"

rem --- window 3: frontend ---
start "CLUB-3-FRONTEND-DO-NOT-CLOSE" cmd /k "cd /d %~dp0..\frontend & npm run dev -- --host 127.0.0.1 --port 5173 --strictPort"

echo.
echo Backend window should show:  Uvicorn running on http://127.0.0.1:8080
echo Frontend window should show: VITE ... ready ... http://127.0.0.1:5173/
echo Then open browser:  http://127.0.0.1:5173/
echo Login: your student number + password 123456
echo.
echo You may close THIS window, but keep the 3 service windows open.
pause
