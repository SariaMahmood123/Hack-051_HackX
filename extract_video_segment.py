#!/usr/bin/env python3
"""
Extract reference video segment for motion style analysis
"""
import subprocess
from pathlib import Path

def extract_video_segment(input_path, start_time, end_time, output_path):
    """
    Extract video segment using ffmpeg
    
    Args:
        input_path: Source video path
        start_time: Start timestamp (HH:MM:SS)
        end_time: End timestamp (HH:MM:SS)
        output_path: Output video path
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    print(f"Input path: {input_file}")
    print(f"Checking existence...")
    
    # For WSL, check existence differently
    # Just proceed - let ffmpeg handle file not found
    
    print(f"Extracting segment from {input_file.name}...")
    print(f"  Start: {start_time}")
    print(f"  End: {end_time}")
    print(f"  Output: {output_file}")
    print()
    
    # Convert to WSL path if needed
    if str(input_file).startswith('D:'):
        wsl_input = str(input_file).replace('D:', '/mnt/d').replace('\\', '/')
        wsl_output = str(output_file).replace('D:', '/mnt/d').replace('\\', '/')
    else:
        wsl_input = str(input_file)
        wsl_output = str(output_file)
    
    # ffmpeg command to extract segment
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-ss', start_time,  # Start time
        '-to', end_time,  # End time
        '-i', wsl_input,  # Input file
        '-c:v', 'libx264',  # Video codec
        '-preset', 'fast',  # Encoding speed
        '-crf', '23',  # Quality (18-28, lower=better)
        '-c:a', 'aac',  # Audio codec
        '-b:a', '128k',  # Audio bitrate
        wsl_output  # Output file
    ]
    
    print("Running ffmpeg...")
    try:
        result = subprocess.run(
            ['wsl', 'bash', '-c', ' '.join(cmd)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            if output_file.exists():
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"✅ Video segment extracted successfully")
                print(f"   Size: {size_mb:.2f} MB")
                return True
            else:
                print(f"❌ Output file not created")
                return False
        else:
            print(f"❌ ffmpeg failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    input_video = r"D:\Hack-051_HackX\assets\Every Mistake I Made in 2025 - Marques Brownlee (1080p, h264).mp4"
    output_video = r"D:\Hack-051_HackX\assets\reference_motion.mp4"
    
    print("=" * 60)
    print("VIDEO SEGMENT EXTRACTION")
    print("=" * 60)
    print()
    
    success = extract_video_segment(
        input_path=input_video,
        start_time="00:00:20",
        end_time="00:01:00",
        output_path=output_video
    )
    
    if success:
        print()
        print("=" * 60)
        print("✅ EXTRACTION COMPLETE")
        print("=" * 60)
        print()
        print(f"Reference video: {output_video}")
        print()
        print("Next step: Extract motion style profile")
        print("  Run: python extract_motion_style.py")
    else:
        print()
        print("❌ Extraction failed")
