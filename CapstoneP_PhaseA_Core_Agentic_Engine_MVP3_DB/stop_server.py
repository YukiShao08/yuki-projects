"""
Script to stop the FastAPI server
Run this script to gracefully stop all running uvicorn processes
"""

import subprocess
import sys
import os

def stop_server():
    """Stop all running uvicorn processes"""
    
    print("="*70)
    print("Stopping FastAPI Server")
    print("="*70)
    print()
    
    try:
        # Find all uvicorn processes
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq uvicorn.exe"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if "uvicorn.exe" not in result.stdout:
            print("No uvicorn processes found. Server is not running.")
            return
        
        # Extract PIDs from the output
        lines = result.stdout.split('\n')
        pids = []
        
        for line in lines:
            if "uvicorn.exe" in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[1])
                        pids.append(pid)
                    except (ValueError, IndexError):
                        continue
        
        if not pids:
            print("No uvicorn processes found to stop.")
            return
        
        print(f"Found {len(pids)} uvicorn process(es): {pids}")
        print()
        
        # Stop each process
        stopped_count = 0
        for pid in pids:
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    print(f"[OK] Stopped process PID {pid}")
                    stopped_count += 1
                else:
                    print(f"[WARNING] Could not stop process PID {pid}: {result.stderr}")
            except Exception as e:
                print(f"[ERROR] Error stopping process PID {pid}: {e}")
        
        print()
        print("="*70)
        if stopped_count > 0:
            print(f"Successfully stopped {stopped_count} process(es)")
        else:
            print("No processes were stopped")
        print("="*70)
        
    except FileNotFoundError:
        print("Error: 'tasklist' or 'taskkill' command not found.")
        print("This script requires Windows command-line tools.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    stop_server()

