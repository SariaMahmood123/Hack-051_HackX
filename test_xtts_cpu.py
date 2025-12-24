"""Quick XTTS test with CPU mode"""
import sys
from pathlib import Path
import os

# Force CPU mode for faster testing
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

sys.path.insert(0, str(Path(__file__).parent))

from ai.xtts_wrapper import XTTSWrapper

print("=" * 60)
print("Testing XTTS v2 (CPU Mode)")
print("=" * 60)
print()

reference_audio = Path("assets/reference_voice.wav")

print("[1/3] Initializing XTTS (CPU mode)...")
xtts = XTTSWrapper(device="cpu")
print("[OK] Created")
print()

print("[2/3] Loading model...")
xtts.load_model()
print("[OK] Model loaded")
print()

print("[3/3] Synthesizing test audio...")
print("(This will be slow on CPU - 30-60 seconds)")
test_text = "Hello! This is a test."
output_path = Path("outputs/audio/xtts_test_cpu.wav")

result = xtts.synthesize(
    text=test_text,
    reference_audio=reference_audio,
    output_path=output_path,
    language="en"
)

print(f"[OK] Generated: {result}")
print(f"Size: {result.stat().st_size / 1024:.1f} KB")
print()
print("=" * 60)
print("[SUCCESS] XTTS works! Now try GPU mode.")
print("=" * 60)
