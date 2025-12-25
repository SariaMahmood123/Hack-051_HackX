#!/usr/bin/env python3
"""
XTTS Intent Synthesis Test
Tests synthesize_with_intent() with real ScriptIntent from Gemini
"""

import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai.xtts_wrapper import XTTSWrapper
from ai.script_intent import ScriptIntent

def main():
    print("=" * 60)
    print("XTTS INTENT SYNTHESIS TEST")
    print("=" * 60)
    print()
    
    # Paths
    intent_file = Path("outputs/intent_tests/gemini_intent_test.json")
    reference_audio = Path("assets/mkbhd.wav")
    output_dir = Path("outputs/intent_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Verify files exist
    if not intent_file.exists():
        print(f"❌ Intent file not found: {intent_file}")
        print("   Run test_gemini_intent.py first to generate intent")
        return
    
    if not reference_audio.exists():
        print(f"❌ Reference audio not found: {reference_audio}")
        return
    
    print(f"✓ Intent file: {intent_file}")
    print(f"✓ Reference audio: {reference_audio}")
    print()
    
    # Load intent
    print("Loading ScriptIntent from Gemini test...")
    with open(intent_file, 'r', encoding='utf-8') as f:
        intent_data = json.load(f)
    
    script_intent = ScriptIntent.from_dict(intent_data)
    print(f"✓ Loaded {len(script_intent.segments)} segments")
    print()
    
    # Display intent summary
    print("📊 SCRIPT INTENT SUMMARY:")
    print("-" * 60)
    for i, seg in enumerate(script_intent.segments, 1):
        print(f"Segment {i}:")
        print(f"  Text: {seg.text[:60]}...")
        print(f"  Pause: {seg.pause_after}s")
        print(f"  Emphasis: {seg.emphasis}")
        print(f"  Sentence end: {seg.sentence_end}")
    print()
    
    # Initialize XTTS
    print("Initializing XTTS wrapper...")
    xtts = XTTSWrapper(
        device="cpu"  # XTTS runs on CPU for quality/stability
    )
    
    print("Loading XTTS model...")
    print("(This may take 10-20 seconds on first load)")
    xtts.load_model()
    print("✓ XTTS model loaded")
    print()
    
    # Test synthesis with intent
    print("=" * 60)
    print("🎤 SYNTHESIZING AUDIO WITH INTENT")
    print("=" * 60)
    print()
    print("This will:")
    print("  1. Generate audio for each segment")
    print("  2. Apply emphasis (CAPITALIZATION for TTS)")
    print("  3. Insert explicit silence between segments")
    print("  4. Build IntentTimingMap for Motion Governor")
    print()
    print("Starting synthesis...")
    print("(This may take 30-60 seconds depending on text length)")
    print()
    
    audio_path, timing_map = xtts.synthesize_with_intent(
        script_intent=script_intent,
        reference_audio=str(reference_audio),
        output_path=str(output_dir / "xtts_intent_test.wav")
    )
    
    print()
    print("=" * 60)
    print("✅ SYNTHESIS COMPLETE")
    print("=" * 60)
    print()
    
    # Validate outputs
    if audio_path and Path(audio_path).exists():
        audio_size = Path(audio_path).stat().st_size
        print(f"✓ Audio generated: {audio_path}")
        print(f"  File size: {audio_size / 1024:.1f} KB")
    else:
        print(f"❌ Audio file not found: {audio_path}")
        return
    
    if timing_map:
        print(f"✓ IntentTimingMap created")
        print(f"  FPS: {timing_map.fps}")
        print(f"  Total segments: {len(timing_map.segments)}")
        print()
        
        # Display timing details
        print("📊 TIMING MAP DETAILS:")
        print("-" * 60)
        total_duration = 0.0
        for i, seg in enumerate(timing_map.segments, 1):
            duration = seg.end_time - seg.start_time
            total_duration = seg.end_time
            print(f"Segment {i}:")
            print(f"  Time: {seg.start_time:.2f}s - {seg.end_time:.2f}s (duration: {duration:.2f}s)")
            print(f"  Pause after: {seg.pause_after}s")
            print(f"  Emphasis: {seg.emphasis}")
            print(f"  Sentence end: {seg.sentence_end}")
        
        print()
        print(f"Total audio duration: {total_duration:.2f}s")
        print()
        
        # Save timing map to JSON
        timing_json_path = output_dir / "xtts_timing_map.json"
        with open(timing_json_path, 'w', encoding='utf-8') as f:
            json.dump(timing_map.to_dict(), f, indent=2)
        print(f"✓ Timing map saved to: {timing_json_path}")
        print()
        
        # Build intent masks
        print("Building intent masks for Motion Governor...")
        script_mask = timing_map.build_intent_mask()
        sentence_end_frames = timing_map.get_sentence_end_frames()
        
        print(f"✓ Script mask shape: {script_mask.shape}")
        print(f"  Min value: {script_mask.min():.3f}")
        print(f"  Max value: {script_mask.max():.3f}")
        print(f"  Mean value: {script_mask.mean():.3f}")
        print(f"  Sentence end frames: {len(sentence_end_frames)} markers")
        
        if len(sentence_end_frames) > 0:
            print(f"  Sentence ends at frames: {sentence_end_frames}")
        
    else:
        print("⚠️ No IntentTimingMap generated (fell back to plain synthesis)")
    
    print()
    print("=" * 60)
    print("🔍 VALIDATION")
    print("=" * 60)
    print()
    
    # Validate intent propagation
    if timing_map:
        intent_segments = len(script_intent.segments)
        timing_segments = len(timing_map.segments)
        
        if intent_segments == timing_segments:
            print(f"✅ Segment count matches: {intent_segments} segments")
        else:
            print(f"⚠️ Segment mismatch: {intent_segments} intent segments vs {timing_segments} timing segments")
        
        # Validate emphasis propagation
        emphasis_count = sum(1 for seg in script_intent.segments if seg.emphasis)
        print(f"✓ {emphasis_count}/{intent_segments} segments have emphasis markers")
        
        # Validate sentence ends
        sentence_ends = sum(1 for seg in script_intent.segments if seg.sentence_end)
        print(f"✓ {sentence_ends}/{intent_segments} segments are sentence endings")
        
        # Validate pauses
        total_pause = sum(seg.pause_after for seg in script_intent.segments)
        print(f"✓ Total explicit pause time: {total_pause:.2f}s")
    
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Listen to the generated audio to verify quality")
    print("  2. Check that pauses are audible between segments")
    print("  3. Verify emphasis words sound stressed (CAPITALIZED in TTS)")
    print("  4. Proceed to full pipeline test with SadTalker + Motion Governor")
    print()
    print(f"Audio file: {audio_path}")
    if timing_map:
        print(f"Timing map: {timing_json_path}")

if __name__ == "__main__":
    main()
