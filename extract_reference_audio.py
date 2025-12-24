"""
Extract Reference Audio Clip
Extracts a segment from an MP3 file and saves as WAV for XTTS reference
"""
import subprocess
import sys
from pathlib import Path
import argparse


def parse_time(time_str):
    """
    Parse time string to seconds
    Supports formats: "5:30", "90", "1:23.5"
    """
    if ':' in time_str:
        parts = time_str.split(':')
        if len(parts) == 2:  # MM:SS
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        elif len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    else:
        return float(time_str)


def extract_audio_clip(
    input_file: str,
    start_time: str,
    end_time: str,
    output_name: str = "reference_voice.wav"
):
    """
    Extract audio clip from MP3 and save as WAV
    
    Args:
        input_file: Path to input MP3 file
        start_time: Start time (format: "5:30" or "90" for seconds)
        end_time: End time (format: "5:45" or "105" for seconds)
        output_name: Output filename (default: reference_voice.wav)
    """
    input_path = Path(input_file)
    
    # Validate input file
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_file}")
        sys.exit(1)
    
    # Parse times
    try:
        start_seconds = parse_time(start_time)
        end_seconds = parse_time(end_time)
    except ValueError as e:
        print(f"❌ Error parsing time: {e}")
        print("Use format like '5:30' (5 min 30 sec) or '330' (330 seconds)")
        sys.exit(1)
    
    # Calculate duration
    duration = end_seconds - start_seconds
    
    # Validate duration
    if duration <= 0:
        print("❌ Error: End time must be after start time")
        sys.exit(1)
    
    if duration > 30:
        print(f"⚠️  Warning: Duration is {duration:.1f}s (max recommended: 30s)")
        print("Trimming to 30 seconds...")
        duration = 30
        end_seconds = start_seconds + 30
    
    # Create output directory
    output_dir = Path("assets")
    output_dir.mkdir(exist_ok=True)
    
    output_path = output_dir / output_name
    
    print("=" * 60)
    print("Extracting Reference Audio Clip")
    print("=" * 60)
    print(f"Input:  {input_path}")
    print(f"Start:  {start_time} ({start_seconds:.1f}s)")
    print(f"End:    {end_time} ({end_seconds:.1f}s)")
    print(f"Duration: {duration:.1f}s")
    print(f"Output: {output_path}")
    print()
    
    # Build ffmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(input_path),
        "-ss", str(start_seconds),
        "-t", str(duration),
        "-ar", "24000",  # 24kHz sample rate (matches XTTS)
        "-ac", "1",      # Mono
        "-c:a", "pcm_s16le",  # 16-bit PCM
        "-y",            # Overwrite output
        str(output_path)
    ]
    
    try:
        # Run ffmpeg
        print("Processing...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Verify output
        if output_path.exists():
            file_size = output_path.stat().st_size / 1024
            print()
            print("✓ Success!")
            print(f"✓ Output: {output_path}")
            print(f"✓ Size: {file_size:.1f} KB")
            print(f"✓ Format: 24kHz WAV, mono, 16-bit")
            print()
            print("You can now use this file as reference audio:")
            print(f'  reference_audio=Path("{output_path}")')
        else:
            print("❌ Error: Output file was not created")
            sys.exit(1)
    
    except subprocess.CalledProcessError as e:
        print("❌ Error running ffmpeg:")
        print(e.stderr)
        print()
        print("Make sure ffmpeg is installed:")
        print("  Windows: Download from ffmpeg.org or use 'choco install ffmpeg'")
        print("  Linux: sudo apt install ffmpeg")
        print("  Mac: brew install ffmpeg")
        sys.exit(1)
    
    except FileNotFoundError:
        print("❌ Error: ffmpeg not found")
        print()
        print("Please install ffmpeg:")
        print("  Windows: Download from ffmpeg.org or use 'choco install ffmpeg'")
        print("  Linux: sudo apt install ffmpeg")
        print("  Mac: brew install ffmpeg")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Extract audio clip from MP3 for XTTS reference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from 5:30 to 5:45 (15 seconds)
  python extract_reference_audio.py audio.mp3 5:30 5:45
  
  # Extract from 90 to 105 seconds (15 seconds)
  python extract_reference_audio.py audio.mp3 90 105
  
  # Custom output name
  python extract_reference_audio.py audio.mp3 2:15 2:35 -o excited_voice.wav
  
  # Extract from 1 hour mark for 20 seconds
  python extract_reference_audio.py audio.mp3 1:00:00 1:00:20
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Input MP3 file path"
    )
    parser.add_argument(
        "start_time",
        help="Start time (format: MM:SS or seconds, e.g., '5:30' or '330')"
    )
    parser.add_argument(
        "end_time",
        help="End time (format: MM:SS or seconds, e.g., '5:45' or '345')"
    )
    parser.add_argument(
        "-o", "--output",
        default="reference_voice.wav",
        help="Output filename (default: reference_voice.wav)"
    )
    
    args = parser.parse_args()
    
    extract_audio_clip(
        args.input_file,
        args.start_time,
        args.end_time,
        args.output
    )


if __name__ == "__main__":
    main()
