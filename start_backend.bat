@echo off
REM Quick start script for LUMEN backend

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                   LUMEN Backend Setup                     ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [1/4] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/4] Virtual environment already exists
)

REM Activate virtual environment
echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [3/4] Installing dependencies...
pip install -q -r requirements.txt

REM Check .env file
if not exist ".env" (
    echo [!] Warning: .env file not found
    echo     Copy .env.example to .env and configure GEMINI_API_KEY
    pause
)

REM Start server
echo [4/4] Starting backend server...
echo.
python backend/run.py
