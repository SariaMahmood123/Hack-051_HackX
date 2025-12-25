"""
Patch generator.py to force GPU usage and prevent CPU fallback
"""
from pathlib import Path

def patch_generator():
    file_path = Path("SadTalker/SadTalker-main/src/facerender/modules/generator.py")
    
    print(f"Patching {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Patch both forward methods to enforce device
    old_forward = """    def forward(self, source_image, kp_driving, kp_source):
        # Encoding (downsampling) part
        out = self.first(source_image)"""
    
    new_forward = """    def forward(self, source_image, kp_driving, kp_source):
        # Force inputs to model's device to prevent CPU fallback
        device = next(self.parameters()).device
        source_image = source_image.to(device)
        
        # Encoding (downsampling) part
        out = self.first(source_image)"""
    
    # Count occurrences
    count = content.count(old_forward)
    print(f"Found {count} forward methods to patch")
    
    if count > 0:
        content = content.replace(old_forward, new_forward)
        print(f"✓ Patched {count} forward methods with device enforcement")
    
    # Save if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ Successfully patched {file_path}")
        print("All generator forward passes now enforce GPU device")
        return True
    else:
        print("\n⚠ No changes needed - patch already applied")
        return False

if __name__ == "__main__":
    try:
        patch_generator()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
