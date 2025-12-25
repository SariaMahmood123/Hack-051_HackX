"""
Run the LUMEN backend server
"""
import uvicorn
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add parent directory to path so backend module can be imported
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from project root
load_dotenv(project_root / ".env")

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                   LUMEN Backend Server                    ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Starting server...
    Host: {host}
    Port: {port}
    Auto-reload: {reload}
    API Docs: http://{host}:{port}/docs
    ReDoc: http://{host}:{port}/redoc
    
    """)
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
