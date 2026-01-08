@echo off
REM Setup script for Banking Agent
REM Installs dependencies and checks configuration

echo ========================================
echo Banking Agent - Setup Script
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

echo [1/5] Python version check...
python --version
echo.

echo [2/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

echo [3/5] Checking for .env file...
if not exist .env (
    echo Creating .env template...
    (
        echo # Second Mind API Key ^(for chat/LLM^)
        echo SECOND_MIND_API_KEY=your_second_mind_api_key_here
        echo.
        echo # Optional: Groq API Key
        echo # GROQ_API_KEY=your_groq_api_key_here
        echo.
        echo # Optional: Proxy settings
        echo # HTTP_PROXY=http://127.0.0.1:7890
        echo # HTTPS_PROXY=http://127.0.0.1:7890
    ) > .env
    echo .env template created. Please edit it with your API key.
    echo.
) else (
    echo .env file already exists
    echo.
)

echo [4/5] Checking Phase B project...
set PHASE_B_PATH=..\CapstoneP_PhaseB_RAG
if not exist %PHASE_B_PATH% (
    echo WARNING: Phase B project not found at %PHASE_B_PATH%
    echo You need to build the banking index in Phase B project
    echo.
) else (
    echo Phase B project found
    echo.
)

echo [5/5] Checking for banking index...
set INDEX_PATH=..\CapstoneP_PhaseB_RAG\my_notes.index
if not exist %INDEX_PATH% (
    echo WARNING: Banking index not found
    echo.
    echo To build the index:
    echo   1. Navigate to Phase B project: cd ..\CapstoneP_PhaseB_RAG
    echo   2. Run: python rag_pipeline_custom_embeddings.py
    echo   3. Wait for index to be created (5-15 minutes)
    echo.
) else (
    echo Banking index found at %INDEX_PATH%
    echo.
)

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit .env file with your SECOND_MIND_API_KEY
echo   2. Build banking index in Phase B (if not done)
echo   3. Run launch.bat to start the server
echo.
pause

