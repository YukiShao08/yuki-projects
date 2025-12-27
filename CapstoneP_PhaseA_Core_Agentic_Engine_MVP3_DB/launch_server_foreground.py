"""
Script to launch the FastAPI server in foreground (so you can see logs)
Run this script to start the uvicorn server and see all output
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path

def launch_server():
    """Launch the FastAPI server using uvicorn in foreground"""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    
    # Clear Python cache before starting
    cache_dir = script_dir / "__pycache__"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print("Cleared __pycache__ directory")
    
    print("="*70)
    print("Launching FastAPI Server (Foreground Mode)")
    print("="*70)
    print(f"Working directory: {script_dir}")
    print(f"Server will be available at: http://127.0.0.1:8000")
    print(f"API Documentation: http://127.0.0.1:8000/docs")
    print("="*70)
    print()
    print("Starting uvicorn server...")
    print("You will see all server logs and debug output here.")
    print("Press Ctrl+C to stop the server")
    print()
    print("-"*70)
    print()
    
    # Check if running under debugger (debugpy)
    is_debugging = "debugpy" in sys.modules or "pydevd" in sys.modules
    
    try:
        if is_debugging:
            # When debugging, run uvicorn directly (no subprocess) to avoid debugger conflicts
            print("Debug mode detected - running uvicorn directly (no subprocess)")
            print("Note: Auto-reload is disabled in debug mode")
            print()
            print("-"*70)
            print()
            
            import uvicorn
            # Run directly without subprocess - this avoids debugger conflicts
            uvicorn.run(
                "main:app",
                host="127.0.0.1",
                port=8000,
                reload=False,  # Disable reload in debug mode
                log_level="info"
            )
        else:
            # Normal mode: use subprocess with reload enabled
            print("Auto-reload enabled")
            print()
            print("-"*70)
            print()
            
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    launch_server()

