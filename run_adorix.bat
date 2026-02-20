@echo off
setlocal

echo ========================================
echo ADORIX PROJECT - STARTUP
echo ========================================

:: Check if backend directory exists
if not exist "backend" (
    echo [ERROR] Backend directory not found!
    pause
    exit /b
)

:: Check if frontend directory exists
if not exist "frontend" (
    echo [ERROR] Frontend directory not found!
    pause
    exit /b
)

echo.
echo Launching Frontend (React)...
start cmd /k "cd frontend && npm run dev"

echo.
echo Launching Backend (FastAPI)...
:: Check if venv exists and use it if it does
if exist "backend\venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    cmd /k "cd backend && venv\Scripts\activate && python main.py"
) else (
    echo [WARN] Virtual environment not found, using global python...
    cmd /k "cd backend && python main.py"
)

echo.
echo ========================================
echo All services are launching.
echo Close the individual windows to stop.
echo ========================================
pause
