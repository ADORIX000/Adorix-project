@echo off
REM Start Adorix Project - All Components

echo.
echo ========================================
echo ADORIX PROJECT - STARTUP
echo ========================================
echo.
echo This will open 3 terminals:
echo  1. Core Controller (vision + ads)
echo  2. WebSocket Server (backend)
echo  3. Frontend UI (React)
echo.
pause

REM Get the project root directory
cd /d "%~dp0"

REM Terminal 1: Core Controller
echo Launching Core Controller...
start "Core Controller" cmd /k "python -m core_controller.main"

REM Wait a bit for first terminal to start
timeout /t 2 /nobreak

REM Terminal 2: WebSocket Server
echo Launching WebSocket Server...
start "WebSocket Server" cmd /k "python -m core_controller.websocket_server"

REM Wait a bit
timeout /t 2 /nobreak

REM Terminal 3: Frontend
echo Launching Frontend...
cd frontend
start "Frontend (React)" cmd /k "npm run dev"

echo.
echo ========================================
echo All components are starting!
echo Open browser: http://localhost:5173
echo ========================================
echo.
