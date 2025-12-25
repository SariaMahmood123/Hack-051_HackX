"""
Record reference audio for XTTS voice cloning
Records 15 seconds of audio from your microphone
"""
import sounddevice as sd
import soundfile as sf
import numpy as np
from pathlib import Path

def record_reference_audio(duration=15, sample_rate=22050):
    """
    Record audio from microphone for voice cloning
    
    Args:
        duration: Recording length in seconds (10-30 recommended)
        sample_rate: Audio sample rate (22050 Hz is good for XTTS)
    """
    output_path = Path("assets/reference_voice.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("XTTS Reference Audio Recorder")
    print("="*60)
    print()
    print(f"Recording {duration} seconds of audio...")
    print()
    print("Instructions:")
    print("1. Speak clearly in your natural voice")
    print("2. Read a paragraph or speak naturally")
    print("3. Avoid background noise/music")
    print("4. Stay close to the microphone")
    print()
    
    input("Press ENTER to start recording...")
    print()
    print(f"🎤 RECORDING... ({duration} seconds)")
    print("Speak now!")
    print()
    
    # Record audio
    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )
    sd.wait()  # Wait for recording to finish
    
    print("✓ Recording complete!")
    print()
    
    # Save to file
    sf.write(output_path, audio, sample_rate)
    
    print(f"✓ Saved to: {output_path.absolute()}")
    print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")
    print()
    print("="*60)
    print("Next step: Test XTTS")
    print("  python test_xtts.py")
    print("="*60)

if __name__ == "__main__":
    try:
        record_reference_audio()
    except KeyboardInterrupt:
        print("\n❌ Recording cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print()
        print("Make sure you have sounddevice installed:")
        print("  pip install sounddevice soundfile")
