"""
Configuration management for LUMEN backend
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    
    # Paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent.parent
    MODELS_PATH: Path = PROJECT_ROOT / "models"
    ASSETS_PATH: Path = PROJECT_ROOT / "assets"
    OUTPUTS_PATH: Path = PROJECT_ROOT / "outputs"
    
    # XTTS Configuration
    XTTS_MODEL_PATH: Path = MODELS_PATH / "xtts_v2"
    XTTS_REFERENCE_AUDIO: Path = ASSETS_PATH / "reference_voice.wav"
    
    # SadTalker Configuration
    SADTALKER_MODEL_PATH: Path = MODELS_PATH / "sadtalker"
    SADTALKER_REFERENCE_IMAGE: Path = ASSETS_PATH / "mkbhd.jpg"  # MKBHD portrait for video generation
    
    # GPU Configuration
    GPU_ENABLED: bool = True
    CUDA_DEVICE: int = 0
    
    # Generation Settings
    MAX_TEXT_LENGTH: int = 500
    AUDIO_SAMPLE_RATE: int = 22050
    VIDEO_FPS: int = 25
    
    class Config:
        env_file = Path(__file__).parent.parent.parent / ".env"
        case_sensitive = True


settings = Settings()

# Ensure output directories exist
settings.OUTPUTS_PATH.mkdir(exist_ok=True, parents=True)
(settings.OUTPUTS_PATH / "audio").mkdir(exist_ok=True)
(settings.OUTPUTS_PATH / "video").mkdir(exist_ok=True)
