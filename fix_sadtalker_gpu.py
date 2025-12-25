"""
Patch SadTalker's make_animation.py to ensure GPU tensors stay on GPU.
The issue: models are on GPU but intermediate tensors get moved to CPU.
"""

import re
from pathlib import Path

def apply_patch():
    file_path = Path("SadTalker/SadTalker-main/src/facerender/modules/make_animation.py")
    
    print(f"Patching {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Patch 1: Add device parameter to make_animation function
    old_signature = """def make_animation(source_image, source_semantics, target_semantics,
                            generator, kp_detector, he_estimator, mapping, 
                            yaw_c_seq=None, pitch_c_seq=None, roll_c_seq=None,
                            use_exp=True, use_half=False):"""
    
    new_signature = """def make_animation(source_image, source_semantics, target_semantics,
                            generator, kp_detector, he_estimator, mapping, 
                            yaw_c_seq=None, pitch_c_seq=None, roll_c_seq=None,
                            use_exp=True, use_half=False):
    # Patch: Ensure all tensors stay on the same device as the models
    device = next(generator.parameters()).device"""
    
    if old_signature in content and "device = next(generator.parameters()).device" not in content:
        content = content.replace(old_signature, new_signature)
        print("✓ Added device detection")
    else:
        print("⚠ Device detection already present or signature not found")
    
    # Patch 2: Ensure kp_canonical stays on GPU
    old_kp_line = "        kp_canonical = kp_detector(source_image)"
    new_kp_line = "        kp_canonical = kp_detector(source_image)\n        # Ensure stays on GPU\n        for k, v in kp_canonical.items():\n            if isinstance(v, torch.Tensor):\n                kp_canonical[k] = v.to(device)"
    
    if old_kp_line in content and "Ensure stays on GPU" not in content:
        content = content.replace(old_kp_line, new_kp_line)
        print("✓ Patched kp_canonical to stay on GPU")
    else:
        print("⚠ kp_canonical GPU patch already applied")
    
    # Save if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ Successfully patched {file_path}")
        print("GPU tensors will now stay on GPU during rendering")
        return True
    else:
        print("\n⚠ No changes needed - patch already applied")
        return False

if __name__ == "__main__":
    try:
        apply_patch()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
