# AI Model Wrappers

Python wrappers for AI models used in LUMEN pipeline.

## Components

### `gemini_client.py`
Wrapper for Google Gemini 2.0 Flash API
- Handles conversational text generation
- Manages chat history
- API-based (no local GPU required)

### `xtts_wrapper.py`
Wrapper for XTTS v2 (Coqui TTS)
- Text-to-speech with voice cloning
- Requires reference audio for voice cloning
- GPU-accelerated inference
- Auto-downloads model on first use

### `sadtalker_wrapper.py`
Wrapper for SadTalker
- Generates talking-head videos from audio + image
- Requires reference portrait image
- GPU-accelerated inference
- Checkpoints must be downloaded separately

### `pipeline.py`
Full pipeline orchestrator
- Coordinates: Text → Audio → Video
- Sequential execution to avoid GPU memory conflicts
- Manages model loading/unloading
- Handles output file management

## Usage Example

```python
from ai.pipeline import PipelineManager
from pathlib import Path

# Initialize pipeline
pipeline = PipelineManager(
    gemini_api_key="your_key",
    reference_audio=Path("assets/reference_voice.wav"),
    reference_image=Path("assets/avatar.jpg"),
    output_dir=Path("outputs")
)

# Generate full response
result = await pipeline.generate_full_response(
    prompt="Hello, how are you?",
    conversation_history=[]
)

print(f"Text: {result['text']}")
print(f"Video: {result['video_path']}")
```

## GPU Memory Management

Models run sequentially to avoid VRAM conflicts:
1. Gemini (API call, no GPU)
2. XTTS (GPU)
3. SadTalker (GPU)

Each model can be loaded/unloaded as needed.
