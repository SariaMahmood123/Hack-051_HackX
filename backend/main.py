"""
LUMEN Backend - FastAPI Application
Main entry point for the video chatbot generation API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import logging

from .routes import generation
from .core.config import settings
from .core.logging_config import setup_logging
from .core.middleware import RequestLoggingMiddleware, RateLimitMiddleware
from .core.exceptions import (
    LumenException,
    lumen_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from .core.utils import cleanup_old_files

load_dotenv()

# Setup logging
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    logger.info("Starting LUMEN Backend...")
    logger.info(f"   GPU Available: {settings.GPU_ENABLED}")
    logger.info(f"   Models Path: {settings.MODELS_PATH}")
    logger.info(f"   Outputs Path: {settings.OUTPUTS_PATH}")
    
    # Cleanup old generated files on startup
    logger.info("Cleaning up old files...")
    cleanup_old_files(settings.OUTPUTS_PATH / "audio", max_age_hours=24)
    cleanup_old_files(settings.OUTPUTS_PATH / "video", max_age_hours=24)
    
    yield
    
    logger.info("Shutting down LUMEN Backend...")


app = FastAPI(
    title="LUMEN API",
    description="Generative AI platform for video-based conversational chatbots",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        # Add production URLs here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

# Exception handlers
app.add_exception_handler(LumenException, lumen_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Mount static files for generated outputs
if settings.OUTPUTS_PATH.exists():
    app.mount(
        "/outputs",
        StaticFiles(directory=str(settings.OUTPUTS_PATH)),
        name="outputs"
    )
    logger.info(f"Mounted static files at /outputs")

# Include routes
app.include_router(generation.router, prefix="/api", tags=["generation"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LUMEN API is running",
        "status": "healthy",
        "version": "1.0.0",
        "gpu_enabled": settings.GPU_ENABLED,
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    gpu_info = None
    gpu_available = False
    
    try:
        import torch
        if settings.GPU_ENABLED and torch.cuda.is_available():
            gpu_available = True
            gpu_info = {
                "device_name": torch.cuda.get_device_name(0),
                "cuda_version": torch.version.cuda,
                "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1024**3:.2f} GB",
                "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1024**3:.2f} GB"
            }
    except ImportError:
        # Torch not installed, GPU features not available
        pass
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "gpu_available": gpu_available,
        "gpu_info": gpu_info,
        "models_path": str(settings.MODELS_PATH),
        "outputs_path": str(settings.OUTPUTS_PATH),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL
    }


# Duplicate at /health for backwards compatibility
@app.get("/health")
async def health_check_legacy():
    """Legacy health check endpoint"""
    return await health_check()


@app.get("/api/status")
async def api_status():
    """API status and configuration"""
    return {
        "api_version": "1.0.0",
        "endpoints": {
            "text_generation": "/api/generate/text",
            "tts_generation": "/api/generate/tts",
            "video_generation": "/api/generate/video",
            "full_pipeline": "/api/generate/full"
        },
        "limits": {
            "max_text_length": settings.MAX_TEXT_LENGTH,
            "audio_sample_rate": settings.AUDIO_SAMPLE_RATE,
            "video_fps": settings.VIDEO_FPS
        }
    }
