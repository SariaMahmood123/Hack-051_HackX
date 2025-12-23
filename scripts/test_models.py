"""
Utility script to test AI model wrappers individually
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai.gemini_client import GeminiClient
from ai.xtts_wrapper import XTTSWrapper
from ai.sadtalker_wrapper import SadTalkerWrapper


def test_gemini():
    """Test Gemini text generation"""
    print("\n" + "="*60)
    print("Testing Gemini 2.0 Flash")
    print("="*60)
    
    try:
        client = GeminiClient()
        response = client.generate("Hello! Tell me a short joke.")
        print(f"✅ Response: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_xtts():
    """Test XTTS text-to-speech"""
    print("\n" + "="*60)
    print("Testing XTTS v2")
    print("="*60)
    
    try:
        xtts = XTTSWrapper()
        print("✅ XTTS wrapper initialized")
        print("⚠️  Model not loaded (requires actual TTS library)")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_sadtalker():
    """Test SadTalker video generation"""
    print("\n" + "="*60)
    print("Testing SadTalker")
    print("="*60)
    
    try:
        sadtalker = SadTalkerWrapper()
        print("✅ SadTalker wrapper initialized")
        print("⚠️  Model not loaded (requires actual SadTalker checkpoints)")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║              LUMEN Model Testing Utility                  ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    test_gemini()
    test_xtts()
    test_sadtalker()
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
