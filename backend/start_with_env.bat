@echo off
cd /d %~dp0

REM Load environment variables from .env
for /f "usebackq tokens=*" %%a in (".env") do (
    echo %%a | findstr /v "^#" | findstr /v "^$" > nul
    if not errorlevel 1 set %%a
)

REM Start server
venv\Scripts\python.exe -m uvicorn evo_ai.api.app:app --host 127.0.0.1 --port 8002 --reload
