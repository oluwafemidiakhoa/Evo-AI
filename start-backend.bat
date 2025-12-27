@echo off
echo ============================================
echo Starting Evo-AI Backend Server
echo ============================================
echo.

cd /d "%~dp0backend"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo Creating .env from .env.example...
    copy .env.example .env
)

REM Install/update dependencies
echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo ============================================
echo Backend server starting on http://localhost:8000
echo API Docs available at http://localhost:8000/docs
echo Press Ctrl+C to stop
echo ============================================
echo.

REM Start the server
uvicorn evo_ai.api.app:app --reload --host 0.0.0.0 --port 8000
