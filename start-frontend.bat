@echo off
echo ============================================
echo Starting Evo-AI Frontend
echo ============================================
echo.

cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

REM Check if .env.local exists
if not exist ".env.local" (
    echo Creating .env.local...
    echo NEXT_PUBLIC_API_URL=http://localhost:8000 > .env.local
)

echo.
echo ============================================
echo Frontend starting on http://localhost:3000
echo Press Ctrl+C to stop
echo ============================================
echo.

REM Start the dev server
call npm run dev
