# Persona Video Pipeline - Backend Integration

## Overview
The `/generate/persona-video` endpoint provides a complete pipeline for generating persona-based talking head videos with intent-aware motion.

## Pipeline Flow
```
Frontend (persona + prompt)
  ↓
Backend API (/generate/persona-video)
  ↓
1. Gemini: Generate script with intent (persona-specific style)
  ↓
2. XTTS: Synthesize audio with timing map
  ↓
3. SadTalker: Generate video with Motion Governor + intent fusion
  ↓
4. Return video URL to frontend (GFPGAN face enhancement applied)
```

## API Endpoint

### POST `/generate/persona-video`

**Request Body:**
```json
{
  "prompt": "Explain why the new M4 Mac Mini is the best value",
  "persona": "mkbhd",
  "temperature": 0.7,
  "max_tokens": 300
}
```

**Parameters:**
- `prompt` (required): User topic/request (1-2000 chars)
- `persona` (required): Voice persona - `"ijustine"` or `"mkbhd"`
- `temperature` (optional): Script creativity 0.0-2.0, default 0.7
- `max_tokens` (optional): Script length 10-1024, default 500

**Response:**
```json
{
  "text": "Generated script text...",
  "audio_path": "/path/to/audio.wav",
  "audio_url": "http://localhost:8000/outputs/audio/...",
  "video_path": "/path/to/video.mp4",
  "video_url": "http://localhost:8000/outputs/video/...",
  "request_id": "uuid-here",
  "timestamp": "2025-01-10T12:34:56",
  "processing_time": 187.5
}
```

## Persona Characteristics

### MKBHD (Marques Brownlee)
- **Style**: Smooth, measured, professional
- **Voice**: Deep, clear, consistent pacing
- **Pauses**: 0.4-0.5s (deliberate)
- **Emphasis**: 1-2 words per segment (selective)
- **Temperature**: 0.6 (more consistent scripts)
- **Reference Assets**:
  - Audio: `assets/mkbhd.wav`
  - Image: `assets/mkbhd2.jpg`

### iJustine (Justine Ezarik)
- **Style**: Energetic, fast-paced, enthusiastic
- **Voice**: Bright, expressive, lots of emphasis
- **Pauses**: 0.2-0.3s (quick flow)
- **Emphasis**: 2-4 words per segment (frequent)
- **Temperature**: 0.8 (higher creativity)
- **Reference Assets**:
  - Audio: `assets/reference_voice.wav`
  - Image: `assets/mkbhd2.jpg` (fallback - TODO: Add ijustine portrait)

## Motion Intent System

The pipeline includes intent-aware motion control:

1. **Script Intent**: Gemini generates text with emphasis/pause markers
2. **Timing Map**: XTTS creates frame-by-frame intent values (0.0-1.0)
3. **Motion Governor**: Applies intent to 3DMM coefficients:
   - **Compact Models** (< 200 dims): Scalar gating (70-100% range)
   - **Full 3DMM Models**: Expression + pose refinement
4. **Renderer-Safe**: Preserves latent space integrity for compact models

### Intent Effects:
- **Pauses** (0.0): Reduced motion, calmer expression
- **Emphasis** (1.0): Increased motion, more expressive
- **Neutral** (0.5): Baseline motion

## Face Enhancement
- **GFPGAN** enabled by default
- Improves facial details, reduces artifacts
- Can disable with `enhancer=None` for faster processing

## Processing Time
- **Typical**: 3-7 minutes per video
- **Stages**:
  - Gemini script: 5-15 seconds
  - XTTS audio: 30-60 seconds
  - SadTalker video: 2-5 minutes (with GFPGAN)

## Testing

### Using curl:
```bash
# Test MKBHD persona
curl -X POST http://localhost:8000/generate/persona-video \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the new M4 Mac Mini",
    "persona": "mkbhd",
    "temperature": 0.7
  }'

# Test iJustine persona
curl -X POST http://localhost:8000/generate/persona-video \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Check out the new iPhone camera",
    "persona": "ijustine",
    "temperature": 0.8
  }'
```

