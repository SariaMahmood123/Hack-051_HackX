# 🔍 Pre-Launch Verification Checklist

Run through this checklist before testing the persona video pipeline.

---

## ✅ Backend Verification

### 1. Python Environment
```bash
# Check Python version
python --version
# Expected: Python 3.10.x

# Check virtual environment
which python
# Expected: /path/to/.venv-wsl/bin/python or similar
```

### 2. Dependencies Installed
```bash
# Check key packages
pip list | grep -E "torch|fastapi|TTS|google-generativeai"

# Expected output should include:
# torch              2.5.1+cu121
# fastapi            0.xxx
# TTS                0.xxx
# google-generativeai 0.xxx
```

### 3. GPU Available
```bash
nvidia-smi

# Expected: Shows RTX 4080 SUPER with available memory
# If "command not found": GPU drivers not installed
```

### 4. Assets Present
```bash
ls -la assets/

# Expected files:
# mkbhd.wav           ✅ MKBHD reference voice
# mkbhd2.jpg          ✅ MKBHD portrait
# reference_voice.wav ✅ iJustine reference voice
```

### 5. Backend Starts Successfully
```bash
cd d:\Hack-051_HackX
python backend/run.py

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

### 6. Health Check Passes
```bash
curl http://localhost:8000/api/health

# Expected:
# {"status":"healthy","timestamp":"..."}
```

---

## ✅ Frontend Verification

### 1. Node/npm Installed
```bash
node --version
# Expected: v18.x or higher

npm --version
# Expected: v9.x or higher
```

### 2. Dependencies Installed
```bash
cd frontend
npm install

# Should complete without errors
```

### 3. Configuration Correct
```bash
# Check next.config.js has API proxy
cat next.config.js | grep -A 5 "rewrites"

# Expected:
# async rewrites() {
#   return [
#     {
#       source: '/api/:path*',
#       destination: 'http://localhost:8000/api/:path*',
```

### 4. Frontend Starts Successfully
```bash
npm run dev

# Expected output:
# ready - started server on 0.0.0.0:3000
# url: http://localhost:3000
```

### 5. Persona Page Accessible
Open browser: **http://localhost:3000/persona**

Expected:
- ✅ "Persona Video Generator" heading
- ✅ Two persona cards (MKBHD, iJustine)
- ✅ Prompt textarea
- ✅ Generate button

---

## ✅ API Endpoint Verification

### 1. Endpoint Exists
```bash
curl -X POST http://localhost:8000/api/generate/persona-video \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","persona":"mkbhd"}' \
  --max-time 10

# Expected: Either starts processing OR returns validation error
# Should NOT return 404 or "Method Not Allowed"
```

### 2. Request Validation Works
```bash
# Test invalid persona
curl -X POST http://localhost:8000/api/generate/persona-video \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","persona":"invalid"}'

# Expected error:
# {"error":"InvalidInputException","message":"Invalid persona: invalid..."}
```

### 3. Required Fields Enforced
```bash
# Test missing prompt
curl -X POST http://localhost:8000/api/generate/persona-video \
  -H "Content-Type: application/json" \
  -d '{"persona":"mkbhd"}'

# Expected error about missing 'prompt' field
```

---

## ✅ AI Components Verification

### 1. Gemini Client
```bash
python -c "
from ai.gemini_client import GeminiClient
gemini = GeminiClient()
print('✅ Gemini import OK')
print(f'✅ Has generate_mkbhd_script: {hasattr(gemini, \"generate_mkbhd_script\")}')
print(f'✅ Has generate_ijustine_script: {hasattr(gemini, \"generate_ijustine_script\")}')
"

# Expected:
# ✅ Gemini import OK
# ✅ Has generate_mkbhd_script: True
# ✅ Has generate_ijustine_script: True
```

### 2. XTTS Wrapper
```bash
python -c "
from ai.xtts_wrapper import XTTSWrapper
xtts = XTTSWrapper()
print('✅ XTTS import OK')
print(f'✅ Has synthesize_with_intent: {hasattr(xtts, \"synthesize_with_intent\")}')
"

# Expected:
# ✅ XTTS import OK
# ✅ Has synthesize_with_intent: True
```

### 3. SadTalker Wrapper
```bash
python -c "
from ai.sadtalker_wrapper import SadTalkerWrapper
sadtalker = SadTalkerWrapper()
print('✅ SadTalker import OK')
print(f'✅ Has generate: {hasattr(sadtalker, \"generate\")}')
"

# Expected:
# ✅ SadTalker import OK
# ✅ Has generate: True
```

### 4. Motion Governor
```bash
python -c "
from ai.motion_governor import MotionGovernor
governor = MotionGovernor()
print('✅ MotionGovernor import OK')
print(f'✅ Has govern_coefficients: {hasattr(governor, \"govern_coefficients\")}')
"

