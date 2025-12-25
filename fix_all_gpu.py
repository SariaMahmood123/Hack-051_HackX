"""
Comprehensive GPU enforcement patch for all SadTalker modules
"""
from pathlib import Path

def patch_keypoint_detector():
    """Add device enforcement to keypoint detector"""
    file_path = Path("SadTalker/SadTalker-main/src/facerender/modules/keypoint_detector.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Patch KPDetector forward
    old = """    def forward(self, x):
        if self.scale_factor != 1:
            x = self.down(x)

        feature_map = self.predictor(x)"""
    
    new = """    def forward(self, x):
        # Force input to model's device
        device = next(self.parameters()).device
        x = x.to(device)
        
        if self.scale_factor != 1:
            x = self.down(x)

        feature_map = self.predictor(x)"""
    
    if old in content:
        content = content.replace(old, new)
        print("✓ Patched KPDetector.forward()")
    
    # Patch HEEstimator forward
    old_he = """    def forward(self, x):
        feature_map = self.predictor(x)"""
    
    new_he = """    def forward(self, x):
        # Force input to model's device
        device = next(self.parameters()).device
        x = x.to(device)
        
        feature_map = self.predictor(x)"""
    
    if old_he in content:
        content = content.replace(old_he, new_he)
        print("✓ Patched HEEstimator.forward()")
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Patched {file_path}")
        return True
    return False

def patch_mapping():
    """Add device enforcement to mapping network"""
    file_path = Path("SadTalker/SadTalker-main/src/facerender/modules/mapping.py")
    
    if not file_path.exists():
        print(f"⚠ {file_path} not found")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Find and patch forward method
    if "def forward(self, source_semantics):" in content:
        old = """    def forward(self, source_semantics):
        out = {}"""
        new = """    def forward(self, source_semantics):
        # Force input to model's device
        device = next(self.parameters()).device
        source_semantics = source_semantics.to(device)
        
        out = {}"""
        
        if old in content:
            content = content.replace(old, new)
            print("✓ Patched MappingNet.forward()")
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Patched {file_path}")
        return True
    return False

def verify_patches():
    """Verify all patches are in place"""
    print("\n" + "="*60)
    print("Verifying GPU enforcement patches...")
    print("="*60)
    
    files_to_check = [
        ("SadTalker/SadTalker-main/src/facerender/modules/make_animation.py", 
         "device = next(generator.parameters()).device"),
        ("SadTalker/SadTalker-main/src/facerender/modules/generator.py",
         "device = next(self.parameters()).device"),
        ("SadTalker/SadTalker-main/src/facerender/modules/keypoint_detector.py",
         "device = next(self.parameters()).device"),
    ]
    
    all_ok = True
    for file_path, check_string in files_to_check:
        path = Path(file_path)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if check_string in content:
                print(f"✓ {path.name}: Device enforcement present")
            else:
                print(f"✗ {path.name}: Missing device enforcement")
                all_ok = False
        else:
            print(f"✗ {path.name}: File not found")
            all_ok = False
    
    return all_ok

if __name__ == "__main__":
    print("Applying comprehensive GPU enforcement patches...\n")
    
    patch_keypoint_detector()
    patch_mapping()
    
    print()
    if verify_patches():
        print("\n✅ All GPU enforcement patches verified!")
    else:
        print("\n⚠ Some patches may be missing")
