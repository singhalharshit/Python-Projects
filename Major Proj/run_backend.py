
import os
import sys
import subprocess
from pathlib import Path

def run_backend():
    # Get backend directory
    project_root = Path(__file__).parent.absolute()
    backend_dir = project_root / "backend"
    
    print(f"🚀 Starting Backend Server from {backend_dir}...")
    
    # Check if venv is active (optional, assume user has python)
    
    cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    
    try:
        subprocess.run(cmd, cwd=str(backend_dir), check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to run server: {e}")
        print("Tip: Make sure you installed requirements using: pip install -r backend/requirements.txt")

if __name__ == "__main__":
    run_backend()
