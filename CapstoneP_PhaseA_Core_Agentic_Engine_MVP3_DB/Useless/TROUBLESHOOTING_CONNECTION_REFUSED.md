# How to Resolve "ERR_CONNECTION_REFUSED" Error

## Problem
When accessing `http://127.0.0.1:8000`, you see **ERR_CONNECTION_REFUSED**.

## Root Cause
The FastAPI server is **not running**.

## Simple Solution

### Option 1: Using Python Launcher (Recommended for Windows)
```powershell
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseA_Core_Agentic_Engine
py launch_server_foreground.py
```

### Option 2: Using Python Directly
```powershell
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseA_Core_Agentic_Engine
python launch_server_foreground.py
```

### Option 3: Using Batch File (Double-click)
1. Navigate to: `C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseA_Core_Agentic_Engine`
2. Double-click `start_server.bat` or `launch_server_foreground.bat`

### Option 4: Direct Uvicorn Command
```powershell
cd C:\Users\HP\AppData\Roaming\Python\Python310\Scripts\GenAI\CapstoneP_PhaseA_Core_Agentic_Engine
py -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Verify Server is Running

After starting, you should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Or check with:
```powershell
netstat -ano | findstr :8000
```

If you see `LISTENING` status, the server is running.

## Quick Checklist

- [ ] Server process is running (check with `netstat` or Task Manager)
- [ ] No firewall blocking port 8000
- [ ] Correct directory (Phase A project folder)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] No port conflicts (another app using port 8000)

## Stop the Server

Press `Ctrl+C` in the terminal, or run:
```powershell
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*"
```

Or use: `stop_server.bat`

