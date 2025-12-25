@echo off
setlocal

echo ============================================================
echo XTTS GPU Background Test
echo ============================================================
echo.
echo Starting XTTS in background process...
echo This will take 2-5 minutes for first GPU load.
echo.
echo Output will be written to: xtts_gpu_output.txt
echo.

REM Start Python in background, redirect output
start /B cmd /c ".venv\Scripts\python.exe test_xtts_gpu_simple.py > xtts_gpu_output.txt 2>&1"

echo Process started! Waiting 3 minutes...
echo.

REM Wait 3 minutes
timeout /t 180 /nobreak

echo.
echo Checking results...
echo ============================================================
type xtts_gpu_output.txt
echo ============================================================
echo.

REM Check if output file was created
if exist "outputs\audio\xtts_gpu_simple.wav" (
    echo.
    echo [SUCCESS] Audio file generated!
    dir "outputs\audio\xtts_gpu_simple.wav"
) else (
    echo.
    echo [WAITING] File not ready yet, check xtts_gpu_output.txt for progress
)

echo.
pause
