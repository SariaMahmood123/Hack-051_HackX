"""
Generation endpoints for LUMEN
Handles text, TTS, video, and full pipeline generation
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
import uuid
from datetime import datetime
from pathlib import Path
import logging

from ..core.config import settings
from ..core.exceptions import GenerationException, InvalidInputException
from ..core.utils import generate_cache_key, ensure_file_exists

# Import AI model wrappers
from ai.gemini_client import GeminiClient
from ai.xtts_wrapper import XTTSWrapper
from ai.sadtalker_wrapper import SadTalkerWrapper
# TODO: Import pipeline manager once implemented
# from ai.pipeline import PipelineManager

logger = logging.getLogger("lumen")
router = APIRouter()


# Request/Response Models
class TextGenerationRequest(BaseModel):
    """Request for text generation via Gemini"""
    prompt: str = Field(..., description="User input text", min_length=1, max_length=2000)
    max_tokens: Optional[int] = Field(default=150, description="Max response length", ge=10, le=1024)
    temperature: Optional[float] = Field(default=0.7, description="Response creativity", ge=0.0, le=2.0)
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class TextGenerationResponse(BaseModel):
    """Response from text generation"""
    text: str
    request_id: str
    timestamp: str
    tokens_used: Optional[int] = None


class TTSRequest(BaseModel):
    """Request for text-to-speech"""
    text: str = Field(..., description="Text to synthesize", min_length=1, max_length=5000)
    reference_audio: Optional[str] = Field(default=None, description="Path to reference audio for voice cloning")
    language: Optional[str] = Field(default="en", description="Language code")
    
    @validator('text')
    def validate_text(cls, v):
        if not v.strip():
            raise ValueError("Text cannot be empty")
        if len(v.strip()) > 5000:
            raise ValueError("Text too long (max 5000 characters)")
        return v.strip()


class TTSResponse(BaseModel):
    """Response from TTS generation"""
    audio_path: str
    audio_url: str
    duration: float
    request_id: str
    sample_rate: int


class VideoGenerationRequest(BaseModel):
    """Request for video generation from audio"""
    audio_path: str = Field(..., description="Path to audio file")
    reference_image: Optional[str] = Field(default=None, description="Path to reference avatar image")
    fps: Optional[int] = Field(default=25, description="Video frame rate", ge=15, le=60)
    enhance: Optional[bool] = Field(default=False, description="Apply face enhancement")


class VideoGenerationResponse(BaseModel):
    """Response from video generation"""
    video_path: str
    video_url: str
    duration: float
    request_id: str
    fps: int


class FullPipelineRequest(BaseModel):
    """Request for full text → video pipeline"""
    prompt: str = Field(..., description="User input text", min_length=1, max_length=2000)
    max_tokens: Optional[int] = Field(default=150, description="Max response length", ge=10, le=1024)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    reference_audio: Optional[str] = None
    reference_image: Optional[str] = None
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class MKBHDGenerationRequest(BaseModel):
    """Request for MKBHD-style audio generation"""
    prompt: str = Field(..., description="Topic for MKBHD-style script", min_length=1, max_length=2000)
    max_tokens: Optional[int] = Field(default=3000, description="Max script length", ge=100, le=50000)
    
    @validator('prompt')
    def validate_prompt(cls, v):
        if not v.strip():
            raise ValueError("Prompt cannot be empty")
        return v.strip()


class MKBHDGenerationResponse(BaseModel):
    """Response from MKBHD-style generation"""
    script: str
    audio_path: str
    audio_url: str
    duration: float
    request_id: str
    timestamp: str


class FullPipelineResponse(BaseModel):
    """Response from full pipeline"""
    text: str
    audio_path: str
    audio_url: str
    video_path: str
    video_url: str
    request_id: str
    timestamp: str
    processing_time: Optional[float] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    request_id: Optional[str] = None


# Helper functions
def get_output_url(file_path: str) -> str:
    """Convert file path to URL"""
    # Remove outputs/ prefix and create URL
    relative_path = str(file_path).replace("\\", "/")
    if relative_path.startswith("outputs/"):
        relative_path = relative_path[8:]  # Remove 'outputs/' prefix
    return f"/outputs/{relative_path}"


# Endpoints
@router.post("/generate/text", response_model=TextGenerationResponse)
async def generate_text(request: TextGenerationRequest):
    """
    Generate text response using Gemini 2.0 Flash
    
    - **prompt**: User input text
    - **conversation_history**: Previous conversation context
    - **max_tokens**: Maximum response length
    - **temperature**: Response creativity (0.0 = deterministic, 2.0 = very creative)
    """
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Text generation request: {request.prompt[:50]}...")
    
    try:
        # Initialize Gemini client
        client = GeminiClient(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
        response_text = await client.generate_async(
            request.prompt,
            request.conversation_history
        )
        
        logger.info(f"[{request_id}] Text generation complete")
        
        return TextGenerationResponse(
            text=response_text,
            request_id=request_id,
            timestamp=datetime.utcnow().isoformat(),
            tokens_used=len(response_text.split())
        )
    
    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {str(e)}")
        raise InvalidInputException(str(e))
    except RuntimeError as e:
        # Gemini-specific errors (API key, quota, model issues)
        logger.error(f"[{request_id}] Gemini error: {str(e)}", exc_info=True)
        raise GenerationException(f"AI generation error: {str(e)}")
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        raise GenerationException(f"Text generation failed: {str(e)}")


@router.post("/generate/tts", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """
    Generate speech audio using XTTS v2 with voice cloning
    
    - **text**: Text to synthesize
    - **reference_audio**: Path to reference audio for voice cloning (optional)
    - **language**: Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn)
    """
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] TTS generation request: {len(request.text)} characters")
    
    try:
        # Use reference audio or default
        reference_audio = request.reference_audio or str(settings.XTTS_REFERENCE_AUDIO)
        
        # Initialize XTTS wrapper (quality-optimized CPU mode)
        xtts = XTTSWrapper()
        xtts.load_model()
        
        # Generate audio
        output_path = settings.OUTPUTS_PATH / "audio" / f"{request_id}.wav"
        audio_path = xtts.synthesize(
            text=request.text,
            reference_audio=Path(reference_audio),
            output_path=output_path,
            language=request.language,
            temperature=0.75,  # Emotion-focused
            top_p=0.9,  # Natural variation
            repetition_penalty=2.5  # Quality
        )
        
        # Calculate duration (approximate from file size)
        file_size = audio_path.stat().st_size
        audio_duration = (file_size - 44) / 48000  # 24kHz stereo/mono
        
        logger.info(f"[{request_id}] TTS generation complete: {audio_path.name}")
        
        return TTSResponse(
            audio_path=str(audio_path),
            audio_url=get_output_url(str(audio_path)),
            duration=audio_duration,
            request_id=request_id,
            sample_rate=settings.AUDIO_SAMPLE_RATE
        )
    
    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {str(e)}")
        raise InvalidInputException(str(e))
    except Exception as e:
        logger.error(f"[{request_id}] TTS generation failed: {str(e)}", exc_info=True)
        raise GenerationException(f"TTS generation failed: {str(e)}")


@router.post("/generate/video", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest):
    """
    Generate talking-head video using SadTalker
    
    - **audio_path**: Path to audio file
    - **reference_image**: Path to reference avatar image (optional)
    - **fps**: Video frame rate (15-60)
    - **enhance**: Apply face enhancement for better quality
    """
    request_id = str(uuid.uuid4())
    logger.info(f"[{request_id}] Video generation request: {request.audio_path}")
    
    try:
        # Validate audio file exists
        if not ensure_file_exists(Path(request.audio_path)):
            raise InvalidInputException(f"Audio file not found: {request.audio_path}")
        
        # Use reference image or default
        reference_image = request.reference_image or str(settings.SADTALKER_REFERENCE_IMAGE)
        
        # Generate video with SadTalker
        sadtalker = SadTalkerWrapper()
        output_path = settings.OUTPUTS_PATH / "video" / f"{request_id}.mp4"
        video_path = await sadtalker.generate_async(
            audio_path=Path(request.audio_path),
            reference_image=Path(reference_image),
            output_path=output_path,
            fps=request.fps,
            enhancer="gfpgan" if request.enhance else None
        )
        
        # Calculate video duration from audio
        import wave
        with wave.open(request.audio_path, 'rb') as audio_file:
            frames = audio_file.getnframes()
            rate = audio_file.getframerate()
            duration = frames / float(rate)
        
        logger.info(f"[{request_id}] Video generation complete: {video_path.name} ({duration:.1f}s)")
        
        return VideoGenerationResponse(
            video_path=str(video_path),
            video_url=get_output_url(str(video_path)),
            duration=duration,
            request_id=request_id,
            fps=request.fps
        )
    
    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {str(e)}")
        raise InvalidInputException(str(e))
    except Exception as e:
        logger.error(f"[{request_id}] Video generation failed: {str(e)}", exc_info=True)
        raise GenerationException(f"Video generation failed: {str(e)}")


@router.post("/generate/full", response_model=FullPipelineResponse)
async def generate_full_pipeline(request: FullPipelineRequest, background_tasks: BackgroundTasks):
    """
    Full pipeline: Text → TTS → Video
    
    Sequential execution to avoid GPU conflicts. This endpoint:
    1. Generates text response with Gemini
    2. Synthesizes speech with XTTS (GPU)
    3. Creates talking-head video with SadTalker (GPU)
    
    **Note:** This may take 30-120 seconds depending on GPU and text length.
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    logger.info(f"[{request_id}] Full pipeline started: {request.prompt[:50]}...")
    
    try:
        # Step 1: Generate text response with Gemini (stateless, concurrent-safe)
        logger.info(f"[{request_id}] Step 1/3: Generating text with {settings.GEMINI_MODEL}...")
        client = GeminiClient(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
        
        # Use stateless generation with custom parameters
        response_text = await client.generate_async(
            prompt=request.prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        logger.info(f"[{request_id}] [OK] Text generated: {len(response_text)} chars")
        
        # Step 2: Generate audio with XTTS (GPU)
        logger.info(f"[{request_id}] Step 2/3: Synthesizing speech...")
        reference_audio = request.reference_audio or str(settings.XTTS_REFERENCE_AUDIO)
        audio_filename = f"{request_id}.wav"
        audio_path = f"outputs/audio/{audio_filename}"
        
        # TODO: Implement XTTS
        # xtts = XTTSWrapper()
        # output_audio = settings.OUTPUTS_PATH / "audio" / audio_filename
        # await xtts.synthesize_async(
        #     text=response_text,
        #     reference_audio=Path(reference_audio),
        #     output_path=output_audio
        # )
        
        # Step 3: Generate video with SadTalker (GPU)
        # Note: Sequential execution to avoid GPU memory conflicts
        logger.info(f"[{request_id}] Step 3/3: Generating video...")
        reference_image = request.reference_image or str(settings.SADTALKER_REFERENCE_IMAGE)
        video_filename = f"{request_id}.mp4"
        video_path = f"outputs/video/{video_filename}"
        
        # TODO: Implement SadTalker
        # sadtalker = SadTalkerWrapper()
        # output_video = settings.OUTPUTS_PATH / "video" / video_filename
        # await sadtalker.generate_async(
        #     audio_path=output_audio,
        #     reference_image=Path(reference_image),
        #     output_path=output_video,
        #     fps=settings.VIDEO_FPS
        # )
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        logger.info(f"[{request_id}] Full pipeline complete in {processing_time:.2f}s")
        
        # Schedule cleanup in background
        # background_tasks.add_task(cleanup_old_files, settings.OUTPUTS_PATH / "audio")
        
        return FullPipelineResponse(
            text=response_text,
            audio_path=audio_path,
            audio_url=get_output_url(audio_path),
            video_path=video_path,
            video_url=get_output_url(video_path),
            request_id=request_id,
            timestamp=start_time.isoformat(),
            processing_time=processing_time
        )
    
    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {str(e)}")
        raise InvalidInputException(str(e))
    except RuntimeError as e:
        # Gemini-specific errors (API key, quota, model issues)
        logger.error(f"[{request_id}] Gemini error: {str(e)}", exc_info=True)
        raise GenerationException(f"AI generation error: {str(e)}")
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        raise GenerationException(f"Full pipeline failed: {str(e)}")


@router.post("/generate/mkbhd", response_model=MKBHDGenerationResponse)
async def generate_mkbhd_audio(request: MKBHDGenerationRequest):
    """
    Generate MKBHD-style audio
    
    1. Uses Gemini to create a tech review script in MKBHD's style
    2. Synthesizes it using XTTS with MKBHD's voice reference
    3. Returns high-quality audio
    
    - **prompt**: Topic or product to review (e.g., "the new iPhone 16")
    - **max_tokens**: Length of generated script
    """
    request_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    logger.info(f"[{request_id}] MKBHD generation started: {request.prompt[:50]}...")
    
    try:
        # Step 1: Generate MKBHD-style script with Gemini
        logger.info(f"[{request_id}] Step 1/2: Generating MKBHD-style script...")
        client = GeminiClient(api_key=settings.GEMINI_API_KEY, model_name=settings.GEMINI_MODEL)
        
        # Create a prompt that guides Gemini to write like MKBHD
        mkbhd_system_prompt = f"""You are Marques Brownlee (MKBHD) having a personal conversation with someone who asked you: {request.prompt}

You're responding directly to THEIR question in a natural, conversational way - like you're chatting with them one-on-one, not recording a YouTube video for millions.

CRITICAL RULES:
- Output ONLY spoken words - what you would actually say out loud
- NO stage directions, NO asterisks, NO descriptions like "(Video opens)" or "*sitting at desk*"
- NO formatting, NO actions, NO visual cues
- Just pure dialogue - words that will be spoken
- Keep it CONCISE - aim for 2-3 minutes of spoken content
- IMPORTANT: Always complete your final sentence and end with a clear conclusion - never leave thoughts hanging

Your conversational style:
- Address them directly using "you" and "your" - make it personal to THEIR situation
- Start casually like "Alright, so..." or "Okay, so here's the thing..." or "Hey, so..."
- Use phrases like "For you specifically", "In your case", "Given what you told me"
- Be honest and helpful - focus on what matters to THEM
- Reference their specific situation if they mentioned details (like current phone, use case, etc.)
- Give your genuine opinion and recommendation tailored to their needs
- MUST end with a complete final sentence and practical advice - wrap it up properly

Write a focused, personal response that directly answers their question. Make them feel like you're genuinely helping them make a decision, not performing for a camera. Be concise and conversational. ALWAYS finish your final thought completely and end with a clear recommendation or conclusion. Remember: ONLY words that will be spoken - no video descriptions."""

        script = await client.generate_async(
            prompt=mkbhd_system_prompt,
            temperature=0.8,  # More creative for personality
            max_tokens=request.max_tokens
        )
        
        logger.info(f"[{request_id}] Script generated: {len(script)} chars (max_tokens={request.max_tokens})")
        logger.info(f"[{request_id}] Script preview: {script[:100]}...")
        
        # Step 2: Synthesize with MKBHD voice
        logger.info(f"[{request_id}] Step 2/2: Synthesizing audio with MKBHD voice...")
        
        # Use MKBHD reference audio (located in parent directory's assets folder)
        mkbhd_reference = Path(__file__).parent.parent.parent / "assets" / "mkbhd.wav"
        if not mkbhd_reference.exists():
            raise InvalidInputException(
                "MKBHD reference audio not found. Please run: "
                "python extract_reference_audio.py <source> <start> <end> -o mkbhd.wav"
            )
        
        # Initialize XTTS
        xtts = XTTSWrapper()
        xtts.load_model()
        
        # Generate audio with emotion-focused parameters
        output_path = settings.OUTPUTS_PATH / "audio" / f"mkbhd_{request_id}.wav"
        audio_path = xtts.synthesize(
            text=script,
            reference_audio=mkbhd_reference,
            output_path=output_path,
            language="en",
            temperature=0.75,  # Expressive
            top_p=0.9,  # Natural variation
            repetition_penalty=2.5,  # Quality
            speed=1.0  # Normal MKBHD pace
        )
        
        # Calculate duration
        file_size = audio_path.stat().st_size
        audio_duration = (file_size - 44) / 48000
        
        logger.info(f"[{request_id}] MKBHD audio generated: {audio_duration:.1f}s")
        
        return MKBHDGenerationResponse(
            script=script,
            audio_path=str(audio_path),
            audio_url=get_output_url(str(audio_path)),
            duration=audio_duration,
            request_id=request_id,
            timestamp=start_time.isoformat()
        )
    
    except ValueError as e:
        logger.error(f"[{request_id}] Validation error: {str(e)}")
        raise InvalidInputException(str(e))
    except RuntimeError as e:
        logger.error(f"[{request_id}] Generation error: {str(e)}", exc_info=True)
        raise GenerationException(f"MKBHD generation failed: {str(e)}")
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {str(e)}", exc_info=True)
        raise GenerationException(f"MKBHD generation failed: {str(e)}")
