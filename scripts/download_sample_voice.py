"""
Download a sample reference voice for XTTS testing
Uses a free sample from Coqui's examples
"""
import requests
from pathlib import Path

def download_sample_voice():
    """Download a sample reference audio for quick testing"""
    
    output_path = Path("assets/reference_voice.wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("Download Sample Reference Voice")
    print("="*60)
    print()
    
    # Sample audio from Coqui's examples
    # This is a neutral English voice sample
    sample_url = "https://github.com/coqui-ai/TTS/raw/dev/tests/data/ljspeech/wavs/LJ001-0001.wav"
    
    print(f"Downloading sample voice...")
    print(f"Source: {sample_url}")
    print()
    
    try:
        response = requests.get(sample_url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Downloaded to: {output_path.absolute()}")
        print(f"  Size: {output_path.stat().st_size / 1024:.1f} KB")
        print()
        print("="*60)
        print("Next step: Test XTTS")
        print("  python test_xtts.py")
        print("="*60)
        print()
        print("NOTE: This is a sample voice.")
        print("For your own voice, run:")
        print("  python scripts/record_reference_audio.py")
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        print()
        print("Alternative: Record your own voice")
        print("  python scripts/record_reference_audio.py")

if __name__ == "__main__":
    download_sample_voice()
