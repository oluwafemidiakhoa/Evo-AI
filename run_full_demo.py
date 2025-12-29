"""
Start backend with env vars and run evolution demo
"""
import subprocess
import time
import os
import requests
import sys

print("="*80)
print("  STARTING EVO-AI BACKEND WITH API KEYS")
print("="*80)
print()

# Set environment variables
env = os.environ.copy()
env.update({
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "sk-ant-YOUR-KEY-HERE"),
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "sk-YOUR-KEY-HERE"),
    "DATABASE_URL": "postgresql://evo_user:evo_password@localhost:5432/evo_ai",
    "REDIS_URL": "redis://localhost:6379/0",
    "CORS_ORIGINS": '["http://localhost:3000"]',
    "ENVIRONMENT": "development"
})

# Start backend
print("Starting backend...")
backend_dir = r"C:\Users\adminidiakhoa\Demo\Evo_AI\backend"
python_exe = os.path.join(backend_dir, "venv", "Scripts", "python.exe")

backend_process = subprocess.Popen(
    [
        python_exe,
        "-m", "uvicorn",
        "evo_ai.api.app:app",
        "--host", "127.0.0.1",
        "--port", "8002"
    ],
    cwd=backend_dir,
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

print("Waiting for backend to be ready...")
for i in range(30):
    try:
        response = requests.get("http://localhost:8002/health", timeout=1)
        if response.status_code == 200:
            print("[OK] Backend is ready!")
            print()
            break
    except:
        pass
    time.sleep(1)
    print(f"  Waiting... {i+1}/30")
else:
    print("[ERROR] Backend didn't start in 30 seconds")
    backend_process.kill()
    sys.exit(1)

# Now run the evolution demo
print("="*80)
print("  RUNNING EVOLUTION DEMO")
print("="*80)
print()

try:
    # Run the demo
    exec(open("see_evolution_now.py").read())
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    print("\nShutting down backend...")
    backend_process.kill()
    print("Done!")
