"""Start backend with environment variables"""
import subprocess
import os
import sys

# Set environment variables
env = os.environ.copy()

# Load from .env file
env_file = r"C:\Users\adminidiakhoa\Demo\Evo_AI\backend\.env"
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            env[key.strip()] = value.strip()
            print(f"Set {key.strip()}")

print("\n" + "="*80)
print("  STARTING EVO-AI BACKEND")
print("="*80)
print("\nBackend will be at: http://localhost:8002")
print("API Docs at: http://localhost:8002/docs\n")

backend_dir = r"C:\Users\adminidiakhoa\Demo\Evo_AI\backend"
python_exe = os.path.join(backend_dir, "venv", "Scripts", "python.exe")

# Start backend
process = subprocess.Popen(
    [
        python_exe,
        "-m", "uvicorn",
        "evo_ai.api.app:app",
        "--host", "127.0.0.1",
        "--port", "8002",
        "--reload"
    ],
    cwd=backend_dir,
    env=env
)

print(f"Backend started with PID: {process.pid}")
print("Press Ctrl+C to stop...\n")

try:
    process.wait()
except KeyboardInterrupt:
    print("\nStopping backend...")
    process.terminate()
    process.wait()
    print("Stopped!")
