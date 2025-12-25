#!/usr/bin/env python3
"""Test imports after quota-safe refactor."""

try:
    from ai.gemini_client import GeminiClient
    print("✓ GeminiClient imported")
    
    from backend.routes.generation import GeminiGuard
    print("✓ GeminiGuard imported")
    
    # Test instantiation
    guard = GeminiGuard(max_calls=3)
    print(f"✓ GeminiGuard instantiated: disabled={guard.disabled}, max_calls={guard.max_calls}")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
