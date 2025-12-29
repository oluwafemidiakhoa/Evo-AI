# Load .env file and start backend
$envFile = Get-Content .env
foreach ($line in $envFile) {
    if ($line -match '^\s*([^#][^=]*?)\s*=\s*(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
        Write-Host "Set $name" -ForegroundColor Green
    }
}

Write-Host "`nStarting Evo-AI Backend..." -ForegroundColor Cyan
Write-Host "Backend will be at: http://localhost:8002" -ForegroundColor Yellow
Write-Host "API Docs at: http://localhost:8002/docs`n" -ForegroundColor Yellow

& "venv\Scripts\python.exe" -m uvicorn evo_ai.api.app:app --host 127.0.0.1 --port 8002 --reload
