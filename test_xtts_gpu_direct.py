"""
Direct XTTS GPU test using TTS API
Bypasses wrapper for more control
"""
import sys
import time
import torch
from pathlib import Path

print("="*60)
print("XTTS v2 Direct GPU Test")
print("="*60)
print()

# Check CUDA
print("[1/6] Checking CUDA...")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA Version: {torch.version.cuda}")
else:
    print("[X] CUDA not available!")
    sys.exit(1)

print()

# Check reference audio
reference_audio = Path("assets/reference_voice.wav")
if not reference_audio.exists():
    print("[X] Reference audio not found!")
    sys.exit(1)

print(f"[OK] Reference: {reference_audio}")
print()

# Import TTS
print("[2/6] Importing TTS...")
try:
    from TTS.api import TTS
    print("[OK] TTS imported")
except Exception as e:
    print(f"[X] Import failed: {e}")
    sys.exit(1)

print()

# Initialize model
print("[3/6] Initializing TTS (GPU=True)...")
print("This will load the model to VRAM...")
start = time.time()

try:
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
    load_time = time.time() - start
    print(f"[OK] Model initialized in {load_time:.1f}s")
except Exception as e:
    print(f"[X] Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Check if model is on GPU
print("[4/6] Verifying GPU placement...")
try:
    # Get the actual device
    if hasattr(tts, 'synthesizer') and hasattr(tts.synthesizer, 'tts_model'):
        model_device = next(tts.synthesizer.tts_model.parameters()).device
        print(f"[OK] Model on: {model_device}")
    else:
        print("[?] Unable to verify device")
except Exception as e:
    print(f"[?] Could not check device: {e}")

print()

# Generate audio
print("[5/6] Generating audio with voice cloning...")
test_text = (
    "Hello! This is a GPU-accelerated test of XTTS voice synthesis. "
    "The model is running on the graphics card for faster processing. "
    "This should be significantly quicker than CPU mode."
)

output_path = Path("outputs/audio/xtts_gpu_direct.wav")
output_path.parent.mkdir(parents=True, exist_ok=True)

start = time.time()
try:
    # Direct synthesis
    tts.tts_to_file(
        text=test_text,
        file_path=str(output_path),
        speaker_wav=str(reference_audio),
        language="en"
    )
    synth_time = time.time() - start
    print(f"[OK] Synthesis completed in {synth_time:.2f}s")
except Exception as e:
    print(f"[X] Synthesis failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Verify output
print("[6/6] Verifying output...")
if output_path.exists():
    size_kb = output_path.stat().st_size / 1024
    print(f"[OK] Output file created")
    print()
    print("="*60)
    print("[SUCCESS] GPU Audio Generation Complete!")
    print("="*60)
    print()
    print(f"File: {output_path.absolute()}")
    print(f"Size: {size_kb:.1f} KB")
    print(f"Processing Time: {synth_time:.2f} seconds")
    print()
    print("Play the audio to verify voice cloning quality!")
else:
    print("[X] Output file not created!")
    sys.exit(1)
