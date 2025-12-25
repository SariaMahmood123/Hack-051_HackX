# LUMEN API Documentation

Complete API reference for LUMEN backend.

Base URL: `http://localhost:8000`

## Table of Contents
- [Health Endpoints](#health-endpoints)
- [Generation Endpoints](#generation-endpoints)
- [Error Responses](#error-responses)
- [Rate Limiting](#rate-limiting)

---

## Health Endpoints

### GET `/`
Basic health check.

**Response:**
```json
{
  "message": "LUMEN API is running",
  "status": "healthy",
  "version": "1.0.0",
  "gpu_enabled": true
}
```

### GET `/health`
Detailed health information with GPU stats.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "gpu_available": true,
  "gpu_info": {
    "device_name": "NVIDIA GeForce RTX 4080 Super",
    "cuda_version": "12.1",
    "memory_allocated": "2.34 GB",
    "memory_reserved": "2.50 GB"
  },
  "models_path": "d:/Hack-051_HackX/models",
  "outputs_path": "d:/Hack-051_HackX/outputs",
  "gemini_configured": true
}
```

### GET `/api/status`
API configuration and limits.

**Response:**
```json
{
  "api_version": "1.0.0",
  "endpoints": {
    "text_generation": "/api/generate/text",
    "tts_generation": "/api/generate/tts",
    "video_generation": "/api/generate/video",
    "full_pipeline": "/api/generate/full"
  },
  "limits": {
    "max_text_length": 500,
    "audio_sample_rate": 22050,
    "video_fps": 25
  }
}
```

---

## Generation Endpoints

### POST `/api/generate/text`
Generate text response using Gemini 2.0 Flash.

**Request Body:**
```json
{
  "prompt": "Tell me about artificial intelligence",
  "conversation_history": [
    {"role": "user", "parts": ["Previous message"]},
    {"role": "model", "parts": ["Previous response"]}
  ],
  "max_tokens": 1024,
  "temperature": 0.7
}
```

**Parameters:**
- `prompt` (string, required): User input text (1-2000 chars)
- `conversation_history` (array, optional): Previous messages
- `max_tokens` (integer, optional): Max response length (10-4096, default: 1024)
- `temperature` (float, optional): Creativity level (0.0-2.0, default: 0.7)

**Response:**
```json
{
  "text": "Artificial intelligence (AI) is...",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-24T10:30:45.123456",
  "tokens_used": 256
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/generate/text \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is machine learning?",
    "temperature": 0.7
  }'
```

---

### POST `/api/generate/tts`
Generate speech audio using XTTS v2 with voice cloning.

**Request Body:**
```json
{
  "text": "Hello, this is a test of voice synthesis.",
  "reference_audio": "assets/reference_voice.wav",
  "language": "en"
}
```

**Parameters:**
- `text` (string, required): Text to synthesize (1-5000 chars)
- `reference_audio` (string, optional): Path to reference audio
- `language` (string, optional): Language code (en, es, fr, de, it, pt, pl, tr, ru, nl, cs, ar, zh-cn)

**Response:**
```json
{
  "audio_path": "outputs/audio/550e8400-e29b-41d4-a716-446655440000.wav",
  "audio_url": "/outputs/audio/550e8400-e29b-41d4-a716-446655440000.wav",
  "duration": 5.2,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "sample_rate": 22050
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/generate/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world!",
    "language": "en"
  }'
```

---

### POST `/api/generate/video`
Generate talking-head video using SadTalker.

**Request Body:**
```json
{
  "audio_path": "outputs/audio/550e8400-e29b-41d4-a716-446655440000.wav",
  "reference_image": "assets/avatar.jpg",
  "fps": 25,
  "enhance": true
}
```

**Parameters:**
- `audio_path` (string, required): Path to audio file
- `reference_image` (string, optional): Path to avatar image
- `fps` (integer, optional): Video frame rate (15-60, default: 25)
- `enhance` (boolean, optional): Apply face enhancement (default: false)

**Response:**
```json
{
  "video_path": "outputs/video/550e8400-e29b-41d4-a716-446655440000.mp4",
  "video_url": "/outputs/video/550e8400-e29b-41d4-a716-446655440000.mp4",
  "duration": 5.2,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "fps": 25
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/generate/video \
  -H "Content-Type: application/json" \
  -d '{
    "audio_path": "outputs/audio/test.wav",
    "fps": 25,
    "enhance": true
  }'
```

---

### POST `/api/generate/full`
Full pipeline: Text → Audio → Video.

**⚠️ Note:** This endpoint may take 30-120 seconds depending on GPU and text length.

**Request Body:**
```json
{
  "prompt": "Tell me a joke about programming",
  "conversation_history": [],
  "reference_audio": "assets/reference_voice.wav",
  "reference_image": "assets/avatar.jpg",
  "temperature": 0.7
}
```

**Parameters:**
- `prompt` (string, required): User input text (1-2000 chars)
- `conversation_history` (array, optional): Previous conversation
- `reference_audio` (string, optional): Voice reference
- `reference_image` (string, optional): Avatar image
- `temperature` (float, optional): Text creativity (0.0-2.0)

**Response:**
```json
{
  "text": "Why do programmers prefer dark mode?...",
  "audio_path": "outputs/audio/550e8400-e29b-41d4-a716-446655440000.wav",
  "audio_url": "/outputs/audio/550e8400-e29b-41d4-a716-446655440000.wav",
  "video_path": "outputs/video/550e8400-e29b-41d4-a716-446655440000.mp4",
  "video_url": "/outputs/video/550e8400-e29b-41d4-a716-446655440000.mp4",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-12-24T10:30:45.123456",
  "processing_time": 45.7
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/generate/full \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello! How are you today?",
    "temperature": 0.7
  }'
```

**Example (Python):**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/generate/full",
    json={
        "prompt": "Tell me about your day",
        "conversation_history": [],
        "temperature": 0.7
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Video URL: {data['video_url']}")
    print(f"Processing time: {data['processing_time']}s")
else:
    print(f"Error: {response.json()}")
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "ErrorType",
  "message": "Detailed error message",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### HTTP Status Codes

- **200** - Success
- **400** - Bad Request (InvalidInputException)
- **422** - Validation Error
- **429** - Rate Limit Exceeded
- **500** - Server Error (GenerationException, ModelLoadException)

### Common Errors

**Validation Error (422):**
```json
{
  "error": "ValidationError",
  "message": "Invalid request data",
  "details": [
    {
      "loc": ["body", "prompt"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Invalid Input (400):**
```json
{
  "error": "InvalidInputException",
  "message": "Prompt cannot be empty",
  "path": "/api/generate/text"
}
```

**Generation Failure (500):**
```json
{
  "error": "GenerationException",
  "message": "Text generation failed: API key invalid",
  "path": "/api/generate/text"
}
```

**Rate Limit (429):**
```json
{
  "error": "RateLimitExceeded",
  "message": "Rate limit exceeded"
}
```

---

## Rate Limiting

Default limits:
- **100 requests per minute** per IP address
- Health endpoints (`/`, `/health`) are **not rate limited**

Rate limit headers are not currently included in responses.

---

## Static Files

Generated audio and video files are served at:
- Audio: `http://localhost:8000/outputs/audio/{filename}.wav`
- Video: `http://localhost:8000/outputs/video/{filename}.mp4`

Files are automatically cleaned up after 24 hours.

---

## WebSocket Support

❌ Not currently supported. All endpoints are REST-based and synchronous.

For streaming responses, you would need to implement WebSocket endpoints or Server-Sent Events (SSE).

---

## Authentication

❌ Not currently implemented. This is an MVP for hackathon use.

For production, add:
- API key authentication
- JWT tokens
- Rate limiting per user
- Request signing

---

## CORS

CORS is enabled for:
- `http://localhost:3000` (Next.js frontend)
- `http://127.0.0.1:3000`

Add additional origins in `backend/main.py`:
```python
allow_origins=[
    "http://localhost:3000",
    "https://your-domain.com"
]
```

---

## Response Times

Typical response times (RTX 4080 Super):
- **Text Generation**: 1-3 seconds (Gemini API)
- **TTS Generation**: 5-15 seconds (GPU)
- **Video Generation**: 20-60 seconds (GPU)
- **Full Pipeline**: 30-90 seconds (sequential)

Times vary based on:
- Text length
- GPU load
- Model initialization
- Network latency (Gemini API)

---

## Best Practices

1. **Include request_id** in logs for tracking
2. **Handle timeouts** - Full pipeline can take 2+ minutes
3. **Check health endpoint** before making requests
4. **Validate inputs** client-side to avoid validation errors
5. **Cache responses** when appropriate
6. **Monitor GPU memory** to avoid OOM errors

---

## Interactive Documentation

Visit http://localhost:8000/docs for:
- ✅ Interactive API testing
- ✅ Request/response schemas
- ✅ Try it out functionality
- ✅ Auto-generated examples

---

## Support

For issues or questions:
1. Check `logs/lumen.log` for detailed errors
2. Use `/health` endpoint to verify system status
3. Run `python backend/test_api.py` for diagnostics
4. Open a GitHub issue with logs and request details
