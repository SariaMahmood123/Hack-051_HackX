import torch

# Clear CUDA cache
torch.cuda.empty_cache()
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory allocated: {torch.cuda.memory_allocated(0) / 1024**2:.2f} MB")
    print(f"Memory cached: {torch.cuda.memory_reserved(0) / 1024**2:.2f} MB")
    print("✓ GPU reset complete")
