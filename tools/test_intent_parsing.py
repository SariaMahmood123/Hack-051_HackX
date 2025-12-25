"""
Test Intent Parsing Robustness
Tests various Gemini response formats to ensure parse_gemini_intent_output handles them correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.script_intent import parse_gemini_intent_output, ScriptIntent
import json


# Test cases with various Gemini response formats
TEST_CASES = [
    {
        "name": "Valid Plain JSON",
        "response": """{
  "segments": [
    {
      "text": "Hello world",
      "pause_after": 0.3,
      "emphasis": [],
      "sentence_end": true
    }
  ]
}""",
        "should_pass": True
    },
    {
        "name": "Valid Fenced JSON",
        "response": """```json
{
  "segments": [
    {
      "text": "This is a test",
      "pause_after": 0.5,
      "emphasis": ["test"],
      "sentence_end": true
    }
  ]
}
```""",
        "should_pass": True
    },
    {
        "name": "JSON with Preamble",
        "response": """Here's the JSON output you requested:

{
  "segments": [
    {
      "text": "Tech review content",
      "pause_after": 0.4,
      "emphasis": ["tech"],
      "sentence_end": false
    }
  ]
}""",
        "should_pass": True
    },
    {
        "name": "JSON with Trailing Text",
        "response": """{
  "segments": [
    {
      "text": "Final segment",
      "pause_after": 0.2,
      "emphasis": [],
      "sentence_end": true
    }
  ]
}

I hope this helps!""",
        "should_pass": True
    },
    {
        "name": "Incomplete Response (just fence)",
        "response": "```json",
        "should_pass": False
    },
    {
        "name": "Incomplete Response (fence with no content)",
        "response": """```json

```""",
        "should_pass": False
    },
    {
        "name": "Missing Segments Field",
        "response": """{
  "total_duration": 10.5
}""",
        "should_pass": False
    },
    {
        "name": "Empty Segments Array",
        "response": """{
  "segments": []
}""",
        "should_pass": False
    },
    {
        "name": "Invalid JSON",
        "response": """{
  "segments": [
    {
      "text": "Unclosed object"
      "pause_after": 0.3
    }
  ]
}""",
        "should_pass": False
    },
    {
        "name": "Multiple Segments",
        "response": """{
  "segments": [
    {
      "text": "First segment",
      "pause_after": 0.3,
      "emphasis": [],
      "sentence_end": false
    },
    {
      "text": "Second segment with emphasis",
      "pause_after": 0.5,
      "emphasis": ["emphasis"],
      "sentence_end": true
    },
    {
      "text": "Final segment",
      "pause_after": 0.2,
      "emphasis": [],
      "sentence_end": true
    }
  ]
}""",
        "should_pass": True
    },
    {
        "name": "Fenced JSON without 'json' marker",
        "response": """```
{
  "segments": [
    {
      "text": "Generic fence",
      "pause_after": 0.3,
      "emphasis": [],
      "sentence_end": true
    }
  ]
}
```""",
        "should_pass": True
    },
    {
        "name": "JSON with Windows Line Endings",
        "response": "{\r\n  \"segments\": [\r\n    {\r\n      \"text\": \"Windows style\",\r\n      \"pause_after\": 0.3,\r\n      \"emphasis\": [],\r\n      \"sentence_end\": true\r\n    }\r\n  ]\r\n}",
        "should_pass": True
    },
]


def run_tests():
    """Run all test cases and report results"""
    print("=" * 70)
    print("INTENT PARSING ROBUSTNESS TEST")
    print("=" * 70)
    print()
    
    passed = 0
    failed = 0
    unexpected = 0
    
    for i, test in enumerate(TEST_CASES, 1):
        name = test["name"]
        response = test["response"]
        should_pass = test["should_pass"]
        
        print(f"Test {i}/{len(TEST_CASES)}: {name}")
        print(f"  Response length: {len(response)} chars")
        print(f"  Response preview: {response[:60].replace(chr(10), ' ').replace(chr(13), '')}...")
        print(f"  Expected: {'PASS' if should_pass else 'FAIL'}")
        
        # Try parsing
        try:
            result = parse_gemini_intent_output(response)
            
            if result is not None:
                # Successful parse
                if should_pass:
                    print(f"  ✓ PASS - Successfully parsed {len(result.segments)} segment(s)")
                    passed += 1
                else:
                    print(f"  ✗ UNEXPECTED PASS - Expected to fail but parsed successfully")
                    unexpected += 1
            else:
                # Failed to parse
                if not should_pass:
                    print(f"  ✓ PASS - Correctly rejected invalid input")
                    passed += 1
                else:
                    print(f"  ✗ FAIL - Should have parsed but returned None")
                    failed += 1
        except Exception as e:
            print(f"  ✗ EXCEPTION - {type(e).__name__}: {e}")
            if should_pass:
                failed += 1
            else:
                # Exception on invalid input is acceptable
                print(f"  Note: Exception on invalid input is acceptable")
                passed += 1
        
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total tests:      {len(TEST_CASES)}")
    print(f"Passed:           {passed} ✓")
    print(f"Failed:           {failed} ✗")
    print(f"Unexpected:       {unexpected}")
    print(f"Success rate:     {passed / len(TEST_CASES) * 100:.1f}%")
    print()
    
    if failed == 0 and unexpected == 0:
        print("✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"✗ {failed + unexpected} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
