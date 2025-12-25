@echo off
echo ============================================================
echo XTTS GPU Test - No Interrupt Mode
echo ============================================================
echo.
echo This will run XTTS with GPU and generate audio.
echo The model load to GPU may take 2-3 minutes.
echo Please be patient and do not press any keys...
echo.

REM Run Python script and let it complete
.venv\Scripts\python.exe test_xtts_gpu_direct.py

echo.
echo ============================================================
echo Test complete! Check output above.
echo ============================================================
pause
