# Quick Start Guide - Intent-Aware Pipeline

## Prerequisites

- WSL2 with Ubuntu 22.04
- Python 3.8+
- CUDA 12.1 (for SadTalker)
- Required packages: `pip install -r requirements.txt`

## Basic Usage

### 1. Simple Generation (Plain Text)

```python
from ai.pipeline import PipelineManager
from pathlib import Path

pipeline = PipelineManager(
    gemini_api_key="your-key",
    reference_audio=Path("assets/reference_audio.wav"),
    reference_image=Path("assets/reference_image.jpg"),
    enable_intent=False,  # Plain text mode
    enable_governor=False  # No motion control
)

result = await pipeline.generate_full_response(
    prompt="Explain how GPUs work"
)

print(f"Video: {result['video_path']}")
```

### 2. Intent-Aware Generation (Recommended)

```python
pipeline = PipelineManager(
    gemini_api_key="your-key",
    reference_audio=Path("assets/reference_audio.wav"),
    reference_image=Path("assets/reference_image.jpg"),
    enable_intent=True,  # Script intent enabled
    enable_governor=True,  # Motion control enabled
    motion_style="calm_tech"
)

result = await pipeline.generate_full_response(
    prompt="Today I want to talk about GPUs. They are incredibly powerful."
)

# Access structured data
print(f"Segments: {len(result['script_intent']['segments'])}")
print(f"Video: {result['video_path']}")
```

### 3. Custom Motion Style

```python
from ai.motion_governor import StyleProfile

custom_style = StyleProfile(
    name="my_style",
    pose_max=(0.3, 0.2, 0.2),
    pose_scale=(0.6, 0.5, 0.4),
    smoothing=0.75,
    stillness_on_pause=0.90
)

result = await pipeline.generate_full_response(
    prompt="...",
    motion_style=custom_style  # Use custom style
)
```

### 4. Extract Style from Video

```python
from ai.motion_governor import build_style_from_reference

# Extract from existing video
ref_style = build_style_from_reference(Path("reference.mp4"))
ref_style.save(Path("my_style.json"))

# Use extracted style
result = await pipeline.generate_full_response(
    prompt="...",
    motion_style=ref_style
)
```

## Testing

### Run Integration Tests

```bash
# All tests
wsl bash -c "cd /mnt/d/Hack-051_HackX && source .venv-wsl/bin/activate && python test_integration_pipeline.py"

# Individual test
wsl bash -c "cd /mnt/d/Hack-051_HackX && source .venv-wsl/bin/activate && python -c 'import asyncio; from test_integration_pipeline import test_full_intent; asyncio.run(test_full_intent())'"
```

## Configuration Options

### Pipeline Parameters

- `enable_intent`: Enable script intent (pause, emphasis)
- `enable_governor`: Enable motion control
- `motion_style`: "calm_tech", "energetic", "lecturer", or StyleProfile

### Style Presets

**calm_tech** (default):
- Low motion, high smoothing
- Good for technical content
- Minimal fidgeting

**energetic**:
- Higher motion, lower smoothing
- Good for excited/dynamic content
- More expression

**lecturer**:
- Moderate motion, nods enabled
- Good for educational content
- Subtle sentence-end nods

## Architecture Overview

```
User Prompt
   ↓
Gemini (structured intent)
   ↓ ScriptIntent
XTTS (segmented audio)
   ↓ IntentTimingMap
SadTalker (3 stages)
   1. generate_coeffs()
   2. govern_coeffs() ← combines audio + script intent
   3. render_video()
   ↓
Final Video
```

## Debugging

### Enable Detailed Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Intent Files

```bash
# Script intent
cat outputs/intent/<request_id>_script.json

# Timing map
cat outputs/intent/<request_id>_timing.json
```

### Check Motion Governor

```bash
wsl bash -c "cd /mnt/d/Hack-051_HackX && source .venv-wsl/bin/activate && python check_governor.py"
```

## Common Issues

### Intent Not Working

**Symptom**: No script_intent in output  
**Fix**: Check Gemini API key, verify enable_intent=True

### Governor Not Applied

**Symptom**: Jittery motion, no stillness on pauses  
**Fix**: Verify enable_governor=True, check logs for fallback warnings

### Audio Timing Mismatch

**Symptom**: Motion doesn't match pauses  
**Fix**: Check fps parameter matches (default: 25)

## Performance Tips

1. **CPU for XTTS**: Keep TTS on CPU for quality (configured by default)
2. **GPU for SadTalker**: Ensure CUDA available (check with `torch.cuda.is_available()`)
3. **Caching**: Reuse reference audio/image to avoid reloading

## Files Modified in Refactor

- **NEW**: `ai/script_intent.py` - Intent contract
- **MODIFIED**: `ai/gemini_client.py` - Added `generate_with_intent()`
- **MODIFIED**: `ai/xtts_wrapper.py` - Added `synthesize_with_intent()`
- **MODIFIED**: `ai/sadtalker_wrapper.py` - 3-stage architecture
- **MODIFIED**: `ai/motion_governor.py` - Intent fusion
- **MODIFIED**: `ai/pipeline.py` - End-to-end orchestration
- **NEW**: `test_integration_pipeline.py` - Test suite
- **NEW**: `ARCHITECTURE.md` - System documentation

## Next Steps

1. Run integration tests to verify setup
2. Try different motion styles
3. Extract custom styles from reference videos
4. Enable GFPGAN for quality boost
5. Read ARCHITECTURE.md for deep dive

## Support

For issues or questions:
1. Check logs in outputs/
2. Review ARCHITECTURE.md
3. Run test suite to isolate problem
4. Check GPU memory with `nvidia-smi`
