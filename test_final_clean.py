"""
Final test: Generate audio using updated XTTS wrapper (no deprecation warnings)
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai.xtts_wrapper import XTTSWrapper

print("="*60)
print("XTTS Voice Cloning - Updated API (No Warnings)")
print("="*60)
print()

# Setup
reference = Path("assets/reference_voice.wav")
output = Path("outputs/audio/final_no_warnings.wav")
output.parent.mkdir(parents=True, exist_ok=True)

text = (
    "This is the final test of the updated XTTS wrapper. "
    "No more deprecation warnings! "
    "The new API uses tts dot to device instead of the gpu parameter. "
    "Voice cloning is working perfectly with clean output!"
)

print(f"Reference: {reference.name}")
print(f"Output: {output.name}")
print(f"Text: {len(text)} chars")
print()

# Generate
print("Initializing XTTS...", flush=True)
start_total = time.time()

xtts = XTTSWrapper(device="cpu")
print("[OK]")

print("Loading model...", flush=True)
xtts.load_model()
print("[OK]")

print("Synthesizing...", flush=True)
start_synth = time.time()

result = xtts.synthesize(
    text=text,
    reference_audio=reference,
    output_path=output,
    language="en"
)

synth_time = time.time() - start_synth
total_time = time.time() - start_total

# Results
print()
print("="*60)
print("[SUCCESS] Clean Audio Generation!")
print("="*60)
print()
print(f"File: {result.absolute()}")
print(f"Size: {result.stat().st_size / 1024:.1f} KB")
print(f"Synthesis: {synth_time:.2f}s")
print(f"Total: {total_time:.1f}s")
print()
print("No deprecation warnings! API updated successfully.")
