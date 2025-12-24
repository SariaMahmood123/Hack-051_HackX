"""Simple XTTS GPU test"""
import sys
import time
from pathlib import Path

# Disable buffering for immediate output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("XTTS GPU Simple Test", flush=True)
print("="*60, flush=True)
print(flush=True)

# Quick checks
print("[1/4] Checking files...", flush=True)
reference = Path("assets/reference_voice.wav")
if not reference.exists():
    print("ERROR: Reference not found", flush=True)
    sys.exit(1)
print(f"OK: {reference}", flush=True)
print(flush=True)

# Import
print("[2/4] Importing TTS...", flush=True)
try:
    from TTS.api import TTS
    print("OK: TTS imported", flush=True)
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    sys.exit(1)
print(flush=True)

# Load model with GPU
print("[3/4] Loading model to GPU...", flush=True)
print("This takes 2-3 minutes on first run", flush=True)
print("Please wait...", flush=True)
start = time.time()

try:
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
    load_time = time.time() - start
    print(f"OK: Model loaded in {load_time:.1f} seconds", flush=True)
except Exception as e:
    print(f"ERROR: Model load failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
print(flush=True)

# Generate
print("[4/4] Generating audio...", flush=True)
text = "Hello! This is GPU-accelerated XTTS voice cloning in action."
output = Path("outputs/audio/xtts_gpu_simple.wav")
output.parent.mkdir(parents=True, exist_ok=True)

start = time.time()
try:
    tts.tts_to_file(
        text=text,
        file_path=str(output),
        speaker_wav=str(reference),
        language="en"
    )
    synth_time = time.time() - start
    print(f"OK: Audio generated in {synth_time:.2f} seconds", flush=True)
except Exception as e:
    print(f"ERROR: Synthesis failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(flush=True)
print("="*60, flush=True)
print("SUCCESS!", flush=True)
print("="*60, flush=True)
print(f"Output: {output.absolute()}", flush=True)
print(f"Size: {output.stat().st_size / 1024:.1f} KB", flush=True)
print(f"Synthesis time: {synth_time:.2f}s", flush=True)
