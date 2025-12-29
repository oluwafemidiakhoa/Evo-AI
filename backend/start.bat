@echo off
echo Loading environment variables from .env...

REM Read and set environment variables from .env file
for /f "usebackq tokens=1,2 delims==" %%a in ("C:\Users\adminidiakhoa\Demo\Evo_AI\backend\.env") do (
    set "%%a=%%b"
    echo Set %%a
)

echo.
echo Starting Evo-AI Backend...
echo Backend will be at: http://localhost:8002
echo API Docs at: http://localhost:8002/docs
echo.

cd /d "C:\Users\adminidiakhoa\Demo\Evo_AI\backend"
venv\Scripts\python.exe -m uvicorn evo_ai.api.app:app --host 127.0.0.1 --port 8002 --reload
