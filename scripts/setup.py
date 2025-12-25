"""
Setup script for LUMEN development environment
Downloads and configures AI models
"""
import os
import sys
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
ASSETS_DIR = PROJECT_ROOT / "assets"

def print_step(message):
    """Print formatted step message"""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}\n")

def check_gpu():
    """Check if CUDA is available"""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            print(f"✅ GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA version: {torch.version.cuda}")
        else:
            print("⚠️  No GPU detected. Models will run on CPU (slower)")
        return gpu_available
    except ImportError:
        print("❌ PyTorch not installed. Please install requirements first.")
        return False

def setup_directories():
    """Create necessary directories"""
    print_step("Setting up directories")
    
    directories = [
        MODELS_DIR,
        MODELS_DIR / "xtts_v2",
        MODELS_DIR / "sadtalker",
        ASSETS_DIR,
        PROJECT_ROOT / "outputs" / "audio",
        PROJECT_ROOT / "outputs" / "video",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"✓ {directory}")

def download_xtts():
    """Download XTTS v2 model"""
    print_step("Downloading XTTS v2 model")
    
    print("XTTS v2 will auto-download on first use via TTS library.")
    print("Alternatively, you can pre-download:")
    print("  from TTS.api import TTS")
    print('  TTS("tts_models/multilingual/multi-dataset/xtts_v2")')
    print("\nSkipping pre-download for now...")

def download_sadtalker():
    """Download SadTalker checkpoints"""
    print_step("Downloading SadTalker checkpoints")
    
    sadtalker_dir = MODELS_DIR / "sadtalker"
    
    print("SadTalker requires manual checkpoint download:")
    print(f"\n1. Clone SadTalker repository:")
    print(f"   git clone https://github.com/OpenTalker/SadTalker.git {sadtalker_dir}")
    print(f"\n2. Download checkpoints:")
    print(f"   cd {sadtalker_dir}")
    print(f"   bash scripts/download_models.sh")
    print("\nSkipping automatic download for now...")

def create_sample_assets():
    """Create placeholder asset files"""
    print_step("Creating sample asset placeholders")
    
    avatar_path = ASSETS_DIR / "avatar.jpg"
    voice_path = ASSETS_DIR / "reference_voice.wav"
    
    if not avatar_path.exists():
        print(f"📝 Create: {avatar_path}")
        print("   Add a clear frontal portrait image for the avatar")
    
    if not voice_path.exists():
        print(f"📝 Create: {voice_path}")
        print("   Add a 5-15 second audio sample for voice cloning")

def check_env_file():
    """Check if .env file exists"""
    print_step("Checking environment configuration")
    
    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    
    if not env_file.exists():
        print(f"⚠️  .env file not found")
        print(f"   Copy {env_example} to {env_file}")
        print(f"   Add your GEMINI_API_KEY")
    else:
        print(f"✅ .env file exists")

def main():
    """Main setup routine"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║                   LUMEN Setup Script                      ║
    ║        Video-Based Conversational AI Platform            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check GPU
    check_gpu()
    
    # Setup directories
    setup_directories()
    
    # Model downloads
    download_xtts()
    download_sadtalker()
    
    # Asset placeholders
    create_sample_assets()
    
    # Environment check
    check_env_file()
    
    print_step("Setup Complete!")
    print("Next steps:")
    print("  1. Install Python dependencies: pip install -r requirements.txt")
    print("  2. Configure .env file with GEMINI_API_KEY")
    print("  3. Add reference avatar image and voice sample to assets/")
    print("  4. Download model checkpoints (see instructions above)")
    print("  5. Start backend: cd backend && uvicorn main:app --reload")
    print("  6. Start frontend: cd frontend && npm install && npm run dev")
    print("\n🚀 Happy hacking!\n")

if __name__ == "__main__":
    main()
