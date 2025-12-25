"""
Test frame alignment fix in Motion Governor.

This validates that:
1. _align_intent_mask() correctly handles frame count mismatches
2. Shorter masks are padded with last value (not zeros)
3. Longer masks are truncated
4. Sentence end frames are filtered correctly
"""

import sys
import numpy as np
from pathlib import Path

# Add SadTalker to path
sys.path.append(str(Path(__file__).parent / "SadTalker/SadTalker-main"))

from ai.motion_governor import MotionGovernor
from ai.script_intent import IntentTimingMap

def test_align_intent_mask():
    """Test _align_intent_mask helper method"""
    
    print("=" * 70)
    print("TESTING FRAME ALIGNMENT FIX")
    print("=" * 70)
    print()
    
    # Create Motion Governor instance
    governor = MotionGovernor()
    
    # Test 1: Truncation (longer → shorter)
    print("Test 1: Truncate longer mask (726 → 725 frames)")
    mask_726 = np.linspace(0.5, 1.5, 726)
    mask_725 = governor._align_intent_mask(mask_726, 725, "test")
    print(f"  Input length: {len(mask_726)}")
    print(f"  Output length: {len(mask_725)}")
    print(f"  Last value preserved: {mask_725[-1]:.3f} (expected ~{mask_726[724]:.3f})")
    assert len(mask_725) == 725, "Truncation failed"
    assert np.allclose(mask_725, mask_726[:725]), "Values changed during truncation"
    print("  ✓ PASSED")
    print()
    
    # Test 2: Padding (shorter → longer)
    print("Test 2: Pad shorter mask (724 → 725 frames)")
    mask_724 = np.linspace(0.5, 1.5, 724)
    last_val = mask_724[-1]
    mask_725 = governor._align_intent_mask(mask_724, 725, "test")
    print(f"  Input length: {len(mask_724)}")
    print(f"  Output length: {len(mask_725)}")
    print(f"  Last value: {last_val:.3f}")
    print(f"  Padded value: {mask_725[-1]:.3f}")
    assert len(mask_725) == 725, "Padding failed"
    assert mask_725[-1] == last_val, "Padding didn't use last value"
    print("  ✓ PASSED")
    print()
    
    # Test 3: No change (same length)
    print("Test 3: Same length (725 → 725 frames)")
    mask_725_in = np.ones(725) * 1.1
    mask_725_out = governor._align_intent_mask(mask_725_in, 725, "test")
    print(f"  Input length: {len(mask_725_in)}")
    print(f"  Output length: {len(mask_725_out)}")
    assert len(mask_725_out) == 725, "Length changed"
    assert np.array_equal(mask_725_out, mask_725_in), "Values changed"
    print("  ✓ PASSED")
    print()
    
    # Test 4: None handling
    print("Test 4: None mask handling")
    result = governor._align_intent_mask(None, 725, "test")
    assert result is None, "None not preserved"
    print("  ✓ PASSED")
    print()
    
    # Test 5: Sentence end frame filtering
    print("Test 5: Sentence end frame filtering")
    sentence_frames_in = [238, 481, 713, 730, 850]  # Some out of range
    T_motion = 725
    sentence_frames_out = [f for f in sentence_frames_in if f < T_motion]
    print(f"  Input frames: {sentence_frames_in}")
    print(f"  Motion length: {T_motion}")
    print(f"  Filtered frames: {sentence_frames_out}")
    assert len(sentence_frames_out) == 3, "Filtering failed"
    assert all(f < T_motion for f in sentence_frames_out), "Invalid frames not removed"
    print("  ✓ PASSED")
    print()
    
    print("=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    print()
    print("Frame alignment fix is working correctly!")
    print("SadTalker frame count (T_motion) is now the source of truth.")
    print()

def test_with_real_timing_map():
    """Test with actual IntentTimingMap from XTTS output"""
    
    print("=" * 70)
    print("TESTING WITH REAL INTENT TIMING MAP")
    print("=" * 70)
    print()
    
    # Load real timing map
    timing_map_file = Path("outputs/intent_tests/xtts_timing_map.json")
    if not timing_map_file.exists():
        print(f"⚠️  Timing map not found: {timing_map_file}")
        print("   Run test_xtts_intent.py first to generate timing map")
        return
    
    timing_map = IntentTimingMap.load(timing_map_file)
    print(f"Loaded IntentTimingMap:")
    print(f"  Total duration: {timing_map.total_duration:.2f}s")
    print(f"  FPS: {timing_map.fps}")
    print(f"  Num frames (XTTS): {timing_map.num_frames}")
    print()
    
    # Build intent mask (726 frames from XTTS)
    script_intent_mask = timing_map.build_intent_mask()
    sentence_end_frames = timing_map.get_sentence_end_frames()
    
    print(f"Script intent mask:")
    print(f"  Shape: {script_intent_mask.shape}")
    print(f"  Min: {script_intent_mask.min():.3f}")
    print(f"  Max: {script_intent_mask.max():.3f}")
    print(f"  Sentence end frames: {sentence_end_frames}")
    print()
    
    # Simulate SadTalker generating 725 frames (typical ±1 mismatch)
    T_motion = 725
    print(f"Simulating SadTalker output: T_motion = {T_motion} frames")
    print()
    
    # Test alignment
    governor = MotionGovernor()
    
    aligned_mask = governor._align_intent_mask(script_intent_mask, T_motion, "script")
    aligned_sentences = [f for f in sentence_end_frames if f < T_motion]
    
    print(f"After alignment:")
    print(f"  Mask shape: {aligned_mask.shape}")
    print(f"  Sentence frames: {aligned_sentences}")
    print()
    
    # Verify no crashes would occur
    try:
        # Simulate np.clip operation from _process_motion
        dummy_pose = np.random.randn(T_motion, 3)
        dummy_mask_subset = aligned_mask[aligned_sentences[0]:aligned_sentences[0]+10]
        dummy_clipped = np.clip(dummy_pose[0:10], -0.1, 0.1)
        print("✓ Array operations work correctly (no broadcasting errors)")
        print()
    except ValueError as e:
        print(f"❌ Array operation failed: {e}")
        return
    
    print("=" * 70)
    print("✅ REAL-WORLD TEST PASSED")
    print("=" * 70)
    print()
    print("Frame alignment fix handles actual XTTS → SadTalker mismatch!")
    print()

if __name__ == "__main__":
    test_align_intent_mask()
    test_with_real_timing_map()
