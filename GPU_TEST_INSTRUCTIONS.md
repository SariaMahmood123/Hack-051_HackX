# GPU-Accelerated SadTalker Test Instructions

## Changes Applied

### 1. **Resolution & Quality**
- ✅ Changed from 256x256 to **512x512** resolution
- ✅ Enabled **GFPGAN v1.4** face enhancement (GFPGANv1.4.pth found)
- ✅ Using **full preprocessing** mode (not crop)
- ✅ Confirmed **still mode disabled** (allows head movement)

### 2. **GPU Enforcement Patches**
- ✅ `make_animation.py`: Forces all input tensors to GPU device
- ✅ `generator.py`: Added device enforcement in both forward() methods
- ✅ All intermediate tensors pinned to model's device

### 3. **Monitoring**
- Created `monitor_gpu.py` for real-time GPU utilization tracking

## How to Test

### Terminal 1: GPU Monitor (run first)
```bash
wsl bash -c "cd /mnt/d/Hack-051_HackX && source .venv-wsl/bin/activate && python monitor_gpu.py"
```

### Terminal 2: Run Video Generation
```bash
wsl bash -c "cd /mnt/d/Hack-051_HackX && source .venv-wsl/bin/activate && python test_sadtalker_wsl_gpu.py"
```

## Expected Results

### CPU Rendering (BEFORE):
- Face Renderer speed: ~1.0-1.1 it/s
- GPU utilization: 0-10%
- Time for 385 frames: ~6-7 minutes

### GPU Rendering (TARGET):
- Face Renderer speed: **3-5+ it/s** (3-5x faster)
- GPU utilization: **60-90%** during Face Renderer phase
- Time for 385 frames: **~2-3 minutes** (estimated)
- Resolution: **512x512** (4x more pixels than before)
- Quality: Enhanced with GFPGAN

## What to Watch For

1. **GPU Memory Usage**: Should spike to ~2-4 GB during rendering
2. **GPU Utilization**: Must be >50% during "Face Renderer" phase
3. **Speed**: Look for it/s >= 3.0 (if still ~1.0, GPU not being used)
4. **Output**: Check `outputs/video/test_wsl_gpu.mp4` for 512x512 resolution

## Troubleshooting

If GPU utilization stays at 0%:
1. Check that all tensors are on CUDA: The patches should handle this
2. Verify PyTorch CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
3. Check nvidia-smi shows the python process using GPU memory

If speed is still ~1.0 it/s, the render is happening on CPU despite patches.
