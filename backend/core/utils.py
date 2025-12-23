"""
Utility functions for the backend
"""
from pathlib import Path
import hashlib
import time
from typing import Optional


def generate_cache_key(text: str, reference: Optional[str] = None) -> str:
    """
    Generate a cache key for generated content
    
    Args:
        text: Input text
        reference: Optional reference file path
    
    Returns:
        MD5 hash of the inputs
    """
    content = f"{text}:{reference or ''}"
    return hashlib.md5(content.encode()).hexdigest()


def get_file_duration(file_path: Path) -> float:
    """
    Get duration of audio/video file
    
    Args:
        file_path: Path to media file
    
    Returns:
        Duration in seconds
    """
    # Not implemented - requires moviepy library
    return 0.0


def cleanup_old_files(directory: Path, max_age_hours: int = 24):
    """
    Clean up old generated files
    
    Args:
        directory: Directory to clean
        max_age_hours: Maximum age of files in hours
    """
    if not directory.exists():
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for file_path in directory.glob("*.*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    print(f"Deleted old file: {file_path.name}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")


def ensure_file_exists(file_path: Path) -> bool:
    """
    Check if a file exists and is readable
    
    Args:
        file_path: Path to check
    
    Returns:
        True if file exists and is readable
    """
    return file_path.exists() and file_path.is_file()
