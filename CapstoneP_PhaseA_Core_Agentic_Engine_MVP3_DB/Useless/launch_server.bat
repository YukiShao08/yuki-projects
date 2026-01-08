@echo off
REM Script to launch the FastAPI server
REM Double-click this file or run from command line to start the server

cd /d "%~dp0"
echo ======================================================================
echo Launching FastAPI Server
echo ======================================================================
echo Working directory: %CD%
echo Server will be available at: http://127.0.0.1:8000
echo API Documentation: http://127.0.0.1:8000/docs
echo ======================================================================
echo.
echo Starting uvicorn server...
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000

pause

