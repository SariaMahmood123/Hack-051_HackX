# Motion Governor

Unified motion control layer for SadTalker that improves pose and expression quality.

## Overview

The Motion Governor acts as a **deterministic constraint layer** on top of SadTalker's generated motion/expression coefficients. It addresses common issues like:
- **Overacting** - Excessive facial expressions
- **Jitter** - Frame-to-frame instability in head pose
- **Fidgeting** - Unwanted micro-motion during pauses

**Important**: Motion Governor does NOT touch lip-sync/mouth movement - only head pose and upper-face expressions.

## Architecture

```
Input → SadTalker → Raw Coefficients → Motion Governor → Final Coefficients → Render → Video
```

### Pipeline Flow

1. **SadTalker generates** raw motion/expression coefficients per frame
2. **Motion Governor applies** deterministic constraints:
   - Clamping (safety net)
   - Intent gating (audio/script aware)
   - Style scaling (preset or reference-based)
   - Temporal smoothing (removes jitter)
   - Pause stillness (reduces fidgeting)
3. **Render stage** creates final video with improved motion

## Key Features

### 1. Clamping (Safety Net)
Prevents extreme pose angles and expression intensities that look unnatural.

### 2. Intent Gating (Audio-Aware)
- **Detects pauses** using audio analysis (RMS energy)
- **Reduces motion** during silence (intent_gate ≈ 0.05)
- **Allows motion** during speech (intent_gate ≈ 0.8)
- Future: explicit emphasis detection for high-energy segments

### 3. Style Scaling
Applies preset style profiles to control motion characteristics:
- **calm_tech** - Subtle motion, high stability (default)
- **energetic** - More dynamic, moderate smoothing
- **lecturer** - Professional presentation style

### 4. Temporal Smoothing (IIR Filter)
```python
out[t] = alpha * candidate[t] + (1-alpha) * out[t-1]
```
Higher smoothing values remove jitter but may feel "laggy" if too high.

### 5. Pause Stillness
During detected silence:
```python
pose *= (1 - stillness_strength)  # 0.85 = nearly frozen
expr *= (1 - stillness_expr_strength)  # 0.90 = minimal expression
```

## Usage

### Basic Integration (SadTalker Wrapper)

```python
from ai.sadtalker_wrapper import SadTalkerWrapper

wrapper = SadTalkerWrapper(device='cuda')

# Generate with motion control (default: calm_tech style)
result = wrapper.generate(
    audio_path="audio.wav",
    reference_image="face.jpg",
    output_path="output.mp4",
    enable_motion_governor=True,  # Enable motion control
    motion_style="calm_tech"  # or "energetic", "lecturer"
)
```

### A/B Testing

```bash
# Compare baseline vs. governed output
python test_motion_governor.py
```

This generates:
- `outputs/video/test_baseline.mp4` - No motion control
- `outputs/video/test_governed.mp4` - With motion control

Compare videos to evaluate improvements.

### Direct Use (Advanced)

```python
from ai.motion_governor import MotionGovernor, STYLE_PRESETS
from pathlib import Path

# Create governor
governor = MotionGovernor(
    style_profile=STYLE_PRESETS["calm_tech"],
    fps=25
)

# Process coefficient file
coeff_path = Path("coefficients.mat")
governed_path = governor.process_coeff_file(
    coeff_path=coeff_path,
    audio_path=Path("audio.wav")  # For pause detection
)
```

## Style Profiles

### calm_tech (Default)
Best for: Tech demos, product reviews, calm explanations
- Pose scale: (0.5, 0.4, 0.3) - reduced amplitude
- Expression strength: 0.6 - subtle
- Smoothing: 0.80 - high stability
- Pause stillness: 0.90 - nearly frozen during silence

### energetic
Best for: Dynamic presentations, enthusiasm
- Pose scale: (0.9, 0.8, 0.7) - near full range
- Expression strength: 1.1 - enhanced
- Smoothing: 0.60 - moderate stability
- Pause stillness: 0.60 - some motion during pauses

### lecturer
Best for: Academic presentations, professional talks
- Pose scale: (0.7, 0.6, 0.5) - moderate
- Expression strength: 0.8 - professional
- Smoothing: 0.70 - good stability
- Pause stillness: 0.75 - reduced fidgeting

### Custom Styles

Create custom styles:

