# Reference Style Extraction

Extract motion style profiles from existing videos to replicate their animation characteristics.

## Overview

The `build_style_from_reference()` function analyzes a video to extract head pose statistics and automatically generates a StyleProfile that matches the reference motion characteristics.

## Use Cases

1. **Replicate existing avatar style** - Match the motion of a specific video/avatar
2. **Learn from human videos** - Extract natural motion patterns from recorded humans
3. **Create brand-consistent styles** - Analyze brand videos to maintain consistency
4. **A/B test styles** - Extract from multiple references and compare

## Requirements

### Method 1: MediaPipe (Recommended - Most Accurate)
```bash
pip install mediapipe
```
- **Pros**: Accurate 3D face mesh, reliable pose estimation
- **Cons**: Requires additional dependency (~50MB)

### Method 2: OpenCV Fallback (Built-in)
- **Pros**: No additional dependencies, always available
- **Cons**: Less accurate pose estimation (approximates from face position)

## Basic Usage

```python
from pathlib import Path
from ai.motion_governor import build_style_from_reference
from ai.sadtalker_wrapper import SadTalkerWrapper

# Extract style from reference video
reference_video = Path("reference.mp4")
custom_style = build_style_from_reference(reference_video, name="my_style")

# Use extracted style
wrapper = SadTalkerWrapper(device='cuda')
result = wrapper.generate(
    audio_path="audio.wav",
    reference_image="face.jpg",
    output_path="output.mp4",
    motion_style=custom_style  # Use extracted style
)
```

## Command Line Testing

```bash
# Test extraction on existing video
python test_reference_style.py
```

This will:
1. Load `outputs/video/test_wsl_gpu.mp4`
2. Extract pose statistics
3. Generate `extracted_style.json`
4. Show usage instructions

## Extraction Process

### 1. Video Loading
- Opens video with OpenCV
- Extracts FPS and frame count
- Samples frames (every 3-5 frames for speed)

### 2. Pose Detection

**MediaPipe Method** (if available):
- Uses Face Mesh to detect 468 facial landmarks
- Extracts key points: nose, chin, eyes, mouth corners
- Computes yaw/pitch/roll from landmark geometry
- ~300-500ms per frame on CPU, very accurate

**OpenCV Fallback**:
- Uses Haar Cascade face detector
- Tracks face position and size over time
- Approximates pose from face movement
- ~50-100ms per frame on CPU, less accurate but fast

### 3. Statistics Computation

Analyzes extracted pose data:
- **Standard deviation** - Motion variance (how much movement)
- **Maximum angles** - Range of motion
- **Nod detection** - Pitch direction changes
- **Motion energy** - Overall activity level

### 4. Style Parameter Derivation

Automatically computes:

```python
# Pose constraints
pose_max = (
    95th_percentile(|yaw|),
    95th_percentile(|pitch|),
    95th_percentile(|roll|)
)

# Pose scaling (based on variance)
pose_scale = (
    min(1.0, yaw_std / 0.3 * 0.8),
    min(1.0, pitch_std / 0.2 * 0.7),
    min(1.0, roll_std / 0.15 * 0.6)
)

# Motion style classification
if total_motion < 0.3:
    # Very calm/static
    smoothing = 0.85
    stillness = 0.90
    expr_strength = 0.6
elif total_motion < 0.6:
    # Moderate motion
    smoothing = 0.70
    stillness = 0.75
    expr_strength = 0.8
else:
    # Dynamic/energetic
    smoothing = 0.60
    stillness = 0.60
    expr_strength = 1.0

# Nod rate detection
nod_rate = pitch_sign_changes / video_duration
nod_amplitude = pitch_std * 0.5
```

## Example Output

```
[MotionGovernor] Building style profile from reference: demo.mp4
[MotionGovernor] Using MediaPipe for pose extraction...
[MotionGovernor] Video: 250 frames at 25.0 fps
[MotionGovernor] Processed 100/250 frames...
[MotionGovernor] Processed 200/250 frames...
[MotionGovernor] Extracted pose from 83 frames
[MotionGovernor] Pose statistics:
  Yaw:   std=0.234, max=0.512
  Pitch: std=0.187, max=0.423
  Roll:  std=0.091, max=0.198
[MotionGovernor] Derived style parameters:
  pose_max: (0.487, 0.401, 0.195)
  pose_scale: (0.624, 0.655, 0.364)
  smoothing: 0.7
  nod_rate: 0.32/s

✓ Style Profile Extracted Successfully!

Name: demo_style
Pose Max (yaw, pitch, roll): (0.487, 0.401, 0.195)
Pose Scale: (0.624, 0.655, 0.364)
Expression Strength: 0.8
Smoothing: 0.7
Stillness on Pause: 0.75
Nod Rate: 0.32/s
Nod Amplitude: 0.094
```

## Saving and Loading

```python
# Save extracted style
style.save(Path("my_style.json"))

# Load later
from ai.motion_governor import StyleProfile
loaded_style = StyleProfile.load(Path("my_style.json"))

# Use with wrapper
wrapper.generate(..., motion_style=loaded_style)
```

