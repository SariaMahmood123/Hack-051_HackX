"""
GPU Monitor for SadTalker - Run in separate terminal
"""
import subprocess
import time
import sys

print("=" * 70)
print("GPU MONITOR - Watching for SadTalker GPU utilization")
print("=" * 70)
print("Will display GPU usage every 2 seconds")
print("Press Ctrl+C to stop\n")

try:
    while True:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total,temperature.gpu", 
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            timestamp, name, util, mem_used, mem_total, temp = result.stdout.strip().split(", ")
            mem_pct = (int(mem_used) / int(mem_total)) * 100
            
            print(f"[{timestamp}] GPU: {util:>3}% | Memory: {mem_used}/{mem_total} MB ({mem_pct:.1f}%) | Temp: {temp}°C")
            
            # Alert if GPU usage is suspiciously low during expected rendering
            if int(util) < 10:
                print("  ⚠️  WARNING: GPU utilization < 10% - may be using CPU!")
        else:
            print("Failed to query GPU")
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n\nMonitoring stopped.")
    sys.exit(0)
