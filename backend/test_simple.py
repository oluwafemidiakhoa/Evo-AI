"""
Simple test server to verify setup.
Run this first before the full Evo-AI backend.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI(
    title="Evo-AI Test Server",
    description="Simple test to verify FastAPI is working",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Evo-AI Backend is running!",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "evo-ai-test",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/test")
async def test():
    """Test endpoint."""
    return {
        "test": "success",
        "message": "If you see this, FastAPI is working correctly!",
        "next_step": "Now you can start the full Evo-AI backend"
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  EVO-AI TEST SERVER")
    print("="*60)
    print("\n  Server starting on http://localhost:8000")
    print("  API Docs: http://localhost:8000/docs")
    print("\n  Press Ctrl+C to stop\n")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
