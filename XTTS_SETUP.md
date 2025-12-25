# XTTS v2 Setup Guide

## What is XTTS v2?
XTTS v2 is Coqui's text-to-speech model that can clone voices from a short audio sample (5-30 seconds). It supports 13 languages and runs best on GPU.

## Prerequisites
- ✅ Python 3.11 (you have this)
- ✅ CUDA-capable GPU (you have this - RTX 4070)
- ✅ TTS library in requirements.txt (already added)

## Setup Steps

### 1. Install TTS Library
```bash
cd D:\Hack-051_HackX
.\.venv\Scripts\activate
pip install TTS==0.22.0
```

### 2. Test XTTS Installation
```bash
# This will auto-download XTTS v2 model (~2GB)
python -c "from TTS.api import TTS; tts = TTS('tts_models/multilingual/multi-dataset/xtts_v2'); print('✓ XTTS installed')"
```

**First run will download:**
- Model checkpoint (~1.8GB)
- Config files
- Vocoder
- Stored in: `C:\Users\<YourUser>\.local\share\tts\`

### 3. Add Reference Voice Audio

You need a reference audio file (5-30 seconds of clear speech):

**Option A - Use existing audio:**
```bash
# Copy your voice sample to:
D:\Hack-051_HackX\assets\reference_voice.wav
```

**Option B - Record new audio:**
```bash
# Run the provided script:
python scripts/record_reference_audio.py
```

**Option C - Download sample:**
```bash
# Use a sample voice (I'll provide a download script)
python scripts/download_sample_voice.py
```

### 4. Verify Setup
```bash
# Test XTTS with the updated wrapper
python test_xtts.py
```

## Model Details

**XTTS v2 Specs:**
- Size: ~1.8GB
- Languages: en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn
- Speed: ~2-5s for 1 sentence on GPU
- Quality: Near-human voice cloning
- GPU Memory: ~2-4GB VRAM

**Your Hardware:**
- GPU: RTX 4070 (12GB VRAM) ✅ Perfect for XTTS
- CPU: Ryzen 7 5700X ✅ Good fallback
- RAM: Should have 16GB+ for smooth operation

## Configuration

Your `.env` file already has:
```env
XTTS_MODEL_PATH=models/xtts_v2
XTTS_REFERENCE_AUDIO=assets/reference_voice.wav
```

## Usage in Code

```python
from ai.xtts_wrapper import XTTSWrapper

# Initialize (auto-loads model)
xtts = XTTSWrapper()

# Generate speech
audio_path = xtts.synthesize(
    text="Hello! This is a test.",
    reference_audio=Path("assets/reference_voice.wav"),
    output_path=Path("outputs/audio/test.wav"),
    language="en"
)
```

## Troubleshooting

### Issue: Model download fails
```bash
# Manually download:
python -c "from TTS.utils.manage import ModelManager; ModelManager().download_model('tts_models/multilingual/multi-dataset/xtts_v2')"
```

### Issue: CUDA out of memory
```python
# Use CPU instead (slower but works)
xtts = XTTSWrapper(device="cpu")
```

### Issue: Audio quality is poor
- Use higher quality reference audio (16kHz+, clear voice)
- Ensure 5-30 seconds of clean speech
- Avoid background noise/music

### Issue: ImportError for TTS
```bash
pip install --upgrade TTS
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

## Next Steps

After setup completes:
1. ✅ Test XTTS standalone
2. ✅ Integrate into `/api/generate/full` pipeline
3. ✅ Add voice selection UI (optional)
4. ✅ Optimize for your GPU

## Performance Expectations

On your RTX 4070:
- Short text (1 sentence): ~2-3 seconds
- Medium text (1 paragraph): ~5-10 seconds
- Long text (multiple paragraphs): ~15-30 seconds

First run will be slower due to model loading (~5-10s).

## Files to Check

After setup, verify these exist:
- `C:\Users\<User>\.local\share\tts\tts_models--multilingual--multi-dataset--xtts_v2\` (model files)
- `D:\Hack-051_HackX\assets\reference_voice.wav` (your voice sample)
- `D:\Hack-051_HackX\outputs\audio\` (output directory)
