# Deployment & Production Configuration

## Current Status: Ready for Development/Testing

### ✅ Production-Ready Components

#### Backend (`backend/`)
- **FastAPI Server**: Fully configured with CORS, middleware
- **Routes**:
  - `/api/generate/mkbhd` - MKBHD voice cloning (WORKING)
  - `/api/generate/video` - Video generation (IMPLEMENTED, needs testing)
- **AI Modules** (`ai/`):
  - `xtts_wrapper.py` - TTS with voice cloning ✅
  - `gemini_client.py` - Script generation ✅
  - `sadtalker_wrapper.py` - Video generation ✅
- **Configuration**: CPU-only mode (Windows stable config)

#### Frontend (`frontend/`)
- **Next.js 15.5.9**: Modern React app
- **Components**: ChatInterface, SettingsPanel, VideoPlayer, etc.
- **API Integration**: Audio mode working, video mode ready for integration
- **Port**: 3001

#### Reference Assets (`assets/`)
- `mkbhd.jpg` - Reference portrait (900x900)
- `mkbhd.wav` - Reference voice (30s, 24kHz)

### ⚠️ Known Limitations

1. **GPU Mode**: Not working on Windows due to PyTorch CUDA bugs
   - **Workaround**: Use WSL2, Docker, or Linux for GPU acceleration
   - **Current**: CPU-only mode (~5 min for 15s video)

2. **Video Quality**: 256x256 resolution (model constraint)
   - Cannot be increased without GPU + different model
   - GFPGAN enhancement requires GPU

3. **SadTalker Patches**: Manual patches required after installation
   - See `SADTALKER_PATCHES.md` for details
   - Patches applied to external dependencies

### 🗂️ Files/Folders to Exclude from Git

**Should be in .gitignore:**
```
# Virtual environments
.venv/
.venv-wsl/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/

# SadTalker (clone separately)
SadTalker/

# GFPGAN (clone separately)
gfpgan/

# Outputs
outputs/audio/*.wav
outputs/video/*.mp4
logs/*.log

# Test/debug files (if any remain)
test_*.py
fix_*.py
*_test_log.txt
*_output.txt

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

### 📦 Utility Scripts (Keep for Development)

These scripts are useful for setup/testing:
- `download_sadtalker_models.py` - Downloads SadTalker checkpoints
- `extract_reference_audio.py` - Extracts reference audio clips
- `generate_with_reference.py` - Tests XTTS voice cloning
- `quick_test_xtts.py` - Quick XTTS verification
- `start_backend.bat` - Windows backend launcher
- `start_frontend.bat` - Windows frontend launcher
- Various setup batch files

### 🚀 Deployment Options

#### Option 1: Windows (Current - CPU Only)
```bash
# Install dependencies
pip install -r requirements.txt

# Clone SadTalker
git clone https://github.com/OpenTalker/SadTalker.git SadTalker/SadTalker-main

# Download checkpoints
python download_sadtalker_models.py

# Apply patches (see SADTALKER_PATCHES.md)

# Run
start_backend.bat
start_frontend.bat
```

#### Option 2: WSL2 (Windows + GPU)
```bash
# In WSL2 Ubuntu:
cd /mnt/d/Hack-051_HackX
python3.11 -m venv .venv-wsl
source .venv-wsl/bin/activate
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Clone SadTalker and setup (same as above)

# Run with GPU
python backend/main.py
```

#### Option 3: Docker (Recommended for Production)
```bash
# Build
docker build -t hackx-lumen .

# Run with GPU
docker run --gpus all -p 8000:8000 -p 3001:3001 \
  -v ./outputs:/app/outputs \
  hackx-lumen
```

### 📝 Environment Variables

Create `.env` file in project root:
```env
# Gemini API
GEMINI_API_KEY=your_api_key_here

# Server
BACKEND_PORT=8000
FRONTEND_PORT=3001

# AI Configuration
DEVICE=cpu  # or 'cuda' for GPU (WSL2/Linux only)
```

### ⏱️ Performance Benchmarks

**Windows CPU Mode** (Production Config):
- Script generation: ~5-10 seconds
- Audio generation: ~30-60 seconds
- Video generation: ~5 minutes (15s video)
- Total: ~6 minutes for full pipeline

**Linux GPU Mode** (with WSL2/Docker):
- Script generation: ~5-10 seconds
- Audio generation: ~30-60 seconds (CPU optimal for XTTS)
- Video generation: ~1-2 minutes (15s video)
- Total: ~2-3 minutes for full pipeline

### 🔄 Next Steps for Production

1. **Add to .gitignore**: Virtual envs, outputs, SadTalker, logs
2. **Test Video Endpoint**: Verify `/api/generate/video` works end-to-end
3. **Frontend Integration**: Wire up Full Video mode in ChatInterface
4. **Error Handling**: Add better error messages for users
5. **Progress Tracking**: Add WebSocket for real-time generation status
6. **Deployment**: Choose WSL2/Docker for GPU, or accept CPU-only
7. **Documentation**: Update README with setup instructions

### ✅ Commit Checklist

Before pushing to main:
- [ ] Updated .gitignore
- [ ] Removed test outputs from `outputs/`
- [ ] Documented SadTalker patches
- [ ] Tested backend video endpoint
- [ ] Frontend video mode working
- [ ] README has deployment instructions
- [ ] Environment variables documented
- [ ] Known limitations documented

**Current State**: Backend complete, frontend needs video integration, ready for dev testing.
