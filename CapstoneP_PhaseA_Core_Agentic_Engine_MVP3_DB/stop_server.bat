@echo off
REM Script to stop the FastAPI server
REM Double-click this file or run from command line to stop all uvicorn processes

echo ======================================================================
echo Stopping FastAPI Server
echo ======================================================================
echo.

REM Find and kill all uvicorn processes
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq uvicorn.exe" /FO LIST ^| findstr /I "PID"') do (
    echo Stopping process PID %%a...
    taskkill /F /PID %%a >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Could not stop process PID %%a
    ) else (
        echo [OK] Stopped process PID %%a
    )
)

REM Also try to kill by process name (in case exe name is different)
taskkill /F /IM uvicorn.exe >nul 2>&1

echo.
echo ======================================================================
echo Server stop process completed
echo ======================================================================
echo.
pause

