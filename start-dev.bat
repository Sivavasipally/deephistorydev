@echo off
REM Quick start script for development mode (Windows)

echo ====================================
echo Git History Analyzer v2.0
echo React + FastAPI Development Server
echo ====================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

REM Start backend in new window
echo Starting FastAPI backend on port 8000...
start "Git Analyzer Backend" cmd /k "venv\Scripts\activate && python start_backend.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend in new window
echo Starting React frontend on port 3000...
start "Git Analyzer Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ====================================
echo Both servers are starting...
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/api/docs
echo ====================================
echo.
echo Press any key to exit...
pause > nul
