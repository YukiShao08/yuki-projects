@echo off
REM Batch file to launch FastAPI server in foreground mode
REM This will show all server logs in the CMD window

cd /d "%~dp0"

echo ======================================================================
echo Launching FastAPI Server (Foreground Mode)
echo ======================================================================
echo.
echo Working directory: %CD%
echo Server will be available at: http://127.0.0.1:8000
echo API Documentation: http://127.0.0.1:8000/docs
echo.
echo You will see all server logs and debug output in this window.
echo Press Ctrl+C to stop the server
echo.
echo ======================================================================
echo.

REM Clear Python cache
if exist __pycache__ (
    echo Clearing Python cache...
    rmdir /s /q __pycache__
)

REM Run the Python script
python launch_server_foreground.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ======================================================================
    echo Server stopped with an error
    echo ======================================================================
    pause
)