### Using test script:
```bash
# Test MKBHD
python backend/test_persona_endpoint.py

# Test iJustine
python backend/test_persona_endpoint.py ijustine
```

## Frontend Integration

### Example React/Next.js Component:
```typescript
const [persona, setPersona] = useState<'ijustine' | 'mkbhd'>('mkbhd');
const [prompt, setPrompt] = useState('');
const [videoUrl, setVideoUrl] = useState('');
const [loading, setLoading] = useState(false);

const generateVideo = async () => {
  setLoading(true);
  try {
    const response = await fetch('/api/generate/persona-video', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, persona })
    });
    
    const result = await response.json();
    setVideoUrl(result.video_url);
  } catch (error) {
    console.error('Video generation failed:', error);
  } finally {
    setLoading(false);
  }
};

return (
  <div>
    {/* Persona Toggle */}
    <select value={persona} onChange={(e) => setPersona(e.target.value)}>
      <option value="mkbhd">MKBHD (Professional)</option>
      <option value="ijustine">iJustine (Energetic)</option>
    </select>
    
    {/* Prompt Input */}
    <textarea 
      value={prompt} 
      onChange={(e) => setPrompt(e.target.value)}
      placeholder="Enter your topic..."
    />
    
    {/* Generate Button */}
    <button onClick={generateVideo} disabled={loading}>
      {loading ? 'Generating...' : 'Generate Video'}
    </button>
    
    {/* Video Player */}
    {videoUrl && (
      <video src={videoUrl} controls autoPlay />
    )}
  </div>
);
```

## Asset Management

### Current Assets:
- ✅ `assets/mkbhd.wav` - MKBHD reference voice
- ✅ `assets/mkbhd2.jpg` - MKBHD portrait
- ✅ `assets/reference_voice.wav` - iJustine reference voice
- ⚠️ `assets/mkbhd2.jpg` - Using as fallback for iJustine (TODO: Add ijustine portrait)

### Adding New Personas:
1. Add reference audio: `assets/{persona}_voice.wav`
2. Add portrait image: `assets/{persona}.jpg`
3. Implement persona method in `ai/gemini_client.py`:
   ```python
   def generate_{persona}_script(self, prompt, temperature, max_tokens):
       # Custom system prompt with persona style
       ...
   ```
4. Add persona mapping in endpoint (line ~565)

## Error Handling

**Common Errors:**
- `Invalid persona`: Only "ijustine" and "mkbhd" supported
- `Reference audio not found`: Check assets directory
- `Reference image not found`: Check assets directory
- `Pipeline error`: Check logs for Gemini/XTTS/SadTalker failures

**Debugging:**
```bash
# Check backend logs
tail -f backend/logs/lumen.log

# Verify assets exist
ls -la assets/

# Test individual components
python -c "from ai.gemini_client import GeminiClient; ..."
```

## Performance Optimization

### Speed vs Quality Trade-offs:
- **Faster**: Disable GFPGAN (`enhancer=None`) - saves ~1-2 minutes
- **Better Quality**: Increase max_tokens for longer scripts
- **Memory**: Close unused models between requests

### Background Processing (TODO):
For long video generation, consider:
1. Return job_id immediately
2. Process video in background
3. Poll endpoint: GET `/generate/status/{job_id}`
4. Notify frontend when complete

## Known Issues

1. **iJustine portrait missing**: Currently using MKBHD fallback image
2. **Long processing time**: Video generation takes 3-7 minutes
3. **No progress updates**: Frontend blocks until complete (TODO: add streaming)

## Next Steps

- [ ] Add iJustine portrait image
- [ ] Implement background job processing
- [ ] Add progress polling endpoint
- [ ] Create more personas (TechLead, Linus, etc.)
- [ ] Add video quality settings (resolution, fps)
- [ ] Support custom reference audio upload
