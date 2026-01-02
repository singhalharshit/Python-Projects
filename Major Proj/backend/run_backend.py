"""
Backend Server Launcher
Starts the FastAPI backend with proper configuration
"""
import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Decision Assistant Backend...")
    print(f"📁 Working directory: {backend_dir}")
    print(f"🌐 Server will be available at: http://localhost:8000")
    print(f"📖 API docs at: http://localhost:8000/docs")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
