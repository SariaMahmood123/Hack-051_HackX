"""
Test XTTS v2 installation and voice synthesis
Run this after installing TTS library
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai.xtts_wrapper import XTTSWrapper

def test_xtts():
    print("="*60)
    print("Testing XTTS v2 Setup")
    print("="*60)
    print()
    
    # Check reference audio
    reference_audio = Path("assets/reference_voice.wav")
    if not reference_audio.exists():
        print("[X] Reference audio not found!")
        print(f"   Expected: {reference_audio.absolute()}")
        print()
        print("Please add a reference audio file:")
        print("1. Record 10-20 seconds of clear speech")
        print("2. Save as WAV format (16kHz recommended)")
        print("3. Place at: assets/reference_voice.wav")
        print()
        print("OR use this command to record:")
        print("   python scripts/record_reference_audio.py")
        return False
    
    print(f"[OK] Reference audio found: {reference_audio}")
    print()
    
    # Initialize XTTS
    print("Initializing XTTS...")
    try:
        xtts = XTTSWrapper()
        print("[OK] XTTS wrapper created")
        print()
    except Exception as e:
        print(f"[X] Failed to create wrapper: {e}")
        return False
    
    # Load model (will download on first run)
    print("Loading XTTS model...")
    print("(First run will download ~2GB - may take 2-5 minutes)")
    try:
        xtts.load_model()
        print("[OK] Model loaded successfully")
        print()
    except Exception as e:
        print(f"[X] Failed to load model: {e}")
        print()
        print("Try installing TTS:")
        print("   pip install TTS==0.22.0")
        return False
    
    # Test synthesis
    print("Testing voice synthesis...")
    test_text = "Hello! This is a test of the XTTS voice cloning system."
    output_path = Path("outputs/audio/xtts_test.wav")
    
    try:
        result = xtts.synthesize(
            text=test_text,
            reference_audio=reference_audio,
            output_path=output_path,
            language="en"
        )
        
        print(f"[OK] Audio generated: {result}")
        print(f"  Size: {result.stat().st_size / 1024:.1f} KB")
        print()
        print("="*60)
        print("[SUCCESS] XTTS SETUP COMPLETE!")
        print("="*60)
        print()
        print("Listen to the test audio:")
        print(f"  {result.absolute()}")
        print()
        return True
        
    except Exception as e:
        print(f"[X] Synthesis failed: {e}")
        return False

if __name__ == "__main__":
    success = test_xtts()
    sys.exit(0 if success else 1)
