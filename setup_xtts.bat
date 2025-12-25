@echo off
echo ============================================================
echo XTTS v2 Setup - Quick Start
echo ============================================================
echo.

cd /d %~dp0

echo [1/3] Installing TTS library...
.venv\Scripts\pip.exe install TTS==0.22.0
echo.

echo [2/3] Downloading sample reference voice...
.venv\Scripts\python.exe scripts\download_sample_voice.py
echo.

echo [3/3] Testing XTTS...
.venv\Scripts\python.exe test_xtts.py
echo.

echo ============================================================
echo Setup complete! Check test_xtts.py output above.
echo ============================================================
pause
