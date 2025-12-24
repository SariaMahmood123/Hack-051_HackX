@echo off
echo ============================================================
echo XTTS v2 Setup - Fixed Installation
echo ============================================================
echo.

cd /d %~dp0

echo [1/4] Installing PyTorch with CUDA support...
echo This may take 2-5 minutes...
.venv\Scripts\pip.exe install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121
echo.

echo [2/4] Installing TTS (without building from source)...
echo Trying pre-built wheel...
.venv\Scripts\pip.exe install --no-build-isolation TTS==0.22.0
if errorlevel 1 (
    echo.
    echo Pre-built installation failed. Trying alternative...
    .venv\Scripts\pip.exe install TTS --no-deps
    .venv\Scripts\pip.exe install -r requirements.txt
)
echo.

echo [3/4] Downloading sample reference voice...
.venv\Scripts\python.exe scripts\download_sample_voice.py
echo.

echo [4/4] Testing XTTS...
.venv\Scripts\python.exe test_xtts.py
echo.

echo ============================================================
echo Setup complete! Check test_xtts.py output above.
echo ============================================================
echo.
pause
