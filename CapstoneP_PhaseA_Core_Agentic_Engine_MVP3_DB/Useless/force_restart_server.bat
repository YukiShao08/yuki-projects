@echo off
REM Force complete restart of the FastAPI server
REM This script stops all processes, clears cache, and restarts

echo ======================================================================
echo Force Restart FastAPI Server
echo ======================================================================
echo.

REM Stop all uvicorn processes
echo [1/4] Stopping all uvicorn processes...
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *uvicorn*" >nul 2>&1
timeout /t 2 /nobreak >nul

REM Clear Python cache
echo [2/4] Clearing Python cache...
cd /d "%~dp0"
if exist __pycache__ rmdir /s /q __pycache__
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
for /r . %%f in (*.pyc) do @if exist "%%f" del /f /q "%%f"

REM Clear banking_notes_tool cache specifically
if exist banking_notes_tool\__pycache__ rmdir /s /q banking_notes_tool\__pycache__

echo [3/4] Cache cleared
echo.

REM Wait a moment
timeout /t 1 /nobreak >nul

REM Start server
echo [4/4] Starting server...
echo.
python launch_server.py

pause

