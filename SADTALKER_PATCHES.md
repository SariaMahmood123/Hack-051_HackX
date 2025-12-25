# SadTalker Setup & Patches Applied

## Installation

SadTalker is installed in `SadTalker/SadTalker-main/` directory with required checkpoints.

## Compatibility Patches Applied

The following patches were manually applied to fix compatibility issues with our environment:

### 1. **basicsr - Torchvision Import Fix**
- **File**: `SadTalker/SadTalker-main/src/facerender/sync_batchnorm/batchnorm.py` (via basicsr dependency)
- **Issue**: `ModuleNotFoundError: 'torchvision.transforms.functional_tensor'`
- **Fix**: Updated imports to use correct torchvision structure
- **Status**: Applied to `.venv/Lib/site-packages/basicsr/data/degradations.py`

### 2. **NumPy Deprecation Fix**
- **File**: `SadTalker/SadTalker-main/src/face3d/models/arcface_torch/my_awing_arch.py`
- **Issue**: `AttributeError: module 'numpy' has no attribute 'float'`
- **Fix**: Replaced `np.float` with `np.float64`
- **Lines**: Throughout the file

### 3. **NumPy Array Construction Fix**
- **File**: `SadTalker/SadTalker-main/src/utils/preprocess.py`
- **Issue**: `ValueError: setting an array element with a sequence`
- **Fix**: Added explicit `float()` conversions at line 101
- **Status**: Applied

### 4. **FFmpeg Subprocess Fix**
- **File**: `SadTalker/SadTalker-main/src/utils/videoio.py`
- **Issue**: `os.system()` failing with filenames containing special characters
- **Fix**: Changed to `subprocess.run()` with proper list arguments
- **Lines**: 27-40, 57-59
- **Added**: Import subprocess, debug output, temp file handling

### 5. **Exception Syntax Fix**
- **File**: `SadTalker/SadTalker-main/src/utils/croper.py`
- **Issue**: `TypeError: exceptions must derive from BaseException`
- **Fix**: Changed `raise 'string'` to `raise RuntimeError('string')`
- **Status**: Applied

### 6. **GFPGAN Device Handling** (Optional - for GPU mode)
- **File**: `SadTalker/SadTalker-main/src/utils/face_enhancer.py`
- **Issue**: GFPGAN doesn't respect device parameter
- **Fix**: Added device parameter to enhancer functions
- **Status**: Applied but not used (GPU mode disabled on Windows)

### 7. **Animate Device Passing** (Optional - for GPU mode)
- **File**: `SadTalker/SadTalker-main/src/facerender/animate.py`
- **Issue**: Device not passed to enhancer
- **Fix**: Pass `self.device` to enhancer calls
- **Status**: Applied but not used (GPU mode disabled on Windows)

## Current Configuration

- **Mode**: CPU-only (Windows production config)
- **Resolution**: 256x256 internal, 256px output
- **Enhancement**: Disabled (GFPGAN requires GPU)
- **Preprocessing**: 'crop' mode
- **Performance**: ~5 minutes for 15-second video on CPU

## GPU Support

GPU mode is **NOT supported on Windows** due to PyTorch CUDA loading bugs that cause indefinite hangs.

For GPU acceleration, use:
- **WSL2**: Run in Linux environment inside Windows with GPU passthrough
- **Docker**: Use NVIDIA container toolkit
- **Linux**: Native Ubuntu/Debian deployment

See project README for WSL2/Docker setup instructions.

## Notes

- All patches are applied during initial setup
- Patches modify external library code in `.venv/` and `SadTalker/` directories
- If dependencies are reinstalled, patches must be reapplied
- GPU patches (6 & 7) are present but unused in Windows CPU mode
