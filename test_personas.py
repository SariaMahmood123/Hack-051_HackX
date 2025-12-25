"""
Test persona-specific script generation (iJustine vs MKBHD)
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "SadTalker/SadTalker-main"))

from ai.gemini_client import GeminiClient
import json

def test_personas():
    """Test both iJustine and MKBHD script generation"""
    
    print("=" * 70)
    print("PERSONA SCRIPT GENERATION TEST")
    print("=" * 70)
    print()
    
    # Initialize client
    gemini = GeminiClient()
    
    # Test topic
    topic = "Explain why the new GPU is revolutionary"
    
    print(f"📝 Topic: {topic}")
    print()
    
    # Test iJustine style
    print("-" * 70)
    print("🎯 IJUSTINE STYLE (Energetic, Fast-paced)")
    print("-" * 70)
    print()
    
    ijustine_text, ijustine_intent = gemini.generate_ijustine_script(topic)
    
    print("Generated Script:")
    print(ijustine_text)
    print()
    
    if ijustine_intent:
        print(f"Segments: {len(ijustine_intent.segments)}")
        print()
        print("Intent breakdown:")
        for i, seg in enumerate(ijustine_intent.segments[:3], 1):
            print(f"  {i}. \"{seg.text}\"")
            print(f"     Pause: {seg.pause_after}s, Emphasis: {seg.emphasis}, Sentence end: {seg.sentence_end}")
        if len(ijustine_intent.segments) > 3:
            print(f"  ... ({len(ijustine_intent.segments) - 3} more segments)")
    print()
    
    # Test MKBHD style
    print("-" * 70)
    print("🎯 MKBHD STYLE (Smooth, Measured)")
    print("-" * 70)
    print()
    
    mkbhd_text, mkbhd_intent = gemini.generate_mkbhd_script(topic)
    
    print("Generated Script:")
    print(mkbhd_text)
    print()
    
    if mkbhd_intent:
        print(f"Segments: {len(mkbhd_intent.segments)}")
        print()
        print("Intent breakdown:")
        for i, seg in enumerate(mkbhd_intent.segments[:3], 1):
            print(f"  {i}. \"{seg.text}\"")
            print(f"     Pause: {seg.pause_after}s, Emphasis: {seg.emphasis}, Sentence end: {seg.sentence_end}")
        if len(mkbhd_intent.segments) > 3:
            print(f"  ... ({len(mkbhd_intent.segments) - 3} more segments)")
    print()
    
    # Save outputs
    output_dir = Path("outputs/persona_tests")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if ijustine_intent:
        ijustine_path = output_dir / "ijustine_intent.json"
        ijustine_intent.save(ijustine_path)
        print(f"✓ Saved iJustine intent: {ijustine_path}")
    
    if mkbhd_intent:
        mkbhd_path = output_dir / "mkbhd_intent.json"
        mkbhd_intent.save(mkbhd_path)
        print(f"✓ Saved MKBHD intent: {mkbhd_path}")
    
    print()
    print("=" * 70)
    print("✅ PERSONA TEST COMPLETE")
    print("=" * 70)
    print()
    print("Key differences:")
    print("  • iJustine: Shorter segments, more emphasis, faster pauses (0.2-0.3s)")
    print("  • MKBHD: Longer segments, selective emphasis, measured pauses (0.4-0.5s)")
    print()

if __name__ == "__main__":
    test_personas()
