@echo off
REM Simple batch file to start the server and show logs
REM Double-click this file or run from command line

cd /d "%~dp0"
title FastAPI Server - Console Logs

echo.
echo ======================================================================
echo FastAPI Server - Starting...
echo ======================================================================
echo.
echo All server logs will be displayed in this window.
echo To stop the server, press Ctrl+C
echo.
echo ======================================================================
echo.

python launch_server_foreground.py

pause

