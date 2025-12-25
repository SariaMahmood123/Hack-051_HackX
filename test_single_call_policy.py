#!/usr/bin/env python3
"""Test SINGLE-CALL GEMINI POLICY implementation."""

import sys
sys.path.insert(0, '/mnt/d/Hack-051_HackX')

try:
    print("Testing imports...")
    from ai.gemini_client import GeminiClient
    from backend.routes.generation import GeminiGuard
    print("✓ Imports successful")
    
    print("\nTesting GeminiGuard with SINGLE-CALL POLICY...")
    guard = GeminiGuard()
    print(f"✓ Guard created: max_calls={guard.max_calls} (should be 1)")
    assert guard.max_calls == 1, f"ERROR: max_calls should be 1, got {guard.max_calls}"
    
    print(f"✓ First can_call(): {guard.can_call()} (should be True)")
    guard.record_call()
    print(f"✓ After record_call(), calls_made={guard.calls_made}")
    print(f"✓ Second can_call(): {guard.can_call()} (should be False)")
    assert not guard.can_call(), "ERROR: Second call should be blocked!"
    
    print("\nTesting generate_once() method exists...")
    client = GeminiClient(model_name="gemini-2.5-flash")
    assert hasattr(client, 'generate_once'), "ERROR: generate_once() method missing!"
    print("✓ generate_once() method exists")
    
    print("\n✅ SINGLE-CALL POLICY implementation verified!")
    print("   - GeminiGuard defaults to max_calls=1")
    print("   - Guard blocks after first call")
    print("   - generate_once() method available")
    
except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
