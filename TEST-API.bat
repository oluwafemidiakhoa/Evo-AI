@echo off
echo ============================================
echo Testing Evo-AI API
echo ============================================
echo.

REM Test health endpoint
echo [1/4] Testing health endpoint...
curl -s http://localhost:8000/health
echo.
echo.

REM Create a test campaign
echo [2/4] Creating test campaign...
curl -s -X POST "http://localhost:8000/api/campaigns" ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Test Campaign\",\"description\":\"API test\",\"config\":{\"max_rounds\":3,\"variants_per_round\":2,\"evaluators\":[\"llm_judge\"]}}"
echo.
echo.

REM List campaigns
echo [3/4] Listing campaigns...
curl -s http://localhost:8000/api/campaigns | python -m json.tool
echo.
echo.

echo [4/4] Open http://localhost:8000/docs for interactive API testing
echo.
echo ============================================
echo Test complete!
echo ============================================
pause