```python
from ai.motion_governor import StyleProfile

custom_style = StyleProfile(
    name="custom",
    pose_max=(0.35, 0.25, 0.2),  # max angles (radians)
    pose_scale=(0.6, 0.5, 0.4),  # scale factors
    expr_strength=0.7,           # expression intensity
    smoothing=0.75,              # 0..1 (higher = smoother)
    stillness_on_pause=0.85,     # pose freeze during silence
    stillness_expr_on_pause=0.90 # expression freeze
)

# Save for reuse
custom_style.save(Path("my_style.json"))

# Load later
loaded_style = StyleProfile.load(Path("my_style.json"))
```

## Technical Details

### Coefficient Format
SadTalker uses 3DMM coefficients (typically .mat files):
- **Shape**: [T, dims] where T = number of frames
- **Structure**: [id(80), exp(64), tex(80), angles(3), ...]
- **Controlled**: 
  - `exp` (64-dim) - Expression coefficients
  - `angles` (3-dim) - Yaw, pitch, roll

### Pause Detection
Uses librosa to compute short-time RMS energy:
1. Load audio
2. Compute RMS with hop_length = sample_rate / fps
3. Threshold = 20th percentile * 1.5
4. Map silence frames to video frames

### Graceful Fallbacks
- If Motion Governor fails → uses original coefficients
- If librosa unavailable → no pause detection
- If coefficient format unexpected → returns unchanged

## Future Enhancements

### Reference Style Extraction (Stub)
```python
# Not yet implemented
from ai.motion_governor import build_style_from_reference

style = build_style_from_reference(Path("reference_video.mp4"))
# Would analyze reference pose statistics and derive scaling factors
```

### Script-Aware Intent Gating
Current: Audio-based pause detection
Future: Explicit sentence boundaries, emphasis markers from script

### Sentence-End Nods
Optional subtle pitch nod at sentence boundaries (configurable per style).

## Troubleshooting

### Governor not applying
Check logs for:
```
[MotionGovernor] Governor enabled: True
[MotionGovernor] Initialized with style 'calm_tech'
```

If you see:
```
[SadTalker] Motion Governor requested but not available
```
Check import path and ensure `ai/motion_governor.py` exists.

### Still seeing jitter
Try increasing smoothing:
```python
style.smoothing = 0.90  # Higher = more smoothing
```

### Motion too restricted
Try energetic style or reduce stillness:
```python
motion_style="energetic"
# Or customize:
style.stillness_on_pause = 0.50  # Allow more motion
```

## Performance

Motion Governor adds **minimal overhead** (~0.5-1 second):
- Coefficient loading/saving: <0.3s
- Motion processing: <0.5s for 150 frames
- Audio analysis: <0.2s with librosa

Total generation time remains ~2-3 minutes (dominated by rendering).

## Module Tests

Run unit tests:
```bash
python test_motion_governor_module.py
```

Expected output:
- ✓ All style presets loaded
- ✓ Governor initialization
- ✓ Motion processing (clamping + smoothing)
- ✓ Pause detection (if audio available)
- ✓ Style save/load

## Integration Points

### In SadTalker Wrapper
File: `ai/sadtalker_wrapper.py`

Location: After audio-to-coefficient generation, before rendering:
```python
coeff_path = audio_to_coeff.generate(batch, save_dir, 0, None)

# Motion Governor intercepts here
if enable_motion_governor:
    governor = MotionGovernor(style_profile, fps)
    coeff_path = governor.process_coeff_file(coeff_path, audio_path)

# Continue to rendering
data = get_facerender_data(coeff_path, ...)
```

## FAQ

**Q: Does this affect lip sync quality?**  
A: No. Mouth/lip coefficients are pass-through, only pose and upper-face expressions are controlled.

**Q: Can I disable it?**  
A: Yes, set `enable_motion_governor=False` in generate().

**Q: Does it work on CPU?**  
A: Yes, Motion Governor itself runs on CPU and is very fast. GPU is still needed for SadTalker rendering.

**Q: Can I use multiple styles in one video?**  
A: Not currently. Style is applied uniformly across the entire video.

## Citation

If you use Motion Governor in research:
```
Motion Governor: Deterministic constraint layer for improved 3D avatar motion quality
Built on top of SadTalker (Zhang et al., 2023)
```
