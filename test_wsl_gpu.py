import torch

print("PyTorch:", torch.__version__)
print("CUDA Available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("Device:", torch.cuda.get_device_name(0))
    x = torch.randn(1000, 1000).cuda()
    print("✓ GPU tensor creation successful")
    print("Memory allocated:", torch.cuda.memory_allocated() / 1024**2, "MB")
else:
    print("❌ CUDA not available")
