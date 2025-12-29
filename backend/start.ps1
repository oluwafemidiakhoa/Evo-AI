# Start Backend with Environment Variables

# Set API keys
$env:ANTHROPIC_API_KEY = "sk-ant-YOUR-KEY-HERE"
$env:OPENAI_API_KEY = "sk-YOUR-KEY-HERE"
$env:DATABASE_URL = "postgresql://evo_user:evo_password@localhost:5432/evo_ai"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:ENVIRONMENT = "development"
$env:CORS_ORIGINS = '["http://localhost:3000"]'

Write-Host "Starting Evo-AI Backend..." -ForegroundColor Green
Write-Host "API Keys loaded" -ForegroundColor Yellow
Write-Host ""
Write-Host "Backend will be available at: http://localhost:8002" -ForegroundColor Cyan
Write-Host "API Docs at: http://localhost:8002/docs" -ForegroundColor Cyan
Write-Host ""

# Start server
& "venv\Scripts\python.exe" -m uvicorn evo_ai.api.app:app --host 127.0.0.1 --port 8002 --reload
