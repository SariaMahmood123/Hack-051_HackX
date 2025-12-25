from pathlib import Path
from PIL import Image

# Load image
img = Image.open('assets/mkbhd.jpg')
print(f'Original: {img.size} {img.mode}')

# Ensure RGB
if img.mode != 'RGB':
    img = img.convert('RGB')
    
# Resize if too large
max_size = 512
if max(img.size) > max_size:
    ratio = max_size / max(img.size)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    img = img.resize(new_size, Image.Resampling.LANCZOS)
    print(f'Resized: {img.size}')
    
# Save
img.save('assets/mkbhd_512.jpg', quality=95)
print('Saved: assets/mkbhd_512.jpg')
