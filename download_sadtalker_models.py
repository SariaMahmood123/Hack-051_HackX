"""
Download SadTalker model checkpoints (Windows-compatible)
"""
import urllib.request
from pathlib import Path
from tqdm import tqdm

project_root = Path(__file__).parent
checkpoints_dir = project_root / "SadTalker" / "SadTalker-main" / "checkpoints"
gfpgan_dir = project_root / "SadTalker" / "SadTalker-main" / "gfpgan" / "weights"

# Create directories
checkpoints_dir.mkdir(parents=True, exist_ok=True)
gfpgan_dir.mkdir(parents=True, exist_ok=True)

# Model URLs
models = {
    "checkpoints": [
        ("mapping_00109-model.pth.tar", "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar"),
        ("mapping_00229-model.pth.tar", "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar"),
        ("SadTalker_V0.0.2_256.safetensors", "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors"),
        ("SadTalker_V0.0.2_512.safetensors", "https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors"),
    ],
    "gfpgan": [
        ("alignment_WFLW_4HG.pth", "https://github.com/xinntao/facexlib/releases/download/v0.1.0/alignment_WFLW_4HG.pth"),
        ("detection_Resnet50_Final.pth", "https://github.com/xinntao/facexlib/releases/download/v0.1.0/detection_Resnet50_Final.pth"),
        ("GFPGANv1.4.pth", "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"),
        ("parsing_parsenet.pth", "https://github.com/xinntao/facexlib/releases/download/v0.2.2/parsing_parsenet.pth"),
    ]
}

def download_file(url, dest_path):
    """Download file with progress bar"""
    if dest_path.exists():
        print(f"✓ {dest_path.name} already exists, skipping")
        return
    
    print(f"Downloading {dest_path.name}...")
    
    try:
        with urllib.request.urlopen(url) as response:
            total_size = int(response.headers.get('content-length', 0))
            
            with open(dest_path, 'wb') as f:
                if total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                        while True:
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                            pbar.update(len(chunk))
                else:
                    f.write(response.read())
        
        print(f"✓ Downloaded {dest_path.name}")
    except Exception as e:
        print(f"✗ Failed to download {dest_path.name}: {e}")
        if dest_path.exists():
            dest_path.unlink()  # Remove partial file

def main():
    print("=" * 70)
    print("SadTalker Model Downloader")
    print("=" * 70)
    print(f"Downloading to: {checkpoints_dir}")
    print("Total size: ~2-3 GB (this may take a while)")
    print()
    
    # Download checkpoint models
    print("📦 Downloading SadTalker checkpoints...")
    for filename, url in models["checkpoints"]:
        dest = checkpoints_dir / filename
        download_file(url, dest)
    
    print()
    print("📦 Downloading GFPGAN enhancer models...")
    for filename, url in models["gfpgan"]:
        dest = gfpgan_dir / filename
        download_file(url, dest)
    
    print()
    print("=" * 70)
    print("✅ Download complete!")
    print("=" * 70)
    print()
    print("Next step: Run test_sadtalker.py to verify installation")

if __name__ == "__main__":
    main()
