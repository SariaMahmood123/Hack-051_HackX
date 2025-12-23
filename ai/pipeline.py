"""
Pipeline Manager
Coordinates the full text → audio → video pipeline
Handles GPU memory management and sequential execution
"""
from pathlib import Path
from typing import Optional, Dict
import uuid
from datetime import datetime

from .gemini_client import GeminiClient
from .xtts_wrapper import XTTSWrapper
from .sadtalker_wrapper import SadTalkerWrapper


class PipelineManager:
    """
    Manages the full LUMEN generation pipeline
    
    Flow:
    1. Text generation (Gemini API - no GPU)
    2. TTS generation (XTTS - GPU)
    3. Video generation (SadTalker - GPU)
    
    Note: XTTS and SadTalker run sequentially to avoid GPU memory conflicts
    """
    
    def __init__(
        self,
        gemini_api_key: str,
        xtts_model_path: Optional[Path] = None,
        sadtalker_model_path: Optional[Path] = None,
        reference_audio: Optional[Path] = None,
        reference_image: Optional[Path] = None,
        output_dir: Path = Path("outputs")
    ):
        """
        Initialize pipeline with all components
        
        Args:
            gemini_api_key: API key for Gemini
            xtts_model_path: Path to XTTS model
            sadtalker_model_path: Path to SadTalker model
            reference_audio: Default reference audio for voice cloning
            reference_image: Default avatar image
            output_dir: Directory for generated files
        """
        self.gemini = GeminiClient(api_key=gemini_api_key)
        self.xtts = XTTSWrapper(model_path=xtts_model_path)
        self.sadtalker = SadTalkerWrapper(model_path=sadtalker_model_path)
        
        self.reference_audio = reference_audio
        self.reference_image = reference_image
        self.output_dir = output_dir
        
        # Create output directories
        (output_dir / "audio").mkdir(parents=True, exist_ok=True)
        (output_dir / "video").mkdir(parents=True, exist_ok=True)
    
    async def generate_full_response(
        self,
        prompt: str,
        conversation_history: Optional[list] = None,
        reference_audio: Optional[Path] = None,
        reference_image: Optional[Path] = None
    ) -> Dict:
        """
        Execute full pipeline: text → audio → video
        
        Args:
            prompt: User input text
            conversation_history: Previous conversation context
            reference_audio: Override default reference audio
            reference_image: Override default reference image
        
        Returns:
            Dict containing:
                - text: Generated response text
                - audio_path: Path to generated audio
                - video_path: Path to generated video
                - request_id: Unique request identifier
                - timestamp: Generation timestamp
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Use provided or default references
        audio_ref = reference_audio or self.reference_audio
        image_ref = reference_image or self.reference_image
        
        if not audio_ref or not image_ref:
            raise ValueError("Reference audio and image must be provided")
        
        try:
            # Step 1: Generate text with Gemini (API call, no GPU)
            print(f"📝 Generating text response...")
            response_text = await self.gemini.generate_async(prompt, conversation_history)
            
            # Step 2: Generate audio with XTTS (GPU)
            print(f"🎤 Synthesizing speech...")
            audio_path = self.output_dir / "audio" / f"{request_id}.wav"
            await self.xtts.synthesize_async(
                text=response_text,
                reference_audio=audio_ref,
                output_path=audio_path
            )
            
            # Step 3: Generate video with SadTalker (GPU)
            # Note: Running after XTTS to avoid GPU memory conflicts
            print(f"🎬 Generating video...")
            video_path = self.output_dir / "video" / f"{request_id}.mp4"
            await self.sadtalker.generate_async(
                audio_path=audio_path,
                reference_image=image_ref,
                output_path=video_path
            )
            
            print(f"✅ Pipeline complete: {request_id}")
            
            return {
                "text": response_text,
                "audio_path": str(audio_path),
                "video_path": str(video_path),
                "request_id": request_id,
                "timestamp": timestamp
            }
        
        except Exception as e:
            # Clean up partial outputs on failure
            print(f"❌ Pipeline failed: {str(e)}")
            raise RuntimeError(f"Pipeline execution failed: {str(e)}")
    
    def cleanup(self):
        """Unload models and free GPU memory"""
        self.xtts.unload_model()
        self.sadtalker.unload_model()
        print("🧹 Pipeline cleanup complete")
