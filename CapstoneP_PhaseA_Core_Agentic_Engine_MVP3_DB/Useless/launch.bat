@echo off
REM Launch script for Banking Agent FastAPI Server
REM Windows batch file to start the agent

echo ========================================
echo Banking Agent - FastAPI Server Launcher
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ and try again
    pause
    exit /b 1
)

echo [1/4] Checking Python version...
python --version
echo.

echo [2/4] Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo WARNING: Dependencies may not be installed
    echo Run: pip install -r requirements.txt
    echo.
)

echo [3/4] Checking for .env file...
if not exist .env (
    echo WARNING: .env file not found
    echo Please create .env file with SECOND_MIND_API_KEY
    echo.
) else (
    echo .env file found
    echo.
)

echo [4/4] Checking for banking index...
set INDEX_PATH=..\CapstoneP_PhaseB_RAG\my_notes.index
if not exist %INDEX_PATH% (
    echo WARNING: Banking index not found at %INDEX_PATH%
    echo The agent will work but without local banking knowledge base
    echo To build the index, run in Phase B project:
    echo   python rag_pipeline_custom_embeddings.py
    echo.
) else (
    echo Banking index found
    echo.
)

echo ========================================
echo Starting FastAPI server...
echo ========================================
echo.
echo Server will be available at: http://localhost:8000
echo Press CTRL+C to stop the server
echo.

REM Start the server
uvicorn main:app --reload

pause

