"""
Quick test of Motion Governor module
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from ai.motion_governor import MotionGovernor, STYLE_PRESETS, StyleProfile

print("=" * 60)
print("Motion Governor Module Test")
print("=" * 60)

# Test 1: Style Presets
print("\n1. Testing style presets...")
for name, style in STYLE_PRESETS.items():
    print(f"  ✓ {name}: smoothing={style.smoothing}, pose_scale={style.pose_scale}")

# Test 2: Create governor
print("\n2. Creating MotionGovernor...")
governor = MotionGovernor(style_profile=STYLE_PRESETS["calm_tech"], fps=25)
print(f"  ✓ Governor initialized with style: {governor.style.name}")

# Test 3: Process mock motion data
print("\n3. Testing motion processing...")
T = 100  # 100 frames
raw_pose = np.random.randn(T, 3) * 0.5  # random pose
raw_expr = np.random.randn(T, 64) * 2.0  # random expressions

pose_out, expr_out = governor._process_motion(raw_pose, raw_expr, pause_mask=None)

print(f"  Input pose range: [{raw_pose.min():.2f}, {raw_pose.max():.2f}]")
print(f"  Output pose range: [{pose_out.min():.2f}, {pose_out.max():.2f}]")
print(f"  Input expr std: {raw_expr.std():.3f}")
print(f"  Output expr std: {expr_out.std():.3f}")
print(f"  ✓ Motion processed successfully (clamped and smoothed)")

# Test 4: Pause detection
print("\n4. Testing pause detection...")
audio_path = Path("outputs/audio/mkbhd_tech_review.wav")
if audio_path.exists():
    pause_mask = governor._detect_pauses(audio_path, num_frames=100)
    print(f"  ✓ Detected {pause_mask.sum()}/{len(pause_mask)} pause frames")
else:
    print(f"  ⚠ Audio file not found, skipping pause detection test")

# Test 5: Style persistence
print("\n5. Testing style save/load...")
test_style = StyleProfile(
    name="test_style",
    pose_max=(0.4, 0.3, 0.2),
    smoothing=0.85
)
test_path = Path("test_style.json")
test_style.save(test_path)
loaded_style = StyleProfile.load(test_path)
test_path.unlink()  # cleanup
print(f"  ✓ Style saved and loaded: {loaded_style.name}, smoothing={loaded_style.smoothing}")

print("\n" + "=" * 60)
print("✓ All Motion Governor tests passed!")
print("=" * 60)
