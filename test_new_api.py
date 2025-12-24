"""Test updated XTTS wrapper with new API"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai.xtts_wrapper import XTTSWrapper

print("="*60)
print("Testing XTTS with tts.to(device) API")
print("="*60)
print()

reference = Path("assets/reference_voice.wav")
output = Path("outputs/audio/test_new_api.wav")

print("[1/3] Initializing XTTS (CPU mode)...")
xtts = XTTSWrapper(device="cpu")
print("[OK]")
print()

print("[2/3] Loading model with new API...")
xtts.load_model()
print("[OK]")
print()

print("[3/3] Generating test audio...")
text = "Testing the updated XTTS API without deprecation warnings."
result = xtts.synthesize(
    text=text,
    reference_audio=reference,
    output_path=output,
    language="en"
)
print(f"[OK] Generated: {result}")
print(f"     Size: {result.stat().st_size / 1024:.1f} KB")
print()
print("="*60)
print("[SUCCESS] New API working!")
print("="*60)
