@echo off
echo ============================================================
echo Fixing XTTS PyTorch Compatibility
echo ============================================================
echo.
echo Issue: TTS 0.22.0 requires PyTorch 2.2.0 or newer
echo Current: PyTorch 2.1.2
echo Solution: Upgrade to PyTorch 2.2.2+cu121
echo.

echo [1/2] Upgrading PyTorch to 2.2.2...
.venv\Scripts\pip.exe install --upgrade torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --index-url https://download.pytorch.org/whl/cu121
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to upgrade PyTorch
    echo Try manually: pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
    pause
    exit /b 1
)

echo.
echo [2/2] Testing XTTS again...
python test_xtts.py

echo.
echo ============================================================
echo Fix complete! Check output above.
echo ============================================================
pause