# Expected:
# ✅ MotionGovernor import OK
# ✅ Has govern_coefficients: True
```

---

## ✅ Output Directories

```bash
# Check outputs directory exists
ls -la outputs/

# Expected structure:
# outputs/
#   audio/
#   video/

# If missing, create:
mkdir -p outputs/audio outputs/video
```

---

## ✅ Environment Variables

### Backend
```bash
# Check if GEMINI_API_KEY is set
python -c "
from backend.core.config import settings
print(f'GEMINI_API_KEY set: {bool(settings.GEMINI_API_KEY)}')
print(f'GEMINI_MODEL: {settings.GEMINI_MODEL}')
"

# Expected:
# GEMINI_API_KEY set: True
# GEMINI_MODEL: gemini-2.0-flash-exp (or similar)
```

### Frontend
```bash
cd frontend
echo $NEXT_PUBLIC_API_URL

# Expected: http://localhost:8000/api
# If empty, defaults in api.ts should work
```

---

## ✅ Full Integration Test

### Quick Test (MKBHD)
```bash
python backend/test_persona_endpoint.py

# Expected output:
# Testing MKBHD persona video generation...
# Request payload: { ... }
# [Wait 3-7 minutes]
# ✅ Success!
# Request ID: ...
# Processing time: 187.5s
# Video URL: http://localhost:8000/outputs/video/...
```

### Frontend Test
1. Open http://localhost:3000/persona
2. Select **MKBHD** persona
3. Enter prompt: **"Explain the new M4 Mac Mini"**
4. Click **"Generate MKBHD Video"**
5. Wait for progress indicator
6. Video should appear and auto-play

**Verify**:
- ✅ Video shows face with natural motion
- ✅ Lip sync matches audio
- ✅ Face is clear (GFPGAN enhancement)
- ✅ Motion is subtle (70-100% range)
- ✅ Pauses show reduced motion
- ✅ Emphasis shows increased motion

---

## 🐛 Common Issues

### Issue: Backend won't start
**Check**:
```bash
# Python version
python --version

# Virtual environment active
which python

# Dependencies installed
pip list | grep fastapi
```

### Issue: "Module not found" errors
**Fix**:
```bash
# Install missing dependencies
pip install -r requirements.txt

# Or install individually
pip install fastapi uvicorn torch TTS google-generativeai
```

### Issue: GPU not detected
**Check**:
```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"

# Expected: True
```

### Issue: Frontend can't connect to backend
**Check**:
1. Backend is running on port 8000
2. next.config.js has API proxy configured
3. No CORS errors in browser console

**Fix**:
```bash
# Restart both servers
# Backend: Ctrl+C, then: python backend/run.py
# Frontend: Ctrl+C, then: npm run dev
```

### Issue: Video generation fails
**Check backend logs**:
```bash
tail -f backend/logs/lumen.log

# Look for errors in:
# - Stage 1: Gemini script generation
# - Stage 2: XTTS audio synthesis
# - Stage 3: SadTalker video generation
```

### Issue: CUDA out of memory
**Fix**:
```bash
# Close other GPU processes
nvidia-smi --query-compute-apps=pid --format=csv,noheader | xargs -r kill

# Or restart backend
```

---

## 📋 Final Checklist

Before testing, confirm:

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] http://localhost:8000/api/health returns {"status":"healthy"}
- [ ] http://localhost:3000/persona loads without errors
- [ ] Assets exist: mkbhd.wav, mkbhd2.jpg, reference_voice.wav
- [ ] outputs/audio and outputs/video directories exist
- [ ] GPU available (nvidia-smi works)
- [ ] All AI components import successfully
- [ ] GEMINI_API_KEY configured

**All checked?** ✅ **Ready to test!**

---

## 🚀 First Test Command

```bash
# Simple MKBHD test via test script
python backend/test_persona_endpoint.py

# OR via frontend UI
# Open: http://localhost:3000/persona
# Prompt: "Explain the new M4 Mac Mini"
# Persona: MKBHD
# Click: Generate Video
```

**Expected**: Video generates in 3-7 minutes with natural motion and clear face.

---

## 📊 Success Criteria

After first test, verify:

- ✅ Request completes without errors
- ✅ Video file created in outputs/video/
- ✅ Video shows talking face
- ✅ Lip sync matches audio
- ✅ Face is enhanced (GFPGAN)
- ✅ Motion is natural (not too much/little)
- ✅ Intent effects visible (pauses/emphasis)
- ✅ Processing time is reasonable (3-7 min)

**All verified?** 🎉 **Pipeline is working!**

Now test iJustine persona to compare styles.
