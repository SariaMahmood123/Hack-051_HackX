"""
Generate audio with reference voice using CPU (reliable)
"""
import sys
import time
from pathlib import Path

print("="*60)
print("XTTS Voice Cloning - CPU Mode")
print("="*60)
print()

# Setup
reference = Path("assets/reference_voice.wav")
output = Path("outputs/audio/xtts_final_output.wav")
output.parent.mkdir(parents=True, exist_ok=True)

text = (
    "Hello! This is a demonstration of X T T S voice cloning technology. "
    "I am speaking with a cloned voice that matches the reference audio. "
    "The system can generate natural-sounding speech in multiple languages. "
    "This is the power of AI-driven text to speech synthesis!"
)

print(f"[1/4] Reference: {reference}")
print(f"[2/4] Output: {output}")
print(f"[3/4] Text: {len(text)} characters")
print()

# Load TTS
print("[4/4] Generating audio...")
print("(CPU mode - reliable but slower)")
print()

from TTS.api import TTS

start_total = time.time()

# Load model (CPU)
print("Loading model...", end=" ", flush=True)
start = time.time()
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
print(f"Done ({time.time() - start:.1f}s)")

# Generate audio
print("Synthesizing audio...", end=" ", flush=True)
start = time.time()
tts.tts_to_file(
    text=text,
    file_path=str(output),
    speaker_wav=str(reference),
    language="en"
)
synth_time = time.time() - start
print(f"Done ({synth_time:.2f}s)")

total_time = time.time() - start_total

# Results
print()
print("="*60)
print("[SUCCESS] Audio Generated!")
print("="*60)
print()
print(f"Output File: {output.absolute()}")
print(f"File Size: {output.stat().st_size / 1024:.1f} KB")
print(f"Synthesis Time: {synth_time:.2f} seconds")
print(f"Total Time: {total_time:.1f} seconds")
print()
print("Play the audio file to hear the voice-cloned result!")
print()
print("The voice should match the reference audio characteristics")
print("while speaking the new text content.")
