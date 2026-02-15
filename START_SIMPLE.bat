@echo off
REM ADORIX Kiosk - Simple Startup

cd /d "%~dp0"

echo.
echo ============================================================
echo          ADORIX KIOSK - STARTUP
echo ============================================================
echo.
echo This will:
echo   1. Show camera with detected users
echo   2. Play ads when idle
echo   3. Connect frontend at http://localhost:5173
echo.
echo Two terminals will open:
echo   - Terminal 1: ADORIX Kiosk (camera + ads)
echo   - Terminal 2: Frontend UI (React)
echo.
pause

REM Terminal 1: Main Kiosk with integrated WebSocket
start "ADORIX Kiosk" cmd /k "python adorix_kiosk.py"

timeout /t 2 /nobreak

REM Terminal 2: Frontend
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================================
echo All systems starting!
echo Open: http://localhost:5173
echo Press Ctrl+C to stop
echo ============================================================
echo.
