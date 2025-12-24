"""
Test XTTS with MKBHD Voice Reference
Generates speech using the extracted MKBHD voice clip
"""
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ai.xtts_wrapper import XTTSWrapper

def test_mkbhd_voice():
    """Test synthesis with MKBHD voice reference"""
    print("=" * 60)
    print("XTTS with MKBHD Voice Reference")
    print("=" * 60)
    print()
    
    # Initialize wrapper
    print("Initializing XTTS (quality-optimized CPU mode)...")
    xtts = XTTSWrapper()
    print(f"✓ Device: {xtts.device}")
    print()
    
    # Load model
    print("Loading model...")
    start = time.time()
    xtts.load_model()
    load_time = time.time() - start
    print(f"✓ Model loaded in {load_time:.1f}s")
    print()
    
    # Reference audio
    reference_audio = Path("assets/mkbhd.wav")
    
    if not reference_audio.exists():
        print(f"❌ Error: Reference audio not found: {reference_audio}")
        print("Please run the extract_reference_audio.py script first")
        return
    
    # Test cases with different content styles
    test_cases = [
        {
            "name": "Tech Review Style",
            "text": "So here's the thing about this year's smartphones - they're absolutely incredible! "
                    "The cameras have gotten so much better, the batteries last way longer, "
                    "and the displays? Chef's kiss. This is genuinely the best year for phones we've ever seen.",
            "output": "outputs/audio/mkbhd_tech_review.wav"
        },
        {
            "name": "Excited Announcement",
            "text": "Alright, so today we're talking about something really exciting! "
                    "This is probably one of the coolest things I've tested all year. "
                    "You're gonna love this. Let's dive in!",
            "output": "outputs/audio/mkbhd_excited.wav"
        },
        {
            "name": "Thoughtful Analysis",
            "text": "Now, when you really think about it, the question becomes: "
                    "is this actually worth the upgrade? Well, it depends on what you're coming from. "
                    "If you're on last year's model, maybe not. But if you're on something older? "
                    "Yeah, this is a pretty significant jump in quality.",
            "output": "outputs/audio/mkbhd_analysis.wav"
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test['name']}")
        print(f"Text: {test['text'][:80]}...")
        
        output_path = Path(test['output'])
        
        try:
            start = time.time()
            
            # Synthesize with emotion-focused parameters
            result_path = xtts.synthesize(
                text=test['text'],
                reference_audio=reference_audio,
                output_path=output_path,
                language="en",
                temperature=0.75,       # More expressive (higher than default)
                repetition_penalty=2.5, # Avoid repetition
                top_p=0.9,             # More natural variation
                top_k=50,              # Quality sampling
                speed=1.0              # Normal speed
            )
            
            gen_time = time.time() - start
            file_size = result_path.stat().st_size / 1024
            
            # Estimate audio duration
            audio_duration = (result_path.stat().st_size - 44) / 48000
            real_time_factor = gen_time / audio_duration if audio_duration > 0 else 0
            
            results.append({
                'name': test['name'],
                'success': True,
                'time': gen_time,
                'size': file_size,
                'duration': audio_duration
            })
            
            print(f"✓ Generated: {result_path.name}")
            print(f"  Size: {file_size:.1f} KB")
            print(f"  Time: {gen_time:.1f}s")
            print(f"  Duration: {audio_duration:.1f}s")
            print(f"  RTF: {real_time_factor:.2f}x")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            results.append({
                'name': test['name'],
                'success': False,
                'error': str(e)
            })
        
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    successful = sum(1 for r in results if r.get('success'))
    print(f"Passed: {successful}/{len(results)}")
    print()
    
    if successful > 0:
        total_duration = sum(r.get('duration', 0) for r in results if r.get('success'))
        total_size = sum(r.get('size', 0) for r in results if r.get('success'))
        
        print("Generated Files:")
        for r in results:
            if r.get('success'):
                print(f"  ✓ {r['name']}: {r['duration']:.1f}s ({r['size']:.1f} KB)")
        print()
        print(f"Total audio: {total_duration:.1f}s ({total_size:.1f} KB)")
        print(f"Voice: MKBHD (from assets/mkbhd.wav)")
        print(f"Quality: 24kHz, FP32 precision, CPU-optimized")
        print()
        print("🎧 Listen to the generated files in outputs/audio/")
    
    print()
    print("Done!")


if __name__ == "__main__":
    test_mkbhd_voice()
