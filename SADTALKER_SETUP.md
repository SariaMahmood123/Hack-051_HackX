# SadTalker Setup Guide

## Overview
SadTalker generates realistic talking-head videos from audio + a single portrait image. We'll use it to animate MKBHD's face with the generated audio.

## Prerequisites
✅ Already have:
- CUDA-capable GPU (RTX 4080 SUPER)
- Python 3.11
- Working virtual environment

## Step 1: Install SadTalker

### Option A: Install from Official Repo (Recommended)

```powershell
# Navigate to project root
cd D:\Hack-051_HackX

# Clone SadTalker repository
git clone https://github.com/OpenTalker/SadTalker.git

# Install SadTalker dependencies
cd SadTalker
pip install -r requirements.txt

# Download pre-trained models (required, ~2-3GB)
python scripts/download_models.py
```

### Option B: Install as Package (Simpler but less control)

```powershell
cd D:\Hack-051_HackX
pip install TTS sadtalker
```

**Note**: Option A gives you more control and is recommended for this project.

## Step 2: Get MKBHD Reference Image

You need a high-quality portrait image of MKBHD:

### Requirements:
- Clear frontal face
- Good lighting
- Neutral expression works best
- Recommended: 512x512 or higher resolution
- Format: JPG or PNG

### Where to get it:
1. **Screenshot from YouTube video** - Pause a clear frame
2. **Official press photo** - From his website/Twitter
3. **AI-generated headshot** - If needed

### Action Required:
📸 **YOU NEED TO PROVIDE**: Save MKBHD's portrait image to:
```
D:\Hack-051_HackX\assets\mkbhd.jpg
```

## Step 3: Test SadTalker Installation

Create a test script:

```python
# test_sadtalker.py
import sys
sys.path.append('SadTalker')  # If using Option A

from sadtalker.inference import SadTalker

# Test basic loading
model = SadTalker(checkpoint_path='SadTalker/checkpoints', device='cuda')
print("✅ SadTalker loaded successfully!")
```

Run it:
```powershell
python test_sadtalker.py
```

## Step 4: Verify Required Files

After installation, check you have:

```
D:\Hack-051_HackX\
├── SadTalker/                    # Cloned repo
│   ├── checkpoints/              # Downloaded models
│   │   ├── mapping_00109-model.pth.tar
│   │   ├── mapping_00229-model.pth.tar
│   │   ├── SadTalker_V0.0.2_256.safetensors
│   │   └── ...
│   └── src/
├── assets/
│   ├── mkbhd.wav                # ✅ Already have
│   └── mkbhd.jpg                # ❌ NEED TO ADD
└── ai/
    └── sadtalker_wrapper.py     # Will implement next
```

## Expected Issues & Solutions

### Issue 1: CUDA Out of Memory
**Solution**: SadTalker uses ~4-6GB VRAM. Your RTX 4080 SUPER (16GB) should be fine.

### Issue 2: Missing Dependencies
**Solution**: 
```powershell
pip install face-alignment resampy pydub yacs
```

### Issue 3: Model Download Fails
**Solution**: Manually download from:
- https://github.com/OpenTalker/SadTalker/releases
- Place in `SadTalker/checkpoints/`

## Next Steps (I'll handle)

Once you complete Steps 1-2, I will:
1. ✅ Implement the actual SadTalker wrapper code
2. ✅ Uncomment and activate the video generation routes
3. ✅ Update frontend to support video mode
4. ✅ Create end-to-end pipeline: Prompt → Script → Audio → Video

## What You Need To Do Now

### STEP 1: Install SadTalker
```powershell
cd D:\Hack-051_HackX
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker
pip install -r requirements.txt
python scripts/download_models.py
```

### STEP 2: Get MKBHD Image
- Find a clear portrait of MKBHD (frontal face, good lighting)
- Save as: `D:\Hack-051_HackX\assets\mkbhd.jpg`

### STEP 3: Test it
```powershell
cd D:\Hack-051_HackX
python test_sadtalker.py  # I'll create this script
```

## Let me know when you've completed these steps!

Then I'll implement the wrapper and integrate it into the full pipeline.
