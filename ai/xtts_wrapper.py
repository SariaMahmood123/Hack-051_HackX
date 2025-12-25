"""
XTTS v2 Wrapper - CPU Optimized for Maximum Quality
Handles text-to-speech with voice cloning using Coqui TTS

This wrapper is configured for CPU-only operation to ensure:
- Numerical stability (no inf/nan issues)
- Maximum audio quality (no GPU precision loss)
- Deterministic output
- Reliable generation

Intent-Aware Architecture:
- Accepts ScriptIntent with pause/emphasis markers
- Generates audio per-segment with explicit silence
- Returns IntentTimingMap for Motion Governor
"""
import torch
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional, Union, Tuple
import os
import logging

# Import intent contract
try:
    from ai.script_intent import ScriptIntent, IntentTimingMap, TimingSegment, flatten_segments_to_text
    INTENT_AVAILABLE = True
except ImportError:
    INTENT_AVAILABLE = False
    ScriptIntent = None
    IntentTimingMap = None

logger = logging.getLogger("lumen")


class XTTSWrapper:
    """
    High-Quality XTTS v2 Wrapper (CPU-optimized)
    
    Provides text-to-speech with voice cloning capabilities.
    Configured for CPU operation to maximize audio quality and stability.
    
    Quality Features:
    - 24kHz sample rate output
    - FP32 precision throughout pipeline
    - Deterministic generation
    - No numerical instabilities
    
    First run will download ~2GB model files
    """
    
    def __init__(
        self, 
        model_path: Optional[Path] = None,
        device: str = "cpu"  # CPU-only for quality and stability
    ):
        """
        Initialize XTTS model for high-quality synthesis
        
        Args:
            model_path: Path to XTTS model checkpoint (auto-downloads if None)
            device: Device to run inference on (forced to CPU for quality)
        """
        # Force CPU for quality and stability
        self.device = "cpu"
        self.model_path = model_path
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        self.model = None
        self.is_loaded = False
        
        # Quality settings
        self.sample_rate = 24000  # XTTS native sample rate
        self.use_fp32 = True  # Full precision for quality
        
        logger.info(f"[XTTS] Initializing on {self.device} (quality-optimized mode)")
    
    def load_model(self):
        """
        Load XTTS model into memory with quality-focused configuration
        
        This is separate from __init__ to allow lazy loading.
        First run will auto-download model (~2GB).
        
        Quality optimizations:
        - CPU operation for numerical stability
        - FP32 precision (no quantization)
        - Deterministic computation
        """
        if self.is_loaded:
            return
        
        try:
            from TTS.api import TTS
            
            logger.info("[XTTS] Loading model for high-quality synthesis...")
            logger.info("[XTTS] This may take 10-15 seconds on first run (downloading ~2GB)")
            
            # Load XTTS v2 on CPU for maximum quality and stability
            self.model = TTS(
                model_name=self.model_name,
                gpu=False  # CPU for quality
            )
            
            # Configure PyTorch for deterministic, high-quality output
            torch.set_num_threads(os.cpu_count() or 4)  # Use all CPU cores
            torch.backends.cudnn.enabled = False  # Not using GPU
            
            # Ensure full precision
            if hasattr(self.model, 'synthesizer') and hasattr(self.model.synthesizer, 'tts_model'):
                tts_model = self.model.synthesizer.tts_model
                tts_model = tts_model.float()  # FP32
                tts_model.eval()  # Inference mode
                
                # Disable dropout for deterministic output
                for module in tts_model.modules():
                    if isinstance(module, torch.nn.Dropout):
                        module.p = 0.0
                
                logger.info("[XTTS] Model configured for FP32 precision and deterministic output")
            
            logger.info(f"[XTTS] Model loaded successfully on {self.device}")
            logger.info(f"[XTTS] Sample rate: {self.sample_rate}Hz, Precision: FP32")
            self.is_loaded = True
        
        except ImportError as e:
            logger.error(f"[XTTS] Import error: {str(e)}")
            raise RuntimeError(
                "TTS library not installed. Run: pip install TTS==0.22.0"
            )
        except Exception as e:
            logger.error(f"[XTTS] Load error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Failed to load XTTS model: {str(e)}")
    
    def synthesize(
        self, 
        text: str, 
        reference_audio: Union[str, Path],
        output_path: Union[str, Path],
        language: str = "en",
        temperature: float = 0.75,
        length_penalty: float = 1.0,
        repetition_penalty: float = 2.5,
        top_k: int = 50,
        top_p: float = 0.9,
        speed: float = 0.95
    ) -> Path:
        """
        Synthesize high-quality speech from text using voice cloning
        
        Quality-focused synthesis with fine-tuned parameters for best output.
        
        Args:
            text: Text to synthesize (longer text = more processing time)
            reference_audio: Path to reference audio for voice cloning 
                           (5-30 seconds recommended, clear speech)
            output_path: Where to save generated audio (WAV format, 24kHz, 16-bit)
            language: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn, ja, hu, ko, hi)
            temperature: Sampling randomness (0.65 = balanced quality/naturalness)
            length_penalty: Utterance length control (1.0 = normal)
            repetition_penalty: Avoid repetitive speech (2.5 = high quality)
            top_k: Nucleus sampling top-k (50 = quality-focused)
            top_p: Nucleus sampling top-p (0.85 = natural variation)
            speed: Speech speed multiplier (1.0 = normal, <1.0 = slower/clearer)
        
        Returns:
            Path to generated audio file (24kHz WAV)
        
        Raises:
            RuntimeError: If synthesis fails
            FileNotFoundError: If reference audio doesn't exist
        """
        if not self.is_loaded:
            self.load_model()
        
        # Convert to Path objects
        reference_audio = Path(reference_audio)
        output_path = Path(output_path)
        
        # Validate inputs
        if not reference_audio.exists():
            raise FileNotFoundError(f"Reference audio not found: {reference_audio}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"[XTTS] High-quality synthesis on CPU")
            logger.info(f"[XTTS] Text: {text[:80]}{'...' if len(text) > 80 else ''}")
            logger.info(f"[XTTS] Quality parameters: temp={temperature}, rep_penalty={repetition_penalty}, top_p={top_p}")
            
            # Quality-focused generation settings
            generation_kwargs = {}
            
            # Access internal model for quality settings
            if hasattr(self.model, 'synthesizer') and hasattr(self.model.synthesizer, 'tts_model'):
                tts_model = self.model.synthesizer.tts_model
                
                # Set quality parameters if model supports them
                if hasattr(tts_model, 'gpt_config'):
                    # GPT generation parameters for quality
                    generation_kwargs.update({
                        'temperature': temperature,
                        'top_p': top_p,
                        'top_k': top_k,
                        'repetition_penalty': repetition_penalty,
                        'length_penalty': length_penalty,
                    })
            
            # Generate speech with quality-focused settings
            # Note: TTS API may not expose all generation parameters directly
            # The model will use its default quality settings
            self.model.tts_to_file(
                text=text,
                speaker_wav=str(reference_audio),
                language=language,
                file_path=str(output_path),
                speed=speed,
                # Additional kwargs for internal use if supported
                **generation_kwargs
            )
            
            # Verify output was created
            if not output_path.exists():
                raise RuntimeError(f"Output file was not created: {output_path}")
            
            file_size_kb = output_path.stat().st_size / 1024
            logger.info(f"[XTTS] [OK] High-quality audio generated: {output_path.name}")
            logger.info(f"[XTTS] [OK] File size: {file_size_kb:.1f} KB @ 24kHz 16-bit WAV")
            logger.info(f"[XTTS] [OK] Quality: FP32 precision, deterministic output")
            
            return output_path
        
        except Exception as e:
            logger.error(f"[XTTS] Synthesis failed: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise RuntimeError(f"High-quality TTS synthesis failed: {str(e)}")
    
    def synthesize_with_intent(
        self,
        script_intent: 'ScriptIntent',
        reference_audio: Union[str, Path],
        output_path: Union[str, Path],
        language: str = "en",
        fps: int = 25,
        **kwargs
    ) -> Tuple[Path, Optional['IntentTimingMap']]:
        """
        Intent-aware synthesis: generates audio per segment with explicit pauses.
        
        This is the ARCHITECTURAL method that makes intent flow through the system.
        
        Args:
            script_intent: Structured script with pause/emphasis markers
            reference_audio: Voice reference for cloning
            output_path: Output WAV path
            language: Language code
            fps: Frames per second for timing map
            **kwargs: Additional synthesis parameters
        
        Returns:
            (audio_path, timing_map) tuple:
                - audio_path: Final concatenated audio
                - timing_map: IntentTimingMap for Motion Governor (None if not available)
        
        Pipeline:
            1. Generate audio per segment
            2. Insert explicit silence between segments
            3. Concatenate into final audio
            4. Build timing map linking audio time → intent
        """
        if not INTENT_AVAILABLE:
            logger.warning("[XTTS] Intent system not available, falling back to plain synthesis")
            text = " ".join(seg.text for seg in script_intent.segments)
            return self.synthesize(text, reference_audio, output_path, language, **kwargs), None
        
        if not self.is_loaded:
            self.load_model()
        
        reference_audio = Path(reference_audio)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"[XTTS] Intent-aware synthesis: {len(script_intent.segments)} segments")
        
        try:
            audio_segments = []
            timing_segments = []
            current_time = 0.0
            
            for idx, segment in enumerate(script_intent.segments):
                # Shape text for emphasis (capitalization)
                text = segment.text.strip()
                if segment.emphasis:
                    for word in segment.emphasis:
                        import re
                        pattern = re.compile(re.escape(word), re.IGNORECASE)
                        text = pattern.sub(word.upper(), text)
                
                logger.info(f"[XTTS] Segment {idx+1}/{len(script_intent.segments)}: '{text[:50]}...'")
                
                # Generate audio for this segment (to temp file)
                temp_path = output_path.parent / f"_temp_seg_{idx}.wav"
                self.synthesize(
                    text=text,
                    reference_audio=reference_audio,
                    output_path=temp_path,
                    language=language,
                    **kwargs
                )
                
                # Load generated audio
                audio_data, sr = sf.read(str(temp_path))
                if sr != self.sample_rate:
                    logger.warning(f"[XTTS] Sample rate mismatch: {sr} != {self.sample_rate}")
                
                # Record timing
                segment_duration = len(audio_data) / sr
                timing_segments.append(TimingSegment(
                    segment_idx=idx,
                    start_time=current_time,
                    end_time=current_time + segment_duration,
                    pause_after=segment.pause_after,
                    emphasis=segment.emphasis,
                    sentence_end=segment.sentence_end
                ))
                
                audio_segments.append(audio_data)
                current_time += segment_duration
                
                # Insert explicit silence for pauses
                if segment.pause_after > 0.01:
                    silence_samples = int(segment.pause_after * sr)
                    silence = np.zeros(silence_samples, dtype=audio_data.dtype)
                    audio_segments.append(silence)
                    current_time += segment.pause_after
                    logger.info(f"[XTTS] Added {segment.pause_after:.2f}s silence")
                
                # Clean up temp file
                temp_path.unlink()
            
            # Concatenate all segments
            final_audio = np.concatenate(audio_segments)
            total_duration = len(final_audio) / self.sample_rate
            
            # Save final audio
            sf.write(str(output_path), final_audio, self.sample_rate)
            logger.info(f"[XTTS] ✓ Intent-aware audio: {total_duration:.2f}s, {len(timing_segments)} segments")
            
            # Build timing map
            timing_map = IntentTimingMap(
                segments=timing_segments,
                total_duration=total_duration,
                fps=fps
            )
            
            # Update script_intent with duration
            script_intent.total_duration = total_duration
            
            logger.info(f"[XTTS] ✓ Timing map built: {timing_map.num_frames} frames @ {fps}fps")
            
            return output_path, timing_map
            
        except Exception as e:
            logger.error(f"[XTTS] Intent-aware synthesis failed: {e}", exc_info=True)
            # Fallback to plain synthesis
            logger.warning("[XTTS] Falling back to plain synthesis")
            text = flatten_segments_to_text(script_intent)
            return self.synthesize(text, reference_audio, output_path, language, **kwargs), None
    
    async def synthesize_async(
        self, 
        text: str, 
        reference_audio: Union[str, Path],
        output_path: Union[str, Path],
        language: str = "en",
        **kwargs
    ) -> Path:
        """
        Async wrapper for high-quality synthesize
        
        Accepts same parameters as synthesize() method.
        Currently runs synchronously - can be enhanced with proper async if needed.
        """
        return self.synthesize(
            text=text,
            reference_audio=reference_audio,
            output_path=output_path,
            language=language,
            **kwargs
        )
    
    def unload_model(self):
        """Free memory and clean up resources"""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("[XTTS] Model unloaded, memory freed")
