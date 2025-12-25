"""
Test Gemini Intent Generation
Validates that Gemini outputs structured JSON with pause/emphasis markers
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from ai.gemini_client import GeminiClient
from ai.script_intent import ScriptIntent

# Load environment variables
load_dotenv()

# Test prompt
TEST_PROMPT = "Explain how GPUs work for video generation in about 3 sentences."

def main():
    print("=" * 60)
    print("GEMINI INTENT GENERATION TEST")
    print("=" * 60)
    print()
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        print("Set it with: export GEMINI_API_KEY='your-key'")
        return
    
    print(f"✓ Gemini API key found: {api_key[:10]}...")
    print()
    
    # Initialize client
    print("Initializing Gemini client...")
    client = GeminiClient(api_key=api_key)
    print("✓ Client initialized")
    print()
    
    # Test 1: Generate with intent
    print(f"📝 Prompt: {TEST_PROMPT}")
    print()
    print("Requesting structured intent from Gemini...")
    print("(This may take 5-10 seconds)")
    print()
    
    try:
        plain_text, script_intent = client.generate_with_intent(
            prompt=TEST_PROMPT,
            temperature=0.7,
            max_tokens=1000
        )
        
        print("=" * 60)
        print("✅ SUCCESS - Gemini Response Received")
        print("=" * 60)
        print()
        
        # Display plain text
        print("📄 PLAIN TEXT:")
        print("-" * 60)
        print(plain_text)
        print()
        
        # Display structured intent
        if script_intent:
            print("📊 STRUCTURED INTENT:")
            print("-" * 60)
            print(f"Total segments: {len(script_intent.segments)}")
            print()
            
            for i, seg in enumerate(script_intent.segments, 1):
                print(f"Segment {i}:")
                print(f"  Text: {seg.text}")
                print(f"  Pause after: {seg.pause_after}s")
                print(f"  Emphasis: {seg.emphasis if seg.emphasis else 'none'}")
                print(f"  Sentence end: {seg.sentence_end}")
                print()
            
            # Save to JSON
            output_dir = Path("outputs/intent_tests")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / "gemini_intent_test.json"
            script_intent.save(output_file)
            
            print("=" * 60)
            print(f"✓ Intent saved to: {output_file}")
            print("=" * 60)
            print()
            
            # Pretty print JSON
            print("📋 JSON OUTPUT:")
            print("-" * 60)
            with open(output_file, 'r') as f:
                intent_json = json.load(f)
                print(json.dumps(intent_json, indent=2))
            print()
            
            # Validate structure
            print("=" * 60)
            print("🔍 VALIDATION")
            print("=" * 60)
            
            required_fields = ["text", "pause_after", "emphasis", "sentence_end"]
            all_valid = True
            
            for i, seg in enumerate(script_intent.segments, 1):
                seg_dict = seg.to_dict()
                missing = [f for f in required_fields if f not in seg_dict]
                if missing:
                    print(f"❌ Segment {i} missing fields: {missing}")
                    all_valid = False
                else:
                    print(f"✓ Segment {i} has all required fields")
            
            print()
            if all_valid:
                print("✅ ALL SEGMENTS VALID")
            else:
                print("⚠️  SOME SEGMENTS INVALID")
            
        else:
            print("⚠️  Intent parsing failed - using fallback")
            print("This might indicate Gemini didn't return valid JSON")
        
    except Exception as e:
        print("=" * 60)
        print("❌ ERROR")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
