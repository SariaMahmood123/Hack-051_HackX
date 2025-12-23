# Backend

FastAPI backend for LUMEN video chatbot platform.

## Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── run.py                     # Server runner script
├── test_api.py               # API testing script
├── core/
│   ├── config.py             # Configuration management
│   ├── logging_config.py     # Logging setup
│   ├── middleware.py         # Custom middleware
│   ├── exceptions.py         # Exception handlers
│   ├── utils.py              # Helper functions
│   └── model_manager.py      # Model lifecycle management
└── routes/
    └── generation.py         # API endpoints
```

## Features

✅ **Modular Architecture** - Clean separation of concerns
✅ **Request Validation** - Pydantic models with validators
✅ **Error Handling** - Custom exceptions with proper status codes
✅ **Logging** - Structured logging to console and file
✅ **Rate Limiting** - Basic rate limiting middleware
✅ **Static Files** - Serves generated outputs
✅ **CORS** - Configured for Next.js frontend
✅ **API Documentation** - Auto-generated OpenAPI docs
✅ **Model Management** - Lazy loading and GPU cleanup

## API Endpoints

### Health & Status
- `GET /` - Basic health check
- `GET /health` - Detailed health with GPU info
- `GET /api/status` - API configuration and limits

### Generation
- `POST /api/generate/text` - Text generation (Gemini)
- `POST /api/generate/tts` - Text-to-speech (XTTS)
- `POST /api/generate/video` - Video generation (SadTalker)
- `POST /api/generate/full` - Full pipeline (Text → Audio → Video)

## Quick Start

### 1. Install Dependencies

```bash
# From project root
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env and set:
# GEMINI_API_KEY=your_api_key_here
```

### 3. Run Server

**Option A: Using run script (recommended)**
```bash
python backend/run.py
```

**Option B: Using uvicorn directly**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### 5. Test API

```bash
python backend/test_api.py
```

## Configuration

Environment variables in `.env`:

```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional (with defaults)
API_HOST=0.0.0.0
API_PORT=8000
GPU_ENABLED=true
CUDA_DEVICE=0

# Paths
MODELS_PATH=models
ASSETS_PATH=assets
OUTPUTS_PATH=outputs

# Model Settings
MAX_TEXT_LENGTH=500
AUDIO_SAMPLE_RATE=22050
VIDEO_FPS=25
```

## Request Examples

### Text Generation

```bash
curl -X POST http://localhost:8000/api/generate/text \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Tell me about AI",
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

### Full Pipeline

```bash
curl -X POST http://localhost:8000/api/generate/full \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello! How are you?",
    "conversation_history": []
  }'
```

## Response Format

All endpoints return JSON with:
- `request_id` - Unique identifier
- `timestamp` - ISO 8601 timestamp
- Additional data specific to endpoint

### Success Response
```json
{
  "text": "Generated response...",
  "audio_url": "/outputs/audio/uuid.wav",
  "video_url": "/outputs/video/uuid.mp4",
  "request_id": "uuid",
  "timestamp": "2025-12-24T...",
  "processing_time": 45.2
}
```

### Error Response
```json
{
  "error": "GenerationException",
  "message": "Detailed error message",
  "request_id": "uuid"
}
```

## Middleware

1. **CORS** - Allows requests from Next.js frontend
2. **Request Logging** - Logs all requests with duration
3. **Rate Limiting** - 100 requests per minute per IP

## Exception Handling

Custom exceptions:
- `InvalidInputException` - HTTP 400 for bad requests
- `GenerationException` - HTTP 500 for generation failures
- `ModelLoadException` - HTTP 500 for model loading errors

## Logging

Logs are written to:
- **Console** - INFO level and above
- **File** - `logs/lumen.log` with all levels

Log format:
```
2025-12-24 10:30:45 - lumen - INFO - [uuid] Text generation request: Hello...
```

## Model Management

The `ModelManager` singleton handles:
- Lazy loading of AI models
- GPU memory management
- Model cleanup and unloading

Usage in endpoints:
```python
from backend.core.model_manager import model_manager

# Get model instances
gemini = model_manager.get_gemini_client()
xtts = model_manager.get_xtts_wrapper()

# Cleanup when done
model_manager.unload_all()
```

## Development Tips

1. **Auto-reload**: Use `--reload` flag for development
2. **Logging**: Check `logs/lumen.log` for detailed logs
3. **Testing**: Use `test_api.py` to verify endpoints
4. **GPU Memory**: Monitor with `nvidia-smi`
5. **Debugging**: Use `/health` endpoint to check GPU status

## Troubleshooting

**Server won't start:**
- Check port 8000 is available
- Verify `.env` file exists
- Ensure dependencies are installed

**GPU not detected:**
- Verify CUDA installation
- Check PyTorch: `python -c "import torch; print(torch.cuda.is_available())"`

**API errors:**
- Check logs in `logs/lumen.log`
- Verify GEMINI_API_KEY is set
- Ensure outputs directory exists
