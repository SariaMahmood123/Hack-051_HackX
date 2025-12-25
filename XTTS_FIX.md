# XTTS Installation Fix

## Problem
TTS installation failed due to missing C++ build tools and PyTorch.

## Quick Fix

**Run this:**
```bash
.\setup_xtts_fixed.bat
```

## Manual Fix (if script fails)

**Step 1: Install PyTorch with CUDA**
```bash
.\.venv\Scripts\pip.exe install torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121
```

**Step 2: Install TTS dependencies**
```bash
.\.venv\Scripts\pip.exe install numpy scipy inflect librosa unidecode phonemizer
```

**Step 3: Try TTS without build tools**

**Option A - Pre-built wheel (fastest):**
```bash
.\.venv\Scripts\pip.exe install TTS --no-build-isolation
```

**Option B - If Option A fails:**
```bash
# Install without building C extensions (slightly slower inference)
.\.venv\Scripts\pip.exe install TTS --no-deps
.\.venv\Scripts\pip.exe install -r requirements.txt
```

**Step 4: Test**
```bash
python test_xtts.py
```

## If Still Fails: Install Visual Studio Build Tools

**Download & Install:**
1. Go to: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Download "Build Tools for Visual Studio 2022"
3. Run installer
4. Select: "Desktop development with C++"
5. Install (takes ~6GB, 10-20 minutes)
6. Restart terminal
7. Run: `.\setup_xtts_fixed.bat`

## Alternative: Use CPU-only (no CUDA)

If you want to skip GPU setup temporarily:
```bash
.\.venv\Scripts\pip.exe install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\pip.exe install TTS --no-build-isolation
```

**Note:** CPU-only will be much slower (~10x)

## Verify Installation

After successful install:
```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
python -c "from TTS.api import TTS; print('TTS OK')"
```

Expected output:
```
PyTorch: 2.1.2+cu121
CUDA: True
TTS OK
```
