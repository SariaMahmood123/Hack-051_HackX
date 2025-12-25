# Quick Start: Testing Persona Video Pipeline

## 🚀 Backend Setup

### 1. Start Backend Server
```bash
cd d:\Hack-051_HackX
python backend/run.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 2. Verify Backend Health
```bash
curl http://localhost:8000/api/health
```

Expected:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-10T..."
}
```

## 🎨 Frontend Setup

### 1. Install Dependencies (if needed)
```bash
cd frontend
npm install
```

### 2. Start Frontend Dev Server
```bash
npm run dev
```

Expected output:
```
ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

### 3. Open Persona Video Page
Navigate to: **http://localhost:3000/persona**

## 🧪 Testing Persona Video Generation

### Option 1: Use Frontend UI
1. Open http://localhost:3000/persona
2. Select persona (MKBHD or iJustine)
3. Enter prompt: "Explain the new M4 Mac Mini"
4. Click "Generate Video"
5. Wait 3-7 minutes for processing
6. Video player will appear with final result

### Option 2: Use Test Script
```bash
cd d:\Hack-051_HackX

# Test MKBHD persona
python backend/test_persona_endpoint.py

# Test iJustine persona
python backend/test_persona_endpoint.py ijustine
```

### Option 3: Use curl
```bash
# MKBHD test
curl -X POST http://localhost:8000/api/generate/persona-video \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain why the new M4 Mac Mini is the best value",
    "persona": "mkbhd",
    "temperature": 0.7,
    "max_tokens": 300
  }'

# iJustine test
curl -X POST http://localhost:8000/api/generate/persona-video \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Check out the new iPhone camera features",
    "persona": "ijustine",
    "temperature": 0.8,
    "max_tokens": 300
  }'
```

## 📊 Expected Results

### MKBHD Video Characteristics:
- **Voice**: Deep, smooth, professional
- **Pacing**: Deliberate with 0.4-0.5s pauses
- **Style**: Measured, objective analysis
- **Motion**: Subtle, calm movements
- **Duration**: ~20-40 seconds for 300 tokens

### iJustine Video Characteristics:
- **Voice**: Bright, energetic, expressive
- **Pacing**: Fast with 0.2-0.3s pauses
- **Style**: Enthusiastic reactions ("Oh my gosh!")
- **Motion**: More animated, frequent emphasis
- **Duration**: ~15-30 seconds for 300 tokens (faster speech)

## 🔍 Verifying Intent Effects

Watch for these intent-driven behaviors:

### During Pauses (intent = 0.0):
- ✅ Face becomes calmer
- ✅ Reduced motion
- ✅ Mouth closes or minimal movement

### During Emphasis (intent = 1.0):
- ✅ More expressive face
- ✅ Increased motion (subtle, 70-100% range)
- ✅ Eyes widen slightly
- ✅ More dynamic lip sync

### During Neutral Speech (intent = 0.5):
- ✅ Baseline motion
- ✅ Natural lip sync
- ✅ Steady expression

## 🐛 Troubleshooting

### Backend won't start:
```bash
# Check Python environment
python --version  # Should be 3.10+

# Check dependencies
pip list | grep torch
pip list | grep fastapi

# Check GPU
nvidia-smi
```

### Frontend won't connect:
```bash
# Check API URL in frontend/.env.local
echo $NEXT_PUBLIC_API_URL
# Should be: http://localhost:8000/api

# Or check frontend/lib/api.ts line 6
```

### Video generation fails:
```bash
# Check backend logs
tail -f backend/logs/lumen.log

# Verify assets exist
ls -la assets/mkbhd.wav
ls -la assets/mkbhd2.jpg
ls -la assets/reference_voice.wav

# Check GPU memory
nvidia-smi

# Test individual components
python -c "from ai.gemini_client import GeminiClient; print('Gemini OK')"
python -c "from ai.xtts_wrapper import XTTSWrapper; print('XTTS OK')"
python -c "from ai.sadtalker_wrapper import SadTalkerWrapper; print('SadTalker OK')"
```

### CUDA out of memory:
```bash
# Close other GPU processes
nvidia-smi --query-compute-apps=pid --format=csv,noheader | xargs -r kill

# Or restart backend with smaller batch size
# (TODO: Add batch size configuration)
```

## 📁 Output Files

Generated files are saved in:
```
outputs/
  audio/
    persona_{request_id}/
      output.wav              # Synthesized audio
      timing_map.json         # Intent timing data
  video/
    persona_{request_id}.mp4  # Final video with GFPGAN enhancement
```

## ⚡ Performance Notes

### Processing Time Breakdown:
- **Gemini script generation**: 5-15 seconds
- **XTTS audio synthesis**: 30-60 seconds
- **SadTalker video generation**: 2-5 minutes
  - Stage 1 (coefficients): ~30 seconds
  - Stage 2 (motion governor): ~10 seconds
  - Stage 3 (rendering + GFPGAN): ~2-4 minutes

### Speed Optimizations:
- Disable GFPGAN: Add `enhancer: null` in request (saves ~1-2 min)
- Reduce max_tokens: Shorter scripts = faster processing
- Lower temperature: Less creative = faster generation

## 🎯 Next Steps

1. **Add iJustine Portrait**: Replace MKBHD fallback image
   ```bash
   # TODO: Add assets/ijustine.jpg
   ```

2. **Test Both Personas**: Compare MKBHD vs iJustine side-by-side

3. **Adjust Motion Intensity**: If motion too subtle/strong, update:
   ```python
   # ai/motion_governor.py line 345
   intent_subtle = 0.7 + (intent_clamped * 0.25)  # Current: 70-100%
   ```

4. **Create More Personas**: Follow pattern in PERSONA_VIDEO_API.md

5. **Frontend Integration**: Add persona toggle to main chat interface

## ✅ Success Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 3000
- [ ] Can access http://localhost:3000/persona
- [ ] Both personas (MKBHD, iJustine) generate videos
- [ ] Videos show face with natural motion
- [ ] Intent effects visible (pauses = less motion, emphasis = more motion)
- [ ] GFPGAN face enhancement applied
- [ ] Video quality is clear and smooth
- [ ] Audio syncs with lip movements
- [ ] Processing completes in 3-7 minutes

## 📝 Test Prompts

### MKBHD Style:
- "Explain why the new M4 Mac Mini is the best value"
- "Review the latest iPhone camera system"
- "Compare M3 Max vs M4 Max performance"
- "What makes this GPU architecture different"

### iJustine Style:
- "Check out the new iPhone camera features"
- "This MacBook is incredible"
- "Unboxing the latest Apple products"
- "My first impressions of the new iPad"

---

**Ready to test!** Start with MKBHD persona using the frontend UI, then try iJustine to compare styles.
