#!/usr/bin/env python3
"""Fix basicsr torchvision imports in WSL environment"""

import os
import sys

# Path to degradations.py in WSL venv
degradations_path = "/mnt/d/Hack-051_HackX/.venv-wsl/lib/python3.10/site-packages/basicsr/data/degradations.py"

if not os.path.exists(degradations_path):
    print(f"❌ File not found: {degradations_path}")
    sys.exit(1)

print(f"Patching {degradations_path}...")

# Read the file
with open(degradations_path, 'r') as f:
    content = f.read()

# Check if already patched
if "from torchvision.transforms import functional as F" in content:
    print("✓ File is already patched")
    sys.exit(0)

# Apply patches
old_imports = """from torchvision.transforms.functional_tensor import rgb_to_grayscale"""

new_imports = """# Fixed for newer torchvision
from torchvision.transforms import functional as F
rgb_to_grayscale = F.rgb_to_grayscale"""

content = content.replace(old_imports, new_imports)

# Write back
with open(degradations_path, 'w') as f:
    f.write(content)

print("✓ Patch applied successfully")
