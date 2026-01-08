"""
Script to launch the FastAPI server
Run this script to start the uvicorn server
"""

import subprocess
import sys
import os
from pathlib import Path

def launch_server():
    """Launch the FastAPI server using uvicorn"""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    
    print("="*70)
    print("Launching FastAPI Server")
    print("="*70)
    print(f"Working directory: {script_dir}")
    print(f"Server will be available at: http://127.0.0.1:8000")
    print(f"API Documentation: http://127.0.0.1:8000/docs")
    print("="*70)
    print()
    print("Starting uvicorn server...")
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        # Clear Python cache before starting
        import shutil
        cache_dir = script_dir / "__pycache__"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            print("Cleared __pycache__ directory")
        
        # Launch uvicorn with auto-reload
        # Using --reload-dir to ensure all changes are detected
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--reload",
            "--reload-dir", str(script_dir),
            "--host", "127.0.0.1",
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    launch_server()

