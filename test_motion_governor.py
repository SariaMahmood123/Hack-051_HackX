"""
Motion Governor A/B Test Script
Compares SadTalker baseline vs. Motion Governed output
"""
import sys
import os
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SadTalker/SadTalker-main'))

import torch
from ai.sadtalker_wrapper import SadTalkerWrapper

print("=" * 70)
print("Motion Governor A/B Test")
print("=" * 70)
print(f"[{time.strftime('%H:%M:%S')}] Starting A/B comparison...")
print()

# Check CUDA
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA version: {torch.version.cuda}")
print()

# Configuration
audio_path = "outputs/audio/mkbhd_tech_review.wav"
image_path = "assets/mkbhd.jpg"
baseline_output = "outputs/video/test_baseline.mp4"
governed_output = "outputs/video/test_governed.mp4"

# Verify inputs exist
if not os.path.exists(audio_path):
    print(f"❌ Audio file not found: {audio_path}")
    sys.exit(1)

if not os.path.exists(image_path):
    print(f"❌ Image file not found: {image_path}")
    sys.exit(1)

# Initialize wrapper
print("=" * 70)
print(f"[{time.strftime('%H:%M:%S')}] Initializing SadTalker with CUDA...")
print("=" * 70)
wrapper = SadTalkerWrapper(device='cuda')
print(f"✓ Initialized with device: {wrapper.device}")
print()

# Test 1: Baseline (no Motion Governor)
print("=" * 70)
print(f"[{time.strftime('%H:%M:%S')}] TEST 1: BASELINE (no Motion Governor)")
print("=" * 70)
print(f"Audio: {audio_path}")
print(f"Image: {image_path}")
print(f"Output: {baseline_output}")
print("This will take 2-3 minutes...")
print()

start_time = time.time()
try:
    result_baseline = wrapper.generate(
        audio_path,
        image_path,
        baseline_output,
        enable_motion_governor=False
    )
    elapsed = time.time() - start_time
    
    if os.path.exists(result_baseline):
        size_mb = os.path.getsize(result_baseline) / (1024 * 1024)
        print(f"\n✓ Baseline video generated!")
        print(f"  Path: {result_baseline}")
        print(f"  Size: {size_mb:.2f} MB")
        print(f"  Time: {elapsed:.1f}s")
    else:
        print(f"\n❌ Baseline generation failed")
        sys.exit(1)
except Exception as e:
    print(f"\n❌ Baseline generation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 2: Motion Governed
print("=" * 70)
print(f"[{time.strftime('%H:%M:%S')}] TEST 2: MOTION GOVERNED (calm_tech style)")
print("=" * 70)
print(f"Audio: {audio_path}")
print(f"Image: {image_path}")
print(f"Output: {governed_output}")
print("This will take 2-3 minutes...")
print()

# Reset wrapper state
wrapper = SadTalkerWrapper(device='cuda')

start_time = time.time()
try:
    result_governed = wrapper.generate(
        audio_path,
        image_path,
        governed_output,
        enable_motion_governor=True,
        motion_style="calm_tech"
    )
    elapsed = time.time() - start_time
    
    if os.path.exists(result_governed):
        size_mb = os.path.getsize(result_governed) / (1024 * 1024)
        print(f"\n✓ Governed video generated!")
        print(f"  Path: {result_governed}")
        print(f"  Size: {size_mb:.2f} MB")
        print(f"  Time: {elapsed:.1f}s")
    else:
        print(f"\n❌ Governed generation failed")
        sys.exit(1)
except Exception as e:
    print(f"\n❌ Governed generation error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("A/B TEST COMPLETE")
print("=" * 70)
print(f"Baseline:  {baseline_output}")
print(f"Governed:  {governed_output}")
print()
print("Compare the videos to evaluate:")
print("  - Head pose stability (less jitter)")
print("  - Expression subtlety (less overacting)")
print("  - Pause behavior (less fidgeting during silence)")
print("=" * 70)
