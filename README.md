# LUMEN 🌟

> **Generative AI Platform for Video-Based Conversational Chatbots**

LUMEN is a hackathon MVP that creates realistic video responses from text conversations. It combines cutting-edge LLMs, voice cloning, and talking-head synthesis to generate engaging video chatbot interactions.

---

## 🎯 Project Overview

**Pipeline:**
```
User Input (Text) 
    ↓
Gemini 2.0 Flash (LLM Response)
    ↓
XTTS v2 (Text-to-Speech with Voice Cloning)
    ↓
SadTalker (Talking-Head Video Generation)
    ↓
Video Response (Frontend Display)
```

**Key Features:**
- 💬 Natural conversation with Gemini 2.0 Flash
- 🎤 Voice cloning for personalized responses
- 🎬 Realistic talking-head video generation
- 🖥️ Clean chat interface with video playback
- 🚀 Optimized for RTX 4080 Super GPU

---

## 🏗️ Architecture

```
LUMEN/
├── backend/              # FastAPI server
│   ├── main.py          # App entry point
│   ├── core/            # Configuration
│   └── routes/          # API endpoints
├── frontend/            # Next.js app
│   ├── app/             # Pages & layouts
│   ├── components/      # React components
│   └── lib/             # API client
├── ai/                  # AI model wrappers
│   ├── gemini_client.py
│   ├── xtts_wrapper.py
│   ├── sadtalker_wrapper.py
│   └── pipeline.py
├── scripts/             # Setup utilities
├── assets/              # Reference images & audio
├── models/              # AI model checkpoints (gitignored)
└── outputs/             # Generated files (gitignored)
```

---

## 🛠️ Tech Stack

**Backend:**
- Python 3.10+
- FastAPI
- PyTorch

**AI Models:**
- **Gemini 2.0 Flash** - LLM (API-based)
- **XTTS v2** - Text-to-Speech (local GPU)
- **SadTalker** - Video Generation (local GPU)

**Frontend:**
- Next.js 15
- React 18
- TypeScript
- Axios

**Hardware:**
- NVIDIA RTX 4080 Super (16GB VRAM)
- CUDA 12.x

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- NVIDIA GPU with CUDA support
- Gemini API key ([Get one here](https://ai.google.dev/))

### 1. Clone & Setup Environment

```bash
# Clone repository
git clone <your-repo-url>
cd LUMEN

# Create Python virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install Python dependencies
pip install -r requirements.txt

# Setup project structure
python scripts/setup.py
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_key_here
```

### 3. Download AI Models

**XTTS v2:**
```python
# Auto-downloads on first use, or manually:
from TTS.api import TTS
TTS("tts_models/multilingual/multi-dataset/xtts_v2")
```

**SadTalker:**
```bash
cd models
git clone https://github.com/OpenTalker/SadTalker.git sadtalker
cd sadtalker
bash scripts/download_models.sh
```

### 4. Add Assets

Place the following in `assets/`:
- `avatar.jpg` - Clear frontal portrait (512x512+)
- `reference_voice.wav` - 5-15 second audio sample

### 5. Start Backend

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`

### 6. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: `http://localhost:3000`

---

## 📡 API Endpoints

### Health Check
```http
GET /health
```

### Text Generation
```http
POST /api/generate/text
{
  "prompt": "Hello!",
  "conversation_history": []
}
```

### Full Pipeline
```http
POST /api/generate/full
{
  "prompt": "Tell me about AI",
  "conversation_history": []
}
```

Returns:
```json
{
  "text": "Generated response...",
  "audio_path": "outputs/audio/{id}.wav",
  "video_path": "outputs/video/{id}.mp4",
  "request_id": "uuid",
  "timestamp": "2025-12-23T..."
}
```

---

## 🎨 Frontend Features

- **Chat Interface**: Clean conversation view
- **Video Player**: Auto-playing video responses
- **Loading States**: Visual feedback during generation
- **Responsive Design**: Works on desktop and tablet

---

## 🔧 Development

### Project Structure Details

**Backend (`backend/`)**
- `main.py` - FastAPI app initialization
- `core/config.py` - Environment configuration
- `routes/generation.py` - API endpoints

**AI Layer (`ai/`)**
- `gemini_client.py` - Gemini API wrapper
- `xtts_wrapper.py` - XTTS inference
- `sadtalker_wrapper.py` - SadTalker inference
- `pipeline.py` - Full pipeline orchestration

**Frontend (`frontend/`)**
- `app/page.tsx` - Main chat page
- `components/ChatInterface.tsx` - Main component
- `components/VideoPlayer.tsx` - Video display
- `lib/api.ts` - Backend API client

### Testing Models

```bash
python scripts/test_models.py
```

---

## 🐛 Troubleshooting

**GPU Memory Issues:**
- Models run sequentially to avoid conflicts
- Adjust batch sizes in model wrappers
- Monitor VRAM with `nvidia-smi`

**Model Download Failures:**
- Check internet connection
- Verify HuggingFace access
- Download manually if needed

**API Connection Issues:**
- Verify Gemini API key
- Check CORS settings in `backend/main.py`
- Ensure backend is running on port 8000

---

## 📝 TODO / Future Improvements

- [ ] Implement actual XTTS integration
- [ ] Implement actual SadTalker integration
- [ ] Add conversation memory management
- [ ] Implement response streaming
- [ ] Add multiple persona support
- [ ] Optimize GPU memory usage
- [ ] Add video quality settings
- [ ] Implement caching layer
- [ ] Add user authentication
- [ ] Deploy to production

---

## 🤝 Contributing

This is a hackathon MVP. Feel free to fork and improve!

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- [Gemini API](https://ai.google.dev/) - LLM
- [Coqui XTTS](https://github.com/coqui-ai/TTS) - Voice synthesis
- [SadTalker](https://github.com/OpenTalker/SadTalker) - Video generation

---

**Built with ❤️ for hackathons**

For questions or issues, please open a GitHub issue.
