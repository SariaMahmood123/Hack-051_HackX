# LUMEN - Project Structure

Complete file tree of the LUMEN hackathon MVP.

```
LUMEN/
│
├── README.md                          # Main project documentation
├── QUICKSTART.md                      # 5-minute setup guide
├── API_DOCS.md                        # Complete API reference
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── .gitignore                         # Git ignore rules
├── start_backend.bat                  # Windows quick start script
│
├── backend/                           # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                       # FastAPI app entry point
│   ├── run.py                        # Server runner script
│   ├── test_api.py                   # API testing utility
│   ├── README.md                     # Backend documentation
│   │
│   ├── core/                         # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py                # Settings & configuration
│   │   ├── logging_config.py        # Logging setup
│   │   ├── middleware.py            # Custom middleware
│   │   ├── exceptions.py            # Exception handlers
│   │   ├── utils.py                 # Helper functions
│   │   └── model_manager.py         # Model lifecycle management
│   │
│   └── routes/                       # API routes
│       ├── __init__.py
│       └── generation.py            # Generation endpoints
│
├── frontend/                         # Next.js Frontend
│   ├── package.json                 # Node dependencies
│   ├── tsconfig.json                # TypeScript config
│   ├── next.config.js               # Next.js config
│   ├── .env.local                   # Frontend environment
│   ├── README.md                    # Frontend documentation
│   │
│   ├── app/                         # App router
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Home page
│   │   └── globals.css             # Global styles
│   │
│   ├── components/                  # React components
│   │   ├── ChatInterface.tsx       # Main chat component
│   │   ├── MessageList.tsx         # Message display
│   │   ├── VideoPlayer.tsx         # Video playback
│   │   └── InputBox.tsx            # User input
│   │
│   └── lib/                         # Utilities
│       └── api.ts                  # Backend API client
│
├── ai/                               # AI Model Wrappers
│   ├── __init__.py
│   ├── README.md                    # AI layer documentation
│   ├── gemini_client.py            # Gemini API wrapper
│   ├── xtts_wrapper.py             # XTTS TTS wrapper
│   ├── sadtalker_wrapper.py        # SadTalker video wrapper
│   └── pipeline.py                 # Full pipeline orchestrator
│
├── scripts/                          # Utility Scripts
│   ├── setup.py                    # Project setup script
│   └── test_models.py              # Model testing utility
│
├── assets/                           # Reference Files
│   └── README.md                   # Asset instructions
│   # Add these files:
│   # - avatar.jpg (512x512+ portrait)
│   # - reference_voice.wav (5-15 sec audio)
│
├── models/                           # AI Model Checkpoints (gitignored)
│   ├── xtts_v2/                    # XTTS model files
│   └── sadtalker/                  # SadTalker checkpoints
│
├── outputs/                          # Generated Files (gitignored)
│   ├── audio/                      # Generated audio files
│   └── video/                      # Generated video files
│
└── logs/                            # Application Logs (auto-created)
    └── lumen.log                   # Main log file
```

## File Count Summary

- **Backend**: 13 files
- **Frontend**: 12 files  
- **AI Layer**: 5 files
- **Scripts**: 2 files
- **Documentation**: 5 files
- **Configuration**: 5 files

**Total**: 42 files created

## Key Technologies

### Backend
- **FastAPI** - Modern async web framework
- **Pydantic** - Request/response validation
- **Uvicorn** - ASGI server
- **PyTorch** - Deep learning framework

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type safety
- **Axios** - HTTP client
- **Tailwind CSS** - Styling (via utility classes)

### AI Models
- **Gemini 2.0 Flash** - Text generation (API)
- **XTTS v2** - Voice synthesis (local)
- **SadTalker** - Video generation (local)

## Setup Status

### ✅ Complete
- [x] Project structure
- [x] Backend API scaffolding
- [x] Frontend UI components
- [x] AI model wrappers (interfaces)
- [x] Configuration management
- [x] Error handling
- [x] Logging system
- [x] API documentation
- [x] Testing utilities
- [x] Quick start scripts

### ⏳ Todo
- [ ] Download AI model checkpoints
- [ ] Add reference assets (avatar.jpg, reference_voice.wav)
- [ ] Implement actual model integration
- [ ] Test end-to-end pipeline
- [ ] Optimize GPU memory usage
- [ ] Add caching layer

## Documentation

1. **[README.md](README.md)** - Main project overview
2. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
3. **[API_DOCS.md](API_DOCS.md)** - Complete API reference
4. **[backend/README.md](backend/README.md)** - Backend details
5. **[frontend/README.md](frontend/README.md)** - Frontend details
6. **[ai/README.md](ai/README.md)** - AI layer details

## Quick Commands

```bash
# Setup
python scripts/setup.py

# Backend
python backend/run.py

# Frontend
cd frontend && npm install && npm run dev

# Test API
python backend/test_api.py

# Test Models
python scripts/test_models.py
```

## Next Steps

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Add GEMINI_API_KEY
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   cd frontend && npm install
   ```

3. **Start servers**
   ```bash
   # Terminal 1: Backend
   python backend/run.py
   
   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

4. **Access application**
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## Development Workflow

1. Backend runs on port **8000**
2. Frontend runs on port **3000**
3. Frontend calls backend via `/api/*` endpoints
4. Generated files served at `/outputs/*`
5. Logs written to `logs/lumen.log`

## Git Workflow

```bash
# Initial commit
git add .
git commit -m "Initial LUMEN project scaffolding"
git push origin main

# Feature branches
git checkout -b feature/model-integration
# ... make changes ...
git commit -m "Implement XTTS integration"
git push origin feature/model-integration
```

## Production Deployment

For production, you'll need to:
1. Set up proper environment variables
2. Use production ASGI server (gunicorn + uvicorn workers)
3. Add authentication/authorization
4. Set up HTTPS with SSL certificates
5. Configure reverse proxy (nginx)
6. Add monitoring and logging (Sentry, etc.)
7. Implement rate limiting per user
8. Add database for conversation history
9. Set up CI/CD pipeline
10. Add comprehensive error handling

## License

MIT License - See LICENSE file

---

**LUMEN** - Built with ❤️ for HackX 2025
