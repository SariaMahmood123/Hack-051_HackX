@echo off
REM Quick start script for LUMEN frontend

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║                   LUMEN Frontend Setup                    ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check if Node.js and npm are installed
where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is not installed or not in PATH
    echo.
    echo Please install Node.js from: https://nodejs.org/
    echo Recommended version: v20.x LTS or higher
    echo.
    echo After installation:
    echo 1. Close and reopen this terminal
    echo 2. Run this script again
    echo.
    pause
    exit /b 1
)

echo [Node.js installed] Checking version...
node --version
npm --version
echo.

REM Check if node_modules exists
if not exist "frontend\node_modules\" (
    echo [1/3] Installing dependencies...
    cd frontend
    call npm install
    cd ..
) else (
    echo [1/3] Dependencies already installed
)

REM Check .env.local
if not exist "frontend\.env.local" (
    echo [2/3] Creating .env.local...
    copy frontend\.env.example frontend\.env.local
) else (
    echo [2/3] .env.local already exists
)

REM Start dev server
echo [3/3] Starting development server...
echo.
cd frontend
call npm run dev
