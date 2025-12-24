"""
Test XTTS v2 with GPU acceleration
Generates audio using the reference voice
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai.xtts_wrapper import XTTSWrapper

def test_gpu():
    print("="*60)
    print("XTTS v2 GPU Test")
    print("="*60)
    print()
    
    # Check reference audio
    reference_audio = Path("assets/reference_voice.wav")
    if not reference_audio.exists():
        print("[X] Reference audio not found!")
        return False
    
    print(f"[OK] Reference: {reference_audio}")
    print()
    
    # Initialize with GPU
    print("[1/3] Initializing XTTS with GPU...")
    try:
        xtts = XTTSWrapper(device="cuda")
        print("[OK] XTTS wrapper created (GPU mode)")
    except Exception as e:
        print(f"[X] Failed: {e}")
        return False
    
    print()
    print("[2/3] Loading model to GPU...")
    print("(First load transfers 1.87GB to VRAM - may take 1-2 minutes)")
    print("Please wait, do not interrupt...")
    print()
    
    start_load = time.time()
    try:
        xtts.load_model()
        load_time = time.time() - start_load
        print(f"[OK] Model loaded in {load_time:.1f} seconds")
    except Exception as e:
        print(f"[X] Load failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("[3/3] Generating audio...")
    
    test_text = (
        "Hello! This is a test of XTTS voice cloning with GPU acceleration. "
        "The quick brown fox jumps over the lazy dog. "
        "This should be much faster than CPU mode."
    )
    
    output_path = Path("outputs/audio/xtts_gpu_test.wav")
    
    start_synth = time.time()
    try:
        result = xtts.synthesize(
            text=test_text,
            reference_audio=reference_audio,
            output_path=output_path,
            language="en"
        )
        synth_time = time.time() - start_synth
        
        size_kb = result.stat().st_size / 1024
        print()
        print("="*60)
        print("[SUCCESS] GPU Audio Generation Complete!")
        print("="*60)
        print()
        print(f"Output: {result}")
        print(f"Size: {size_kb:.1f} KB")
        print(f"Processing Time: {synth_time:.2f} seconds")
        print()
        print("Listen to the audio file to verify voice cloning!")
        return True
        
    except Exception as e:
        print(f"[X] Synthesis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gpu()
    sys.exit(0 if success else 1)
