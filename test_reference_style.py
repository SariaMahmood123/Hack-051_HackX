"""
Test reference style extraction from video
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai.motion_governor import build_style_from_reference, MEDIAPIPE_AVAILABLE

print("=" * 70)
print("Reference Style Extraction Test")
print("=" * 70)
print()

# Check dependencies
print("Dependencies:")
print(f"  MediaPipe available: {MEDIAPIPE_AVAILABLE}")
if not MEDIAPIPE_AVAILABLE:
    print("  Note: Will use OpenCV fallback (less accurate)")
print()

# Test with a video file
test_video = Path("outputs/video/test_wsl_gpu.mp4")

if not test_video.exists():
    print(f"❌ Test video not found: {test_video}")
    print("Please generate a video first:")
    print("  python test_sadtalker_wsl_gpu.py")
    sys.exit(1)

print(f"Analyzing video: {test_video.name}")
print("This may take 30-60 seconds depending on video length...")
print()

try:
    # Extract style from video
    style = build_style_from_reference(test_video, name="extracted_style")
    
    print("=" * 70)
    print("✓ Style Profile Extracted Successfully!")
    print("=" * 70)
    print()
    print(f"Name: {style.name}")
    print(f"Pose Max (yaw, pitch, roll): {style.pose_max}")
    print(f"Pose Scale: {style.pose_scale}")
    print(f"Expression Strength: {style.expr_strength}")
    print(f"Smoothing: {style.smoothing}")
    print(f"Stillness on Pause: {style.stillness_on_pause}")
    print(f"Nod Rate: {style.nod_rate:.2f}/s")
    print(f"Nod Amplitude: {style.nod_amplitude:.3f}")
    print()
    
    # Save to JSON
    output_path = Path("extracted_style.json")
    style.save(output_path)
    print(f"✓ Style saved to: {output_path}")
    print()
    
    # Test loading
    loaded_style = build_style_from_reference.load(output_path)
    print(f"✓ Style can be loaded back")
    print()
    
    print("=" * 70)
    print("Usage:")
    print("=" * 70)
    print("from ai.motion_governor import StyleProfile")
    print(f"style = StyleProfile.load('{output_path}')")
    print("wrapper.generate(..., motion_style=style)")
    print("=" * 70)
    
except Exception as e:
    print(f"❌ Style extraction failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
