# LUMEN - Quick Start Guide

This guide will help you get LUMEN running in 5 minutes.

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.10+ installed
- ✅ Node.js 18+ installed
- ✅ NVIDIA GPU with CUDA support (RTX 4080 Super recommended)
- ✅ Gemini API key ([Get one here](https://ai.google.dev/))

## 🚀 Quick Start (5 Minutes)

### Step 1: Clone & Setup (2 min)

```bash
# Clone repository
git clone <your-repo-url>
cd LUMEN

# Run setup script
python scripts/setup.py
```

### Step 2: Configure Environment (1 min)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_key_here
```

**Windows:**
```powershell
copy .env.example .env
notepad .env
```

### Step 3: Start Backend (1 min)

```bash
# Install dependencies
pip install -r requirements.txt

# Start backend
python backend/run.py
```

**Or use the quick start script (Windows):**
```powershell
.\start_backend.bat
```

Backend will be available at: **http://localhost:8000**

### Step 4: Start Frontend (1 min)

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: **http://localhost:3000**

### Step 5: Test It! (30 sec)

1. Open http://localhost:3000 in your browser
2. Type a message in the chat
3. See the placeholder response (models not yet loaded)

## 📋 What You Should See

**Backend Terminal:**
```
🚀 Starting LUMEN Backend...
   GPU Available: True
   Models Path: d:\Hack-051_HackX\models
   Outputs Path: d:\Hack-051_HackX\outputs
📁 Mounted static files at /outputs
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Frontend Terminal:**
```
  ▲ Next.js 15.0.0
  - Local:        http://localhost:3000
  - Network:      http://192.168.1.x:3000

✓ Ready in 2.3s
```

## 🧪 Test the API

Open http://localhost:8000/docs to see interactive API documentation.

Or use curl:
```bash
curl http://localhost:8000/health
```

Or run the test script:
```bash
python backend/test_api.py
```

## 📝 Next Steps

Now that LUMEN is running with placeholder responses, you need to:

### 1. Download AI Models

**XTTS v2:**
```python
from TTS.api import TTS
TTS("tts_models/multilingual/multi-dataset/xtts_v2")
```

**SadTalker:**
```bash
cd models
git clone https://github.com/OpenTalker/SadTalker.git sadtalker
cd sadtalker
bash scripts/download_models.sh
```

### 2. Add Reference Assets

Place these files in the `assets/` folder:
- **avatar.jpg** - A clear frontal portrait (512x512+ pixels)
- **reference_voice.wav** - 5-15 second clean audio sample

### 3. Enable Model Integration

Uncomment the TODO sections in:
- `ai/gemini_client.py`
- `ai/xtts_wrapper.py`
- `ai/sadtalker_wrapper.py`
- `backend/routes/generation.py`

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.10+

# Check if port 8000 is available
# Windows: netstat -ano | findstr :8000
# Linux: lsof -i :8000
```

### Frontend won't start
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### GPU not detected
```python
# Test GPU availability
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

### Module import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📚 Additional Resources

- **API Docs**: http://localhost:8000/docs
- **Backend README**: [backend/README.md](backend/README.md)
- **Frontend README**: [frontend/README.md](frontend/README.md)
- **AI Models README**: [ai/README.md](ai/README.md)

## 🎯 Project Status

Current status: **✅ Scaffolding Complete**

- ✅ Backend FastAPI structure
- ✅ Frontend Next.js interface
- ✅ AI model wrappers (scaffolded)
- ⏳ Model integration (TODO)
- ⏳ Asset files (TODO)

## 💡 Tips

1. **Development**: Both servers support hot-reload
2. **Logs**: Check `logs/lumen.log` for backend logs
3. **Outputs**: Generated files are in `outputs/` folder
4. **GPU Memory**: Monitor with `nvidia-smi` in separate terminal

## 🚨 Known Limitations (MVP)

- Turn-based only (no streaming)
- Single persona
- No authentication
- Limited error recovery
- Basic caching only

This is a hackathon MVP - focus is on getting it working, not production-ready!

## 🎉 You're Ready!

LUMEN is now running with full backend scaffolding. Start implementing model integration to make it functional!

Questions? Check the main [README.md](README.md) or open an issue.
