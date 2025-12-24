"""Test XTTS with GPU (auto-detected)"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai.xtts_wrapper import XTTSWrapper

print("="*60)
print("Testing XTTS GPU Mode")
print("="*60)
print()

reference = Path("assets/reference_voice.wav")
output = Path("outputs/audio/gpu_test.wav")

print("Initializing XTTS...")
xtts = XTTSWrapper()
print(f"Device: {xtts.device}")
print()

print("Loading model...")
xtts.load_model()
print("[OK]")
print()

print("Generating audio...")
text = "Testing GPU acceleration with XTTS voice cloning."

try:
    result = xtts.synthesize(
        text=text,
        reference_audio=reference,
        output_path=output,
        language="en"
    )
    print(f"[SUCCESS] Generated: {result}")
    print(f"Size: {result.stat().st_size / 1024:.1f} KB")
except Exception as e:
    print(f"[ERROR] Synthesis failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
