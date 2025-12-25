#!/usr/bin/env python3
"""
Extract Motion Style Profile from Reference Video
Uses Motion Governor to analyze motion patterns and create reusable style preset
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ai.motion_governor import MotionGovernor, StyleProfile

def main():
    print("=" * 70)
    print("MOTION STYLE EXTRACTION")
    print("=" * 70)
    print()
    
    reference_video = Path("assets/reference_motion.mp4")
    output_style = Path("assets/mkbhd_motion_style.json")
    
    if not reference_video.exists():
        print(f"❌ Reference video not found: {reference_video}")
        print()
        print("Run extract_video_segment.py first to create reference video")
        return
    
    print(f"✓ Reference video: {reference_video}")
    print(f"  Output style: {output_style}")
    print()
    
    # Initialize Motion Governor
    print("Initializing Motion Governor...")
    governor = MotionGovernor()
    print("✓ Motion Governor ready")
    print()
    
    # Extract style from video
    print("=" * 70)
    print("🎯 ANALYZING MOTION PATTERNS")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Extract video frames")
    print("  2. Detect face landmarks using OpenCV (mediapipe not available)")
    print("  3. Calculate head rotation angles (pitch, yaw, roll)")
    print("  4. Compute motion statistics (magnitude, smoothness)")
    print("  5. Generate reusable StyleProfile")
    print()
    print("Processing... (this may take 30-90 seconds)")
    print()
    
    try:
        style_profile = governor.extract_style_from_video(
            video_path=str(reference_video),
            style_name="mkbhd_reference"
        )
        
        print()
        print("=" * 70)
        print("✅ MOTION STYLE EXTRACTED")
        print("=" * 70)
        print()
        
        if style_profile:
            # Display style details
            print("📊 STYLE PROFILE SUMMARY:")
            print("-" * 70)
            print(f"Name: {style_profile.name}")
            print()
            print("Motion Factors:")
            print(f"  Pitch (up/down): {style_profile.pitch_factor:.3f}")
            print(f"  Yaw (left/right): {style_profile.yaw_factor:.3f}")
            print(f"  Roll (tilt): {style_profile.roll_factor:.3f}")
            print(f"  Expression: {style_profile.expression_factor:.3f}")
            print()
            print("Smoothing:")
            print(f"  Temporal alpha: {style_profile.smoothing_alpha:.3f}")
            print()
            print("Intent Scaling:")
            print(f"  Pause gate: {style_profile.intent_pause_gate:.3f}")
            print(f"  Emphasis boost: {style_profile.intent_emphasis_boost:.3f}")
            print()
            
            # Save to JSON
            style_dict = style_profile.to_dict()
            with open(output_style, 'w') as f:
                json.dump(style_dict, f, indent=2)
            
            print(f"✓ Style saved to: {output_style}")
            print()
            
            # Usage instructions
            print("=" * 70)
            print("📝 USAGE")
            print("=" * 70)
            print()
            print("To use this style in pipeline:")
            print()
            print("  # Option 1: Pass StyleProfile object")
            print("  style = StyleProfile.from_dict(json.load(open('assets/mkbhd_motion_style.json')))")
            print("  sadtalker.generate(..., motion_style=style)")
            print()
            print("  # Option 2: Load from file in Motion Governor")
            print("  governor.load_style('mkbhd_reference', 'assets/mkbhd_motion_style.json')")
            print("  sadtalker.generate(..., motion_style='mkbhd_reference')")
            print()
            print("=" * 70)
            print("EXTRACTION COMPLETE")
            print("=" * 70)
            print()
            print("Next step: Run full pipeline test with extracted style")
            print("  Edit test_full_intent_pipeline.py:")
            print("  Change motion_style='natural' to motion_style='mkbhd_reference'")
            
        else:
            print("⚠️ Style extraction returned None (may have failed)")
            print("Check logs above for errors")
            
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ STYLE EXTRACTION FAILED")
        print("=" * 70)
        print()
        print(f"Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