## Advanced Usage

### Extract from Multiple References

```python
from ai.motion_governor import build_style_from_reference
from pathlib import Path
import numpy as np

# Extract from multiple videos
styles = []
for video in Path("references/").glob("*.mp4"):
    style = build_style_from_reference(video)
    styles.append(style)

# Average the parameters (simple ensemble)
avg_smoothing = np.mean([s.smoothing for s in styles])
avg_pose_scale = tuple(np.mean([s.pose_scale[i] for s in styles], axis=0) 
                       for i in range(3))

# Create ensemble style
ensemble_style = StyleProfile(
    name="ensemble",
    pose_scale=avg_pose_scale,
    smoothing=avg_smoothing,
    # ... other averaged parameters
)
```

### Fine-tune Extracted Style

```python
# Extract base style
style = build_style_from_reference(Path("reference.mp4"))

# Manual adjustments
style.smoothing = 0.85  # More smoothing than original
style.expr_strength = 0.7  # Reduce expression intensity
style.stillness_on_pause = 0.90  # More stillness

# Save adjusted version
style.name = "reference_adjusted"
style.save(Path("reference_adjusted.json"))
```

## Video Requirements

For best results:
- **Duration**: 10-30 seconds (enough samples, not too long)
- **Face visibility**: Clear, frontal face throughout
- **Quality**: Good lighting, minimal blur
- **Content**: Representative of desired motion style
- **Format**: Any common format (MP4, AVI, MOV, etc.)

Poor results if:
- ❌ Face frequently occluded or off-screen
- ❌ Extreme close-ups (face too large)
- ❌ Very low resolution (<480p)
- ❌ Rapid cuts/scene changes

## Performance

Extraction speed (typical 10-second video at 25fps):

| Method | Time | Accuracy |
|--------|------|----------|
| MediaPipe | 15-30s | High ⭐⭐⭐⭐⭐ |
| OpenCV | 5-10s | Moderate ⭐⭐⭐ |

Processing is CPU-bound (doesn't require GPU).

## Troubleshooting

### "Insufficient face detections"
- Video doesn't contain clear faces
- Try different video with better face visibility
- Check video plays correctly in media player

### "MediaPipe extraction failed, trying fallback"
- MediaPipe installed but encountering errors
- Fallback to OpenCV automatically
- Consider reinstalling: `pip install --upgrade mediapipe`

### Extracted style too energetic/calm
Reference video characteristics determine output. To adjust:
```python
style = build_style_from_reference(video)
# Manual adjustment
style.smoothing = 0.80  # Increase smoothing
style.pose_scale = tuple(s * 0.8 for s in style.pose_scale)  # Reduce amplitude
```

### "Can't estimate roll reliably" (OpenCV fallback)
OpenCV fallback can't detect head tilt (roll). Default value used.
Install MediaPipe for full 3D pose: `pip install mediapipe`

## Comparison: Preset vs Reference

| Aspect | Preset Styles | Reference Extraction |
|--------|---------------|---------------------|
| Setup | Instant | 10-30 seconds |
| Customization | Predefined | Video-specific |
| Accuracy | Generic | Tailored |
| Requirements | None | Reference video |
| Use Case | Quick start | Match specific style |

## Future Enhancements

Planned improvements:
- [ ] Expression coefficient extraction (beyond pose)
- [ ] Multi-face support (average ensemble)
- [ ] Temporal consistency analysis
- [ ] GPU-accelerated extraction
- [ ] Interactive style tuning GUI

## API Reference

### build_style_from_reference()

```python
def build_style_from_reference(
    video_path: Path,
    name: str = "reference"
) -> StyleProfile
```

**Parameters:**
- `video_path` (Path): Path to reference video file
- `name` (str): Name for generated style profile

**Returns:**
- `StyleProfile`: Extracted style configuration

**Raises:**
- `FileNotFoundError`: Video file doesn't exist
- `RuntimeError`: Pose extraction failed (insufficient data)

**Example:**
```python
style = build_style_from_reference(
    Path("demo.mp4"),
    name="demo_style"
)
```

## Integration with SadTalker

Full workflow:
```python
from pathlib import Path
from ai.motion_governor import build_style_from_reference
from ai.sadtalker_wrapper import SadTalkerWrapper

# 1. Extract style from reference
ref_style = build_style_from_reference(
    Path("reference.mp4"),
    name="custom"
)

# 2. Optional: Save for reuse
ref_style.save(Path("custom_style.json"))

# 3. Generate video with custom style
wrapper = SadTalkerWrapper(device='cuda')
result = wrapper.generate(
    audio_path="speech.wav",
    reference_image="portrait.jpg",
    output_path="video.mp4",
    enable_motion_governor=True,
    motion_style=ref_style  # Use extracted style
)

print(f"Generated: {result}")
```

## See Also

- [MOTION_GOVERNOR.md](MOTION_GOVERNOR.md) - Main Motion Governor documentation
- [test_reference_style.py](test_reference_style.py) - Test script
- [ai/motion_governor.py](ai/motion_governor.py) - Source code
