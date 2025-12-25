"""
Pipeline Manager - ARCHITECTED SYSTEM
Coordinates the full text → audio → video pipeline with intent propagation.

ARCHITECTURAL DESIGN:
- Gemini → structured script intent (pause, emphasis, sentence boundaries)
- XTTS → segmented audio + timing map  
- SadTalker → motion proposals (3 stages: coeffs, govern, render)
- Motion Governor → director (audio + script intent fusion)

This is NOT a hack. This is an intentional, coherent system.
"""
from pathlib import Path
from typing import Optional, Dict, Tuple
import uuid
from datetime import datetime
import logging

from .gemini_client import GeminiClient
from .xtts_wrapper import XTTSWrapper
from .sadtalker_wrapper import SadTalkerWrapper
from .script_intent import ScriptIntent, IntentTimingMap, create_simple_intent
from .motion_governor import STYLE_PRESETS, StyleProfile

logger = logging.getLogger("lumen")


class PipelineManager:
    """
    ARCHITECTED PIPELINE MANAGER
    
    This is the PRODUCT, not a demo.
    
    Flow (Intent-Aware):
        User Prompt
        ↓
        Gemini (generate_with_intent)
        → Script text
        → ScriptIntent (pause, emphasis, sentence_end)
        ↓
        XTTS (synthesize_with_intent)
        → Segmented audio with explicit silence
        → IntentTimingMap (audio time → intent)
        ↓
        SadTalker (3-stage architecture)
        1. generate_coeffs() - motion proposals
        2. govern_coeffs() - director (audio + script intent)
        3. render_video() - final rendering
        ↓
        Final video (coherent, intentional motion)
    
    Quality Features:
    - CPU-based TTS for numerical stability (24kHz, FP32)
    - GPU-based SadTalker for rendering (512px)
    - Motion Governor for expression control
    - Intent propagation from script → audio → motion
    """
    
    def __init__(
        self,
        gemini_api_key: str,
        xtts_model_path: Optional[Path] = None,
        sadtalker_model_path: Optional[Path] = None,
        reference_audio: Optional[Path] = None,
        reference_image: Optional[Path] = None,
        output_dir: Path = Path("outputs"),
        motion_style: str = "calm_tech",
        enable_intent: bool = True,
        enable_governor: bool = True
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
            motion_style: Default motion style (calm_tech, energetic, lecturer)
            enable_intent: Enable intent-aware generation
            enable_governor: Enable Motion Governor
        """
        self.gemini = GeminiClient(api_key=gemini_api_key)
        self.xtts = XTTSWrapper(model_path=xtts_model_path)
        self.sadtalker = SadTalkerWrapper(model_path=sadtalker_model_path)
        
        self.reference_audio = reference_audio
        self.reference_image = reference_image
        self.output_dir = output_dir
        self.motion_style = motion_style
        self.enable_intent = enable_intent
        self.enable_governor = enable_governor
        
        # Create output directories
        (output_dir / "audio").mkdir(parents=True, exist_ok=True)
        (output_dir / "video").mkdir(parents=True, exist_ok=True)
        (output_dir / "intent").mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[Pipeline] Initialized with intent={'ON' if enable_intent else 'OFF'}, governor={'ON' if enable_governor else 'OFF'}")
    
    async def generate_full_response(
        self,
        prompt: str,
        reference_audio: Optional[Path] = None,
        reference_image: Optional[Path] = None,
        motion_style: Optional[str] = None,
        enable_intent: Optional[bool] = None,
        enable_governor: Optional[bool] = None,
        fps: int = 25
    ) -> Dict:
        """
        Execute full ARCHITECTED pipeline: prompt → script intent → audio → video
        
        This is the PRODUCT method that demonstrates the entire system.
        
        Args:
            prompt: User input text
            reference_audio: Override default reference audio
            reference_image: Override default reference image
            motion_style: Override default motion style
            enable_intent: Override intent setting
            enable_governor: Override governor setting
            fps: Frames per second
        
        Returns:
            Dict containing:
                - text: Generated response text
                - script_intent: ScriptIntent object (if enabled)
                - audio_path: Path to generated audio
                - intent_timing_map: IntentTimingMap (if enabled)
                - video_path: Path to generated video
                - request_id: Unique request identifier
                - timestamp: Generation timestamp
                - metadata: System state information
        """
        request_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Override settings
        audio_ref = reference_audio or self.reference_audio
        image_ref = reference_image or self.reference_image
        style = motion_style or self.motion_style
        use_intent = enable_intent if enable_intent is not None else self.enable_intent
        use_governor = enable_governor if enable_governor is not None else self.enable_governor
        
        if not audio_ref or not image_ref:
            raise ValueError("Reference audio and image must be provided")
        
        logger.info(f"[Pipeline] ========== REQUEST {request_id} ==========")
        logger.info(f"[Pipeline] Prompt: {prompt[:60]}...")
        logger.info(f"[Pipeline] Intent: {'ON' if use_intent else 'OFF'}")
        logger.info(f"[Pipeline] Governor: {'ON' if use_governor else 'OFF'}")
        logger.info(f"[Pipeline] Style: {style}")
        
        try:
            # STAGE 1: Generate script with intent
            logger.info(f"[Pipeline] === STAGE 1: GEMINI ===")
            
            if use_intent:
                response_text, script_intent = self.gemini.generate_with_intent(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=500
                )
                
                # Save intent
                intent_path = self.output_dir / "intent" / f"{request_id}_script.json"
                script_intent.save(intent_path)
                logger.info(f"[Pipeline] ✓ Script intent: {len(script_intent.segments)} segments")
            else:
                response_text = self.gemini.generate(prompt, temperature=0.7, max_tokens=150)
                script_intent = create_simple_intent(response_text, pause_after=0.3)
                logger.info(f"[Pipeline] ✓ Plain text (no intent)")
            
            # STAGE 2: Generate audio with timing
            logger.info(f"[Pipeline] === STAGE 2: XTTS ===")
            audio_path = self.output_dir / "audio" / f"{request_id}.wav"
            
            if use_intent and script_intent:
                audio_path, intent_timing_map = self.xtts.synthesize_with_intent(
                    script_intent=script_intent,
                    reference_audio=audio_ref,
                    output_path=audio_path,
                    fps=fps
                )
                
                # Save timing map
                if intent_timing_map:
                    timing_path = self.output_dir / "intent" / f"{request_id}_timing.json"
                    intent_timing_map.save(timing_path)
                    logger.info(f"[Pipeline] ✓ Intent-aware audio: {intent_timing_map.num_frames} frames")
            else:
                self.xtts.synthesize(
                    text=response_text,
                    reference_audio=audio_ref,
                    output_path=audio_path
                )
                intent_timing_map = None
                logger.info(f"[Pipeline] ✓ Plain audio (no timing)")
            
            # STAGE 3: Generate video (3-stage architecture)
            logger.info(f"[Pipeline] === STAGE 3: SADTALKER ===")
            video_path = self.output_dir / "video" / f"{request_id}.mp4"
            
            self.sadtalker.generate(
                audio_path=audio_path,
                reference_image=image_ref,
                output_path=video_path,
                fps=fps,
                enhancer=None,  # Can enable gfpgan
                enable_motion_governor=use_governor,
                motion_style=style,
                intent_timing_map=intent_timing_map  # ARCHITECTURAL KEY
            )
            
            logger.info(f"[Pipeline] ========== COMPLETE {request_id} ==========")
            
            return {
                "text": response_text,
                "script_intent": script_intent.to_dict() if script_intent else None,
                "audio_path": str(audio_path),
                "intent_timing_map": intent_timing_map.to_dict() if intent_timing_map else None,
                "video_path": str(video_path),
                "request_id": request_id,
                "timestamp": timestamp,
                "metadata": {
                    "intent_enabled": use_intent,
                    "governor_enabled": use_governor,
                    "motion_style": style,
                    "fps": fps
                }
            }
        
        except Exception as e:
            logger.error(f"[Pipeline] FAILED: {e}", exc_info=True)
            raise RuntimeError(f"Pipeline execution failed: {e}")
    
    def cleanup(self):
        """Unload models and free GPU memory"""
        self.xtts.unload_model()
        self.sadtalker.unload_model()
        logger.info("[Pipeline] Cleanup complete")
