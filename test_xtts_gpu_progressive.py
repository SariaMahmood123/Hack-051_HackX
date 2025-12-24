"""
XTTS GPU Test - Progressive Loading
Load to CPU first, then move to GPU to avoid timeout
"""
import sys
import time
import torch
from pathlib import Path

print("="*60)
print("XTTS v2 GPU Test (Progressive Loading)")
print("="*60)
print()

# Check setup
print("[1/7] System check...")
print(f"CUDA: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")

reference_audio = Path("assets/reference_voice.wav")
if not reference_audio.exists():
    print("[X] Reference not found!")
    sys.exit(1)
print(f"Reference: {reference_audio.name}")
print()

# Import
print("[2/7] Importing TTS...")
from TTS.api import TTS
print("[OK]")
print()

# Load to CPU first
print("[3/7] Loading model to CPU first...")
print("(This avoids timeout issues)")
start = time.time()

try:
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
    load_time = time.time() - start
    print(f"[OK] CPU load: {load_time:.1f}s")
except Exception as e:
    print(f"[X] Failed: {e}")
    sys.exit(1)

print()

# Move to GPU
print("[4/7] Moving model to GPU...")
print("(This transfers ~2GB to VRAM)")
start = time.time()

try:
    # Access the actual model and move it
    if hasattr(tts, 'synthesizer') and hasattr(tts.synthesizer, 'tts_model'):
        device = torch.device('cuda')
        tts.synthesizer.tts_model = tts.synthesizer.tts_model.to(device)
        
        # Also move vocoder if it exists
        if hasattr(tts.synthesizer, 'vocoder') and tts.synthesizer.vocoder is not None:
            if hasattr(tts.synthesizer.vocoder, 'model'):
                tts.synthesizer.vocoder.model = tts.synthesizer.vocoder.model.to(device)
        
        move_time = time.time() - start
        print(f"[OK] GPU transfer: {move_time:.1f}s")
        
        # Verify
        model_device = next(tts.synthesizer.tts_model.parameters()).device
        print(f"[OK] Model device: {model_device}")
    else:
        print("[!] Could not access model for GPU transfer")
        print("[!] Will use CPU mode instead")
except Exception as e:
    print(f"[!] GPU transfer failed: {e}")
    print("[!] Continuing with CPU mode")

print()

# Generate audio
print("[5/7] Generating audio...")
test_text = (
    "Hello! This is a test of XTTS voice cloning. "
    "The model is now running with GPU acceleration for faster processing."
)

output_path = Path("outputs/audio/xtts_progressive_test.wav")
output_path.parent.mkdir(parents=True, exist_ok=True)

start = time.time()
try:
    tts.tts_to_file(
        text=test_text,
        file_path=str(output_path),
        speaker_wav=str(reference_audio),
        language="en"
    )
    synth_time = time.time() - start
    print(f"[OK] Generated in {synth_time:.2f}s")
except Exception as e:
    print(f"[X] Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Verify
print("[6/7] Verifying output...")
if output_path.exists():
    size_kb = output_path.stat().st_size / 1024
    print(f"[OK] File created: {size_kb:.1f} KB")
else:
    print("[X] No output file!")
    sys.exit(1)

print()
print("[7/7] Complete!")
print("="*60)
print("[SUCCESS] Audio Generated!")
print("="*60)
print()
print(f"File: {output_path.absolute()}")
print(f"Size: {size_kb:.1f} KB")
print(f"Time: {synth_time:.2f}s")
print()
print("Play the file to hear the voice-cloned audio!")
