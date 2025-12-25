import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SadTalker/SadTalker-main'))

import torch
from ai.sadtalker_wrapper import SadTalkerWrapper

print("=" * 60)
print("Testing SadTalker with GPU in WSL")
print("=" * 60)
print(f"[{time.strftime('%H:%M:%S')}] Starting...")

# Check CUDA
print(f"\nPyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA version: {torch.version.cuda}")
    
# Initialize wrapper with GPU
print("\n" + "=" * 60)
print(f"[{time.strftime('%H:%M:%S')}] Initializing SadTalkerWrapper with CUDA...")
print("=" * 60)

wrapper = SadTalkerWrapper(device='cuda')
print(f"[{time.strftime('%H:%M:%S')}] ✓ Initialized with device: {wrapper.device}")

# Test video generation
print("\n" + "=" * 60)
print(f"[{time.strftime('%H:%M:%S')}] Generating test video on GPU...")
print("=" * 60)

audio_path = "outputs/audio/mkbhd_53f64944-f49f-464e-8962-11c57e3e746f.wav"
image_path = "assets/mkbhd2.jpg"
output_path = "outputs/video/video_wsl_gpu.mp4"

if not os.path.exists(audio_path):
    print(f"❌ Audio file not found: {audio_path}")
    sys.exit(1)

if not os.path.exists(image_path):
    print(f"❌ Image file not found: {image_path}")
    sys.exit(1)

print(f"Audio: {audio_path}")
print(f"Image: {image_path}")
print(f"Output: {output_path}")
print(f"[{time.strftime('%H:%M:%S')}] Starting generation (this will take 2-3 minutes)...")
print("PLEASE WAIT - Model loading may take 60-90 seconds on first run...")

start_time = time.time()
result_path = wrapper.generate(audio_path, image_path, output_path)
elapsed = time.time() - start_time

if os.path.exists(result_path):
    size_mb = os.path.getsize(result_path) / (1024 * 1024)
    print(f"\n✓ Video generated successfully!")
    print(f"  Path: {result_path}")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
else:
    print(f"\n❌ Video generation failed!")
    sys.exit(1)
