"""Quick XTTS test - no license prompt"""
import sys
import os

print("=" * 60)
print("Quick XTTS Test")
print("=" * 60)
print()

# Test 1: PyTorch version
print("[1/3] Checking PyTorch version...")
try:
    import torch
    print(f"✓ PyTorch: {torch.__version__}")
    print(f"✓ CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"✓ GPU: {torch.cuda.get_device_name(0)}")
except Exception as e:
    print(f"❌ PyTorch error: {e}")
    sys.exit(1)

print()

# Test 2: TTS import
print("[2/3] Checking TTS library...")
try:
    from TTS.api import TTS
    print("✓ TTS library imported successfully")
except Exception as e:
    print(f"❌ TTS import failed: {e}")
    sys.exit(1)

print()

# Test 3: Check _pytree attribute
print("[3/3] Checking PyTorch _pytree compatibility...")
try:
    import torch.utils._pytree
    if hasattr(torch.utils._pytree, 'register_pytree_node'):
        print("✓ torch.utils._pytree.register_pytree_node exists")
        print()
        print("=" * 60)
        print("SUCCESS! XTTS is compatible with your PyTorch version.")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Test audio generation: python test_xtts.py")
        print("2. Record your voice: python scripts/record_reference_audio.py")
    else:
        print("❌ register_pytree_node not found")
        sys.exit(1)
except Exception as e:
    print(f"❌ _pytree check failed: {e}")
    sys.exit(1)
